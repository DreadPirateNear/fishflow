from datetime import date, datetime, time, timedelta
from typing import List, Dict, Any, Tuple, Optional
import ephem
from app.models.schemas import HourlyActivity, SolunarData
from app.services.solunar import compute_hourly_solunar_score, compute_daily_solunar_baseline
from app.services.weather import kmh_to_knots


def get_rating_label(score: int) -> str:
    if score >= 75:
        return "Eccellente"
    elif score >= 55:
        return "Buona"
    elif score >= 38:
        return "Media"
    elif score >= 23:
        return "Bassa"
    else:
        return "Molto bassa"


def compute_barometric_score(delta_p: float) -> int:
    """
    Computes score (0-100) based on 3-hour pressure change delta_p = P(t) - P(t-3).
    """
    if -3.0 <= delta_p <= -1.0:
        # Ideal slow drop ahead of weather front: fish feed intensely
        return 95
    elif -1.0 < delta_p <= -0.5:
        return 80
    elif -0.5 < delta_p <= 0.5:
        # Stable pressure: standard normal feeding
        return 65
    elif 0.5 < delta_p <= 1.5:
        # Slowly rising: activity slows down
        return 50
    elif 1.5 < delta_p <= 2.5:
        # Rapid rise: post-frontal apathy
        return 35
    elif delta_p > 2.5:
        # Severe rise: fish lock jaws
        return 20
    else:
        # Severe crash (delta_p < -3.0): dangerous squall / thunderstorm approaching
        return 30


def compute_light_score(lat: float, lon: float, target_date: date, hour: int, tz_offset_hours: int = 1) -> int:
    """
    Calculates solar elevation and gives twilight boost.
    """
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    dt_utc = datetime.combine(target_date, time(hour, 0)) - timedelta(hours=tz_offset_hours)
    observer.date = ephem.Date(dt_utc)

    sun = ephem.Sun(observer)
    alt_degrees = float(sun.alt) * 180.0 / 3.1415926535

    # Civil & Nautical Twilight: sun altitude between -8° and +6°
    if -8.0 <= alt_degrees <= 6.0:
        return 95  # Golden hour / twilight peak
    elif 6.0 < alt_degrees <= 25.0:
        return 75  # Morning / late afternoon pleasant light
    elif alt_degrees > 25.0:
        return 45  # Bright overhead midday sun
    elif -18.0 <= alt_degrees < -8.0:
        return 60  # Deep dusk / early dawn
    else:
        return 35  # Dead of night


def compute_wind_weather_score(wind_knots: float, cloud_cover: float, weather_code: int) -> int:
    # Wind factor (4 to 12 knots is optimal for surface ripple)
    if 4.0 <= wind_knots <= 12.0:
        w_score = 90
    elif 12.0 < wind_knots <= 16.0:
        w_score = 75
    elif 2.0 <= wind_knots < 4.0:
        w_score = 65
    elif wind_knots < 2.0:
        w_score = 45  # Glassy calm, fish are cautious
    else:
        w_score = 30  # Heavy wind / gale

    # Cloud cover bonus (moderate clouds reduce glare)
    if 40.0 <= cloud_cover <= 80.0:
        c_bonus = 10
    elif cloud_cover > 80.0:
        c_bonus = 5
    else:
        c_bonus = 0

    # Weather code penalty / bonus
    # WMO: 51, 61 light rain bonus
    # WMO: 95, 96, 99 thunderstorm penalty
    if weather_code in [51, 53, 61]:
        m_mod = 10  # Light drizzle stimulates feeding
    elif weather_code in [95, 96, 99]:
        m_mod = -40  # Thunderstorm shut down
    elif weather_code in [65, 82]:
        m_mod = -20  # Torrential downpour
    else:
        m_mod = 0

    final = max(10, min(100, w_score + c_bonus + m_mod))
    return final


def compute_barometric_delta(delta_p: float) -> int:
    """
    Computes additive delta (-12 to +10) from barometric trend.
    """
    if -3.0 <= delta_p <= -1.0:
        return 10  # Optimal drop ahead of front
    elif -1.0 < delta_p <= -0.5:
        return 5
    elif -0.5 < delta_p <= 0.5:
        return 0   # Stable pressure = neutral
    elif 0.5 < delta_p <= 1.5:
        return -4  # Slow rise
    elif 1.5 < delta_p <= 2.5:
        return -8  # Sharp rise
    elif delta_p > 2.5:
        return -12 # Severe post-frontal shutdown
    else:
        return -8  # Severe crash / squall


def compute_light_delta(alt_degrees: float) -> int:
    if -8.0 <= alt_degrees <= 6.0:
        return 8   # Twilight peak / golden hour
    elif 6.0 < alt_degrees <= 25.0:
        return 3   # Morning / late afternoon pleasant light
    elif alt_degrees > 25.0:
        return -2  # Harsh midday glare
    elif -18.0 <= alt_degrees < -8.0:
        return 0   # Early dawn / dusk
    else:
        return -4  # Dead of night


def compute_wind_weather_delta(wind_knots: float, cloud_cover: float, weather_code: int) -> int:
    delta = 0
    if 4.0 <= wind_knots <= 12.0:
        delta += 3
    elif wind_knots < 2.0:
        delta -= 2
    elif wind_knots > 18.0:
        delta -= 10

    if 40.0 <= cloud_cover <= 80.0:
        delta += 2

    if weather_code in [51, 53, 61]:
        delta += 4
    elif weather_code in [95, 96, 99]:
        delta -= 20
    elif weather_code in [65, 82]:
        delta -= 10
    return delta


def compute_24h_activity(
    lat: float,
    lon: float,
    target_date: date,
    solunar_data: SolunarData,
    weather_hourly: Dict[str, List[Any]],
    marine_wave_height: Optional[float] = None,
    tz_offset_hours: int = 1
) -> List[HourlyActivity]:
    """
    Computes the 24 hourly activity items for target_date.
    """
    times = weather_hourly.get("time", [])
    pressures = weather_hourly.get("surface_pressure", [])
    temperatures = weather_hourly.get("temperature_2m", [])
    apparent_temps = weather_hourly.get("apparent_temperature", [])
    humidities = weather_hourly.get("relative_humidity_2m", [])
    precip_probs = weather_hourly.get("precipitation_probability", [])
    precipitations = weather_hourly.get("precipitation", [])
    winds_kmh = weather_hourly.get("wind_speed_10m", [])
    wind_dirs = weather_hourly.get("wind_direction_10m", [])
    wind_gusts_kmh = weather_hourly.get("wind_gusts_10m", [])
    uv_indices = weather_hourly.get("uv_index", [])
    clouds = weather_hourly.get("cloud_cover", [])
    weather_codes = weather_hourly.get("weather_code", [])

    date_str = target_date.isoformat()
    hourly_activities = []

    # Map timestamps to find the indices for target_date 00:00 to 23:00
    date_indices = []
    for i, t in enumerate(times):
        if t.startswith(date_str):
            date_indices.append(i)

    # If not found or fewer than 24, fallback
    if len(date_indices) < 24:
        date_indices = list(range(min(24, len(times))))

    for hour in range(24):
        idx = date_indices[hour] if hour < len(date_indices) else hour
        p_curr = pressures[idx] if idx < len(pressures) and pressures[idx] is not None else 1013.25
        # Calculate delta_p from 3 hours prior (idx - 3)
        if idx >= 3 and pressures[idx - 3] is not None:
            delta_p = round(p_curr - pressures[idx - 3], 2)
        else:
            delta_p = 0.0

        temp = temperatures[idx] if idx < len(temperatures) and temperatures[idx] is not None else 18.0
        app_temp = apparent_temps[idx] if idx < len(apparent_temps) and apparent_temps[idx] is not None else temp
        humidity = humidities[idx] if idx < len(humidities) and humidities[idx] is not None else 65.0
        precip_prob = precip_probs[idx] if idx < len(precip_probs) and precip_probs[idx] is not None else 0.0
        precip = precipitations[idx] if idx < len(precipitations) and precipitations[idx] is not None else 0.0
        uv = uv_indices[idx] if idx < len(uv_indices) and uv_indices[idx] is not None else 0.0
        wind_kmh = winds_kmh[idx] if idx < len(winds_kmh) and winds_kmh[idx] is not None else 10.0
        wind_knt = kmh_to_knots(wind_kmh)
        wind_gust_kmh = wind_gusts_kmh[idx] if idx < len(wind_gusts_kmh) and wind_gusts_kmh[idx] is not None else None
        wind_gust_knt = kmh_to_knots(wind_gust_kmh) if wind_gust_kmh is not None else None
        wind_dir = wind_dirs[idx] if idx < len(wind_dirs) and wind_dirs[idx] is not None else 180.0
        cloud = clouds[idx] if idx < len(clouds) and clouds[idx] is not None else 30.0
        w_code = weather_codes[idx] if idx < len(weather_codes) and weather_codes[idx] is not None else 0

        # Calculate solar altitude for light score and delta
        observer = ephem.Observer()
        observer.lat = str(lat)
        observer.lon = str(lon)
        dt_utc = datetime.combine(target_date, time(hour, 0)) - timedelta(hours=tz_offset_hours)
        observer.date = ephem.Date(dt_utc)
        sun = ephem.Sun(observer)
        alt_degrees = float(sun.alt) * 180.0 / 3.1415926535

        # Individual 0-100 scores for telemetry display
        solunar_score, is_major, is_minor = compute_hourly_solunar_score(hour, target_date, solunar_data)
        baro_score = compute_barometric_score(delta_p)
        light_score = compute_light_score(lat, lon, target_date, hour, tz_offset_hours)
        weather_score = compute_wind_weather_score(wind_knt, cloud, w_code)

        daily_base = compute_daily_solunar_baseline(target_date)
        scale = max(0.25, min(1.3, daily_base / 75.0))

        # Environmental deltas scaled relative to solunar baseline
        baro_delta = round(compute_barometric_delta(delta_p) * scale)
        light_delta = round(compute_light_delta(alt_degrees) * scale)
        weather_delta = round(compute_wind_weather_delta(wind_knt, cloud, w_code) * scale)

        # Overall fish activity score anchored in Solunar baseline
        overall_score = max(5, min(98, solunar_score + light_delta + baro_delta + weather_delta))
        rating = get_rating_label(overall_score)

        iso_time = f"{date_str}T{hour:02d}:00"
        hourly_activities.append(HourlyActivity(
            time=iso_time,
            hour=hour,
            score=overall_score,
            rating=rating,
            solunar_score=solunar_score,
            barometric_score=baro_score,
            light_score=light_score,
            weather_score=weather_score,
            temperature=round(temp, 1),
            apparent_temperature=round(app_temp, 1),
            relative_humidity=round(humidity, 1),
            pressure=round(p_curr, 1),
            pressure_trend_3h=delta_p,
            wind_knots=wind_knt,
            wind_direction=round(wind_dir, 0),
            wind_gusts_knots=wind_gust_knt,
            precipitation=round(precip, 1),
            precipitation_probability=round(precip_prob, 0),
            uv_index=round(uv, 1) if uv is not None else None,
            weather_code=w_code,
            wave_height=marine_wave_height,
            is_major_window=is_major,
            is_minor_window=is_minor
        ))

    return hourly_activities
