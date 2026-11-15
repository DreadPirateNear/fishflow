import math
from datetime import date, datetime, time, timedelta
from typing import List, Dict, Any, Tuple, Optional
import ephem
from app.models.schemas import HourlyActivity, SolunarData
from app.services.solunar import compute_hourly_solunar_score
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
    Computes barometric score (0-100) based on 3-hour pressure change delta_p = P(t) - P(t-3).
    A smooth, continuous curve:
    - -3.0 <= delta_p <= -1.0: optimal pre-frontal feeding surge (score 90-98).
    - -1.0 < delta_p <= -0.5: slight drop, active fish (score 80-90).
    - -0.5 < delta_p <= 0.5: stable barometric conditions (score 60-70).
    - 0.5 < delta_p <= 1.5: rising pressure, slower feeding (score 40-55).
    - 1.5 < delta_p <= 2.5: rapid post-frontal clearing, lethargy (score 25-35).
    - delta_p > 2.5: severe post-frontal rise, locked jaws (score 15-20).
    - delta_p < -3.0: dangerous squall / thunderstorm crash (score 20-30).
    """
    if -3.0 <= delta_p <= -1.0:
        # Peak zone: interpolate between 90 and 98 with maximum around -2.0
        peak = 98.0 - 8.0 * abs(delta_p - (-2.0))
        return round(max(90, min(98, peak)))
    elif -1.0 < delta_p <= -0.5:
        # Transition from 80 at -0.5 to 90 at -1.0
        t = (delta_p - (-0.5)) / (-0.5)
        return round(80.0 + 10.0 * t)
    elif -0.5 < delta_p <= 0.5:
        # Stable band around 65
        return round(65.0 - 5.0 * (delta_p / 0.5))
    elif 0.5 < delta_p <= 1.5:
        # Transition from 55 at 0.5 down to 40 at 1.5
        t = (delta_p - 0.5) / 1.0
        return round(55.0 - 15.0 * t)
    elif 1.5 < delta_p <= 2.5:
        # Transition from 35 at 1.5 down to 22 at 2.5
        t = (delta_p - 1.5) / 1.0
        return round(35.0 - 13.0 * t)
    elif delta_p > 2.5:
        return 18
    else:
        # delta_p < -3.0: violent storm crash
        return 25


def compute_light_score_from_altitude(alt_degrees: float) -> int:
    """
    Calculates light score (0-100) based on solar elevation angle.
    Twilight / Golden hour (-8° to +6°) is prime predator feeding time.
    """
    if -8.0 <= alt_degrees <= 6.0:
        # Twilight peak
        center = -1.0
        dist = abs(alt_degrees - center)
        return round(96.0 - (dist / 7.0) * 10.0)
    elif 6.0 < alt_degrees <= 25.0:
        # Morning / late afternoon pleasant angled light
        t = (alt_degrees - 6.0) / 19.0
        return round(80.0 - t * 15.0)
    elif alt_degrees > 25.0:
        # Harsh overhead sun causing glare
        t = min(1.0, (alt_degrees - 25.0) / 45.0)
        return round(45.0 - t * 12.0)
    elif -18.0 <= alt_degrees < -8.0:
        # Deep astronomical twilight
        t = (alt_degrees - (-18.0)) / 10.0
        return round(50.0 + t * 25.0)
    else:
        # Night
        return 35


def compute_wind_weather_score(wind_knots: float, cloud_cover: float, weather_code: int) -> int:
    """
    Evaluates surface agitation and atmospheric conditions.
    Optimal wind: 4-12 knots (creates chop, hides terminal tackle, stimulates predatory ambushes).
    """
    # Wind component
    if 4.0 <= wind_knots <= 12.0:
        # Optimal ripple zone
        w_score = 92.0 - abs(wind_knots - 8.0) * 1.5
    elif 2.0 <= wind_knots < 4.0:
        w_score = 65.0 + (wind_knots - 2.0) * 10.0
    elif wind_knots < 2.0:
        w_score = 45.0  # Glassy calm, fish are spooked easily
    elif 12.0 < wind_knots <= 16.0:
        w_score = 80.0 - (wind_knots - 12.0) * 2.5
    elif 16.0 < wind_knots <= 22.0:
        w_score = 65.0 - (wind_knots - 16.0) * 4.0
    else:
        w_score = max(15.0, 40.0 - (wind_knots - 22.0) * 3.0)

    # Cloud cover modifier (+10 pts when overcast reduces glare)
    if 40.0 <= cloud_cover <= 80.0:
        c_bonus = 10.0
    elif cloud_cover > 80.0:
        c_bonus = 6.0
    else:
        c_bonus = (cloud_cover / 40.0) * 5.0

    # Weather code modifier
    if weather_code in [51, 53, 61]:  # Light drizzle
        m_mod = 8.0
    elif weather_code in [95, 96, 99]:  # Thunderstorm
        m_mod = -40.0
    elif weather_code in [65, 82]:  # Torrential downpour
        m_mod = -20.0
    else:
        m_mod = 0.0

    return round(max(10.0, min(100.0, w_score + c_bonus + m_mod)))


def compute_24h_activity(
    lat: float,
    lon: float,
    target_date: date,
    solunar_data: SolunarData,
    weather_hourly: Dict[str, List[Any]],
    marine_hourly: Optional[Dict[str, List[Any]]] = None,
    tz_offset_hours: float = 1.0
) -> List[HourlyActivity]:
    """
    Computes the 24 hourly activity items for target_date using continuous calibrated weights:
    Score = 0.35 * Solunar + 0.35 * Pressure + 0.15 * Light + 0.15 * Weather
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

    # Marine hourly series
    marine_h = marine_hourly or {}
    marine_times = marine_h.get("time", [])
    wave_heights = marine_h.get("wave_height", [])
    wave_periods = marine_h.get("wave_period", [])
    wave_directions = marine_h.get("wave_direction", [])

    date_str = target_date.isoformat()
    hourly_activities: List[HourlyActivity] = []

    # Map timestamps to find indices for target_date
    date_indices = []
    for i, t in enumerate(times):
        if t.startswith(date_str):
            date_indices.append(i)

    if len(date_indices) < 24:
        date_indices = list(range(min(24, len(times)))) if times else list(range(24))

    # Marine indices
    marine_indices = []
    for i, t in enumerate(marine_times):
        if t.startswith(date_str):
            marine_indices.append(i)

    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)

    for hour in range(24):
        idx = date_indices[hour] if hour < len(date_indices) else hour
        p_curr = pressures[idx] if idx < len(pressures) and pressures[idx] is not None else 1013.25

        # 3-hour barometric derivative
        if idx >= 3 and pressures[idx - 3] is not None:
            delta_p = round(p_curr - pressures[idx - 3], 2)
        elif len(pressures) > 0 and pressures[0] is not None:
            delta_p = 0.0
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

        # Hourly Marine data mapping
        m_idx = marine_indices[hour] if hour < len(marine_indices) else None
        h_wave = wave_heights[m_idx] if m_idx is not None and m_idx < len(wave_heights) else None
        h_period = wave_periods[m_idx] if m_idx is not None and m_idx < len(wave_periods) else None
        h_dir = wave_directions[m_idx] if m_idx is not None and m_idx < len(wave_directions) else None

        # Solar elevation angle
        dt_utc = datetime.combine(target_date, time(hour, 0)) - timedelta(hours=tz_offset_hours)
        observer.date = ephem.Date(dt_utc)
        sun = ephem.Sun(observer)
        alt_degrees = float(sun.alt) * 180.0 / 3.1415926535

        # Individual scientific scores (0-100)
        solunar_score, is_major, is_minor = compute_hourly_solunar_score(hour, target_date, solunar_data)
        baro_score = compute_barometric_score(delta_p)
        light_score = compute_light_score_from_altitude(alt_degrees)
        weather_score = compute_wind_weather_score(wind_knt, cloud, w_code)

        # Composite Continuous Score: 35% Solunar + 35% Pressure + 15% Light + 15% Weather
        composite = (
            0.35 * float(solunar_score) +
            0.35 * float(baro_score) +
            0.15 * float(light_score) +
            0.15 * float(weather_score)
        )
        overall_score = max(5, min(98, round(composite)))
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
            wave_height=round(h_wave, 2) if h_wave is not None else None,
            wave_period=round(h_period, 1) if h_period is not None else None,
            wave_direction=round(h_dir, 0) if h_dir is not None else None,
            is_major_window=is_major,
            is_minor_window=is_minor
        ))

    return hourly_activities
