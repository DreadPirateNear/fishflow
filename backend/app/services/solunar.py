import math
from datetime import datetime, date, time, timedelta
from typing import List, Tuple, Dict, Any, Optional
import ephem
from app.models.schemas import SolunarData, SolunarWindow


def compute_daily_solunar_baseline(target_date: date) -> int:
    """
    Computes intrinsic daily solunar activity baseline (10-95) based on Solunar Theory.
    Syzygy (Full/New Moon) -> ~80-90.
    Quadrature (First/Last Quarter) -> ~15-22 ("Molto bassa").
    """
    d = ephem.Date(target_date)
    p_nm = ephem.previous_new_moon(d)
    n_nm = ephem.next_new_moon(d)
    p_fm = ephem.previous_full_moon(d)
    n_fm = ephem.next_full_moon(d)
    min_dist = min([abs(float(d - x)) for x in (p_nm, n_nm, p_fm, n_fm)])

    # Half synodic cycle is ~7.38 days (Syzygy to Quadrature)
    cos_val = math.cos(min(7.38, min_dist) / 7.38 * math.pi)
    factor = (1.0 + cos_val) / 2.0
    solunar_base = 14.0 + 74.0 * (factor ** 1.3)

    m = ephem.Moon(d)
    dist_km = float(m.earth_distance) * 149597870.7
    if dist_km < 363000:
        solunar_base += 5.0
    elif dist_km > 400000:
        solunar_base -= 5.0

    return round(max(10, min(95, solunar_base)))


def get_moon_phase_info(target_date: date) -> Tuple[str, float, bool]:
    """
    Returns (moon_phase_name, illumination_fraction, is_perigee)
    """
    d = ephem.Date(target_date)
    moon = ephem.Moon(d)
    sun = ephem.Sun(d)
    
    # Calculate phase angle
    elongation = float(ephem.separation(moon, sun))
    illumination = moon.moon_phase  # 0.0 to 1.0
    
    # Check if waxing or waning: look at phase tomorrow
    moon_tomorrow = ephem.Moon(ephem.Date(target_date + timedelta(days=1)))
    waxing = moon_tomorrow.moon_phase > illumination
    
    if illumination < 0.05:
        phase_name = "Luna Nuova"
    elif illumination > 0.95:
        phase_name = "Luna Piena"
    elif abs(illumination - 0.5) < 0.08:
        phase_name = "Primo Quarto" if waxing else "Ultimo Quarto"
    elif illumination < 0.5:
        phase_name = "Luna Crescente" if waxing else "Luna Calante"
    else:
        phase_name = "Gibbosa Crescente" if waxing else "Gibbosa Calante"
        
    # Check perigee (distance in Earth radii; average is ~60.3, perigee is < 57.5)
    is_perigee = moon.earth_distance < 57.5
    
    return phase_name, round(illumination, 2), is_perigee


def _format_ephem_time(ephem_date: Optional[ephem.Date], tz_offset_hours: int = 0) -> Optional[str]:
    if not ephem_date:
        return None
    try:
        dt = ephem.Date(ephem_date).datetime() + timedelta(hours=tz_offset_hours)
        return dt.strftime("%H:%M")
    except Exception:
        return None


def calculate_solunar_data(lat: float, lon: float, target_date: date, tz_offset_hours: int = 1) -> SolunarData:
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.elevation = 0
    # Set time to midday target date in UTC
    target_dt_midday = datetime.combine(target_date, time(12, 0)) - timedelta(hours=tz_offset_hours)
    observer.date = ephem.Date(target_dt_midday)

    sun = ephem.Sun(observer)
    moon = ephem.Moon(observer)

    # Sunrise / Sunset & day/night duration
    try:
        observer.horizon = '0'
        sunrise_d = observer.previous_rising(sun)
        sunset_d = observer.next_setting(sun)
        sunrise_str = _format_ephem_time(sunrise_d, tz_offset_hours)
        sunset_str = _format_ephem_time(sunset_d, tz_offset_hours)
        day_min = max(0, min(1440, round(float(sunset_d - sunrise_d) * 24 * 60)))
        night_min = 1440 - day_min
    except Exception:
        sunrise_str, sunset_str = "06:30", "18:30"
        day_min = 720
        night_min = 720

    # Solar noon (sun culmination)
    try:
        transit_sun = observer.previous_transit(sun)
        if abs(float(observer.date - transit_sun)) > 0.5:
            transit_sun = observer.next_transit(sun)
        solar_noon_str = _format_ephem_time(transit_sun, tz_offset_hours)
    except Exception:
        solar_noon_str = "12:00"

    # Civil twilight (-6 degrees)
    try:
        observer.horizon = '-6'
        civil_dawn_d = observer.previous_rising(sun, use_center=True)
        civil_dusk_d = observer.next_setting(sun, use_center=True)
        civil_dawn_str = _format_ephem_time(civil_dawn_d, tz_offset_hours)
        civil_dusk_str = _format_ephem_time(civil_dusk_d, tz_offset_hours)
    except Exception:
        civil_dawn_str, civil_dusk_str = "06:00", "19:00"

    # Reset horizon for moon
    observer.horizon = '0'
    try:
        moonrise_d = observer.previous_rising(moon)
        moonset_d = observer.next_setting(moon)
        moon_transit_d = observer.previous_transit(moon)
        moon_nadir_d = observer.previous_antitransit(moon)
    except Exception:
        moonrise_d = moonset_d = moon_transit_d = moon_nadir_d = None

    moonrise_str = _format_ephem_time(moonrise_d, tz_offset_hours) or "08:15"
    moonset_str = _format_ephem_time(moonset_d, tz_offset_hours) or "20:45"
    transit_str = _format_ephem_time(moon_transit_d, tz_offset_hours) or "14:30"
    nadir_str = _format_ephem_time(moon_nadir_d, tz_offset_hours) or "02:30"

    phase_name, illumination, is_perigee = get_moon_phase_info(target_date)

    # Moon distance in km and age in days
    try:
        moon_dist_km = round(float(moon.earth_distance) * 149597870.7, 1)
    except Exception:
        moon_dist_km = 384400.0

    try:
        prev_nm = ephem.previous_new_moon(observer.date)
        moon_age_days = round(float(observer.date - prev_nm), 1)
    except Exception:
        moon_age_days = 0.0

    # Build Major Windows (±75 min around Transit and Nadir)
    major_windows = []
    if moon_transit_d:
        dt_zenith = ephem.Date(moon_transit_d).datetime() + timedelta(hours=tz_offset_hours)
        major_windows.append(SolunarWindow(
            start=(dt_zenith - timedelta(minutes=75)).strftime("%H:%M"),
            end=(dt_zenith + timedelta(minutes=75)).strftime("%H:%M"),
            window_type="major",
            description="Zenit Lunare (Culminazione)"
        ))
    if moon_nadir_d:
        dt_nadir = ephem.Date(moon_nadir_d).datetime() + timedelta(hours=tz_offset_hours)
        major_windows.append(SolunarWindow(
            start=(dt_nadir - timedelta(minutes=75)).strftime("%H:%M"),
            end=(dt_nadir + timedelta(minutes=75)).strftime("%H:%M"),
            window_type="major",
            description="Nadir Lunare (Underfoot)"
        ))

    # Build Minor Windows (±45 min around Rise and Set)
    minor_windows = []
    if moonrise_d:
        dt_rise = ephem.Date(moonrise_d).datetime() + timedelta(hours=tz_offset_hours)
        minor_windows.append(SolunarWindow(
            start=(dt_rise - timedelta(minutes=45)).strftime("%H:%M"),
            end=(dt_rise + timedelta(minutes=45)).strftime("%H:%M"),
            window_type="minor",
            description="Levata della Luna"
        ))
    if moonset_d:
        dt_set = ephem.Date(moonset_d).datetime() + timedelta(hours=tz_offset_hours)
        minor_windows.append(SolunarWindow(
            start=(dt_set - timedelta(minutes=45)).strftime("%H:%M"),
            end=(dt_set + timedelta(minutes=45)).strftime("%H:%M"),
            window_type="minor",
            description="Calo della Luna"
        ))

    return SolunarData(
        moon_phase_name=phase_name,
        moon_illumination=illumination,
        moon_distance_km=moon_dist_km,
        moon_age_days=moon_age_days,
        is_perigee=is_perigee,
        moonrise=moonrise_str,
        moonset=moonset_str,
        moon_transit=transit_str,
        moon_underfoot=nadir_str,
        sunrise=sunrise_str,
        sunset=sunset_str,
        solar_noon=solar_noon_str,
        civil_dawn=civil_dawn_str,
        civil_dusk=civil_dusk_str,
        day_duration_minutes=day_min,
        night_duration_minutes=night_min,
        major_windows=major_windows,
        minor_windows=minor_windows
    )


def compute_hourly_solunar_score(
    hour: int,
    target_date: date,
    solunar_data: SolunarData
) -> Tuple[int, bool, bool]:
    """
    Returns (score 0-100, is_major, is_minor) for a given hour.
    """
    dt_hour = datetime.combine(target_date, time(hour, 0))
    
    is_major = False
    is_minor = False

    for w in solunar_data.major_windows:
        sh, sm = map(int, w.start.split(":"))
        eh, em = map(int, w.end.split(":"))
        dt_start = datetime.combine(target_date, time(sh, sm))
        dt_end = datetime.combine(target_date, time(eh, em))
        if dt_start <= dt_hour <= dt_end or (eh < sh and (dt_hour >= dt_start or dt_hour <= dt_end)):
            is_major = True
            break

    if not is_major:
        for w in solunar_data.minor_windows:
            sh, sm = map(int, w.start.split(":"))
            eh, em = map(int, w.end.split(":"))
            dt_start = datetime.combine(target_date, time(sh, sm))
            dt_end = datetime.combine(target_date, time(eh, em))
            if dt_start <= dt_hour <= dt_end or (eh < sh and (dt_hour >= dt_start or dt_hour <= dt_end)):
                is_minor = True
                break

    daily_base = compute_daily_solunar_baseline(target_date)
    scale = max(0.2, min(1.3, daily_base / 75.0))

    if is_major:
        score = min(98, daily_base + round(16 * scale))
    elif is_minor:
        score = min(92, daily_base + round(8 * scale))
    else:
        score = daily_base

    return score, is_major, is_minor
