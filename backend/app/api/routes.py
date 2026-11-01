import asyncio
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Request
from app.models.schemas import (
    ForecastResponse,
    ForecastSummaryResponse,
    DaySummary,
    WeatherData,
    SpotSearchItem,
    ReverseGeocodeResult,
    AutoLocationResponse
)
from app.services.solunar import calculate_solunar_data, get_moon_phase_info
from app.services.weather import fetch_weather_forecast, get_weather_description, kmh_to_knots
from app.services.marine import fetch_marine_forecast
from app.services.scoring import compute_24h_activity, get_rating_label
from app.services.geocoding import search_spots, reverse_geocode, get_auto_location

router = APIRouter(prefix="/api/v1", tags=["Forecast & Search"])

DAY_NAMES_IT = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
MONTH_NAMES_IT = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]


@router.get("/search", response_model=List[SpotSearchItem])
async def search_locations(q: str = Query(..., min_length=1, description="Location search query")):
    if not q.strip():
        return []
    results = await search_spots(q)
    return results


@router.get("/reverse-geocode", response_model=ReverseGeocodeResult)
async def get_reverse_geocode(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude")
):
    result = await reverse_geocode(lat, lon)
    return result


@router.get("/location/auto", response_model=AutoLocationResponse)
async def auto_detect_location(request: Request):
    """
    Detects user location from client IP or X-Forwarded-For header with coastal fallback.
    """
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = None

    result = await get_auto_location(client_ip)
    return result




@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
    target_date_str: Optional[str] = Query(None, alias="date", description="Target date YYYY-MM-DD")
):
    if target_date_str:
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date format. Expected YYYY-MM-DD")
    else:
        target_date = date.today()

    # Parallel async requests for weather & marine
    weather_task = asyncio.create_task(fetch_weather_forecast(lat, lon, forecast_days=7, past_days=1))
    marine_task = asyncio.create_task(fetch_marine_forecast(lat, lon, forecast_days=7))

    weather_raw, marine_data = await asyncio.gather(weather_task, marine_task, return_exceptions=True)

    if isinstance(weather_raw, Exception):
        raise HTTPException(status_code=502, detail=f"Failed to fetch weather data: {str(weather_raw)}")

    if isinstance(marine_data, Exception):
        marine_data = None

    # Calculate local solunar data
    solunar_data = calculate_solunar_data(lat, lon, target_date)

    hourly_weather = weather_raw.get("hourly", {})
    wave_height = marine_data.wave_height if marine_data else None

    # Compute 24h activity curve
    hourly_activities = compute_24h_activity(
        lat=lat,
        lon=lon,
        target_date=target_date,
        solunar_data=solunar_data,
        weather_hourly=hourly_weather,
        marine_wave_height=wave_height
    )

    # Compute daily score (mean of top feeding hours)
    scores = [h.score for h in hourly_activities]
    daily_score = round(sum(scores) / len(scores)) if scores else 50
    daily_rating = get_rating_label(daily_score)

    # Current weather snapshot (use midday or current hour)
    now_hour = datetime.now().hour if target_date == date.today() else 12
    current_hourly = hourly_activities[now_hour] if now_hour < len(hourly_activities) else hourly_activities[0]

    all_temps = [h.temperature for h in hourly_activities] if hourly_activities else [current_hourly.temperature]

    weather_current = WeatherData(
        temperature_2m=current_hourly.temperature,
        apparent_temperature=current_hourly.apparent_temperature,
        relative_humidity=current_hourly.relative_humidity,
        surface_pressure=current_hourly.pressure,
        pressure_trend_3h=current_hourly.pressure_trend_3h,
        wind_speed_knots=current_hourly.wind_knots,
        wind_direction=current_hourly.wind_direction,
        wind_gusts_knots=current_hourly.wind_gusts_knots,
        cloud_cover=50.0,
        weather_code=current_hourly.weather_code,
        weather_description=get_weather_description(current_hourly.weather_code),
        precipitation=current_hourly.precipitation or 0.0,
        precipitation_probability=current_hourly.precipitation_probability or 0.0,
        uv_index=current_hourly.uv_index,
        temp_min=min(all_temps),
        temp_max=max(all_temps)
    )

    return ForecastResponse(
        date=target_date.isoformat(),
        latitude=lat,
        longitude=lon,
        daily_score=daily_score,
        daily_rating=daily_rating,
        hourly_activity=hourly_activities,
        solunar=solunar_data,
        weather_current=weather_current,
        marine=marine_data
    )


@router.get("/forecast/summary", response_model=ForecastSummaryResponse)
async def get_forecast_summary(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
    days: int = Query(7, ge=1, le=14, description="Days to summarize")
):
    try:
        weather_raw = await fetch_weather_forecast(lat, lon, forecast_days=days, past_days=1)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch forecast summary: {str(e)}")

    daily_data = weather_raw.get("daily", {})
    dates = daily_data.get("time", [])
    weather_codes = daily_data.get("weather_code", [])
    t_max = daily_data.get("temperature_2m_max", [])
    t_min = daily_data.get("temperature_2m_min", [])
    w_max = daily_data.get("wind_speed_10m_max", [])

    today = date.today()
    day_summaries: List[DaySummary] = []

    # Map moon icons
    moon_icons = {
        "Luna Nuova": "new-moon",
        "Luna Crescente": "waxing-crescent",
        "Primo Quarto": "first-quarter",
        "Gibbosa Crescente": "waxing-gibbous",
        "Luna Piena": "full-moon",
        "Gibbosa Calante": "waning-gibbous",
        "Ultimo Quarto": "last-quarter",
        "Luna Calante": "waning-crescent"
    }

    for i, d_str in enumerate(dates):
        if i >= days + 1:
            break
        d_obj = date.fromisoformat(d_str)
        # Skip days before yesterday
        if d_obj < today - timedelta(days=1):
            continue

        # Day name
        if d_obj == today:
            day_name = "Oggi"
        elif d_obj == today + timedelta(days=1):
            day_name = "Domani"
        elif d_obj == today - timedelta(days=1):
            day_name = "Ieri"
        else:
            day_name = DAY_NAMES_IT[d_obj.weekday()]

        phase_name, illum, is_perigee = get_moon_phase_info(d_obj)

        # Unified 24h score calculation matching /forecast exactly
        solunar_d = calculate_solunar_data(lat, lon, d_obj)
        activities_d = compute_24h_activity(
            lat=lat,
            lon=lon,
            target_date=d_obj,
            solunar_data=solunar_d,
            weather_hourly=weather_raw.get("hourly", {})
        )
        scores_d = [h.score for h in activities_d]
        score = round(sum(scores_d) / len(scores_d)) if scores_d else 50
        rating = get_rating_label(score)

        day_summaries.append(DaySummary(
            date=d_str,
            day_name=day_name,
            day_number=d_obj.day,
            month_name=MONTH_NAMES_IT[d_obj.month - 1],
            score=score,
            rating=rating,
            moon_phase_name=phase_name,
            moon_phase_icon=moon_icons.get(phase_name, "moon"),
            temp_min=t_min[i] if i < len(t_min) and t_min[i] is not None else 12.0,
            temp_max=t_max[i] if i < len(t_max) and t_max[i] is not None else 22.0,
            weather_code=weather_codes[i] if i < len(weather_codes) and weather_codes[i] is not None else 0,
            wind_knots_max=kmh_to_knots(w_max[i] if i < len(w_max) and w_max[i] is not None else 15.0)
        ))

    return ForecastSummaryResponse(
        latitude=lat,
        longitude=lon,
        days=day_summaries
    )
