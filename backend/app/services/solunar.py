import math
from datetime import datetime, date, time, timedelta
from typing import List, Tuple, Dict, Any, Optional
import ephem
from app.models.schemas import SolunarData, SolunarWindow


def estimate_solar_tz_offset(lon: float) -> float:
    """
    Estimates civil/solar time offset in hours from longitude (15 degrees per hour).
    Used as an offline fallback when external timezone data is unavailable.
    """
    return round(lon / 15.0)


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


def get_moon_phase_info(target_date: date, tz_offset_hours: float = 0.0) -> Tuple[str, float, bool]:
    """
    Returns (moon_phase_name, illumination_fraction, is_perigee)
    """
    # Midday local time converted to UTC
    midday_utc = datetime.combine(target_date, time(12, 0)) - timedelta(hours=tz_offset_hours)
    d = ephem.Date(midday_utc)
    moon = ephem.Moon(d)
    sun = ephem.Sun(d)

    illumination = float(moon.moon_phase)  # 0.0 to 1.0

    # Waxing / Waning check 24 hours later
    moon_tomorrow = ephem.Moon(ephem.Date(d + 1.0))
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

    # Perigee in km (Moon distance < 363,000 km is perigee)
    dist_km = float(moon.earth_distance) * 149597870.7
    is_perigee = dist_km < 363000.0

    return phase_name, round(illumination, 2), is_perigee


def _ephem_to_local_str(ephem_date: Optional[ephem.Date], tz_offset_hours: float) -> Optional[str]:
    if not ephem_date:
        return None
    try:
        dt_local = ephem.Date(ephem_date).datetime() + timedelta(hours=tz_offset_hours)
        return dt_local.strftime("%H:%M")
    except Exception:
        return None


def calculate_solunar_data(
    lat: float,
    lon: float,
    target_date: date,
    tz_offset_hours: float = 1.0
) -> SolunarData:
    """
    Computes astronomical ephemeris and solunar event windows bounded strictly
    within the local calendar day [00:00, 24:00] for the given coordinates and timezone offset.
    """
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.elevation = 0

    # Start and end of the local day in UTC
    dt_local_start_utc = datetime.combine(target_date, time(0, 0)) - timedelta(hours=tz_offset_hours)
    dt_local_end_utc = dt_local_start_utc + timedelta(hours=24)

    observer.date = ephem.Date(dt_local_start_utc)

    sun = ephem.Sun()
    moon = ephem.Moon()

    # --- SUN CALCULATIONS ---
    # Sunrise & Sunset
    try:
        observer.horizon = '0'
        sun_rise_d = observer.next_rising(sun)
        sun_set_d = observer.next_setting(sun)

        # Check if events fall on today in local time
        sunrise_str = _ephem_to_local_str(sun_rise_d, tz_offset_hours) if sun_rise_d < ephem.Date(dt_local_end_utc) else None
        sunset_str = _ephem_to_local_str(sun_set_d, tz_offset_hours) if sun_set_d < ephem.Date(dt_local_end_utc) else None

        if sun_rise_d and sun_set_d and sun_set_d > sun_rise_d:
            day_min = max(0, min(1440, round(float(sun_set_d - sun_rise_d) * 24 * 60)))
        else:
            day_min = 720
        night_min = 1440 - day_min
    except Exception:
        sunrise_str, sunset_str = "06:30", "18:30"
        day_min, night_min = 720, 720

    # Solar noon (Culmination)
    try:
        solar_noon_d = observer.next_transit(sun)
        solar_noon_str = _ephem_to_local_str(solar_noon_d, tz_offset_hours) if solar_noon_d < ephem.Date(dt_local_end_utc) else "12:00"
    except Exception:
        solar_noon_str = "12:00"

    # Civil twilight (-6 degrees)
    try:
        observer.horizon = '-6'
        civil_dawn_d = observer.next_rising(sun, use_center=True)
        civil_dusk_d = observer.next_setting(sun, use_center=True)
        civil_dawn_str = _ephem_to_local_str(civil_dawn_d, tz_offset_hours) if civil_dawn_d < ephem.Date(dt_local_end_utc) else None
        civil_dusk_str = _ephem_to_local_str(civil_dusk_d, tz_offset_hours) if civil_dusk_d < ephem.Date(dt_local_end_utc) else None
    except Exception:
        civil_dawn_str, civil_dusk_str = "06:00", "19:00"

    # --- MOON CALCULATIONS ---
    observer.horizon = '0'
    moon_events_zenith: List[datetime] = []
    moon_events_nadir: List[datetime] = []
    moon_events_rise: List[datetime] = []
    moon_events_set: List[datetime] = []

    # Check for transits around the 24h boundary (search from -2h to +26h)
    search_start = ephem.Date(dt_local_start_utc - timedelta(hours=2))
    search_end = ephem.Date(dt_local_end_utc + timedelta(hours=2))

    observer.date = search_start
    # Collect Moon Transits (Zenith)
    try:
        curr = observer.next_transit(moon)
        while curr < search_end:
            dt_local = ephem.Date(curr).datetime() + timedelta(hours=tz_offset_hours)
            moon_events_zenith.append(dt_local)
            observer.date = ephem.Date(curr + 0.05)
            curr = observer.next_transit(moon)
    except Exception:
        pass

    # Collect Moon Antitransits (Nadir)
    observer.date = search_start
    try:
        curr = observer.next_antitransit(moon)
        while curr < search_end:
            dt_local = ephem.Date(curr).datetime() + timedelta(hours=tz_offset_hours)
            moon_events_nadir.append(dt_local)
            observer.date = ephem.Date(curr + 0.05)
            curr = observer.next_antitransit(moon)
    except Exception:
        pass

    # Collect Moonrise & Moonset
    observer.date = ephem.Date(dt_local_start_utc)
    try:
        m_rise = observer.next_rising(moon)
        if m_rise < ephem.Date(dt_local_end_utc):
            moon_events_rise.append(ephem.Date(m_rise).datetime() + timedelta(hours=tz_offset_hours))
    except Exception:
        pass

    observer.date = ephem.Date(dt_local_start_utc)
    try:
        m_set = observer.next_setting(moon)
        if m_set < ephem.Date(dt_local_end_utc):
            moon_events_set.append(ephem.Date(m_set).datetime() + timedelta(hours=tz_offset_hours))
    except Exception:
        pass

    moonrise_str = moon_events_rise[0].strftime("%H:%M") if moon_events_rise else None
    moonset_str = moon_events_set[0].strftime("%H:%M") if moon_events_set else None
    transit_str = moon_events_zenith[0].strftime("%H:%M") if moon_events_zenith else None
    nadir_str = moon_events_nadir[0].strftime("%H:%M") if moon_events_nadir else None

    # Moon distance & age
    midday_utc = datetime.combine(target_date, time(12, 0)) - timedelta(hours=tz_offset_hours)
    observer.date = ephem.Date(midday_utc)
    moon.compute(observer)
    moon_dist_km = round(float(moon.earth_distance) * 149597870.7, 1)

    try:
        prev_nm = ephem.previous_new_moon(observer.date)
        moon_age_days = round(float(observer.date - prev_nm), 1)
    except Exception:
        moon_age_days = 0.0

    phase_name, illumination, is_perigee = get_moon_phase_info(target_date, tz_offset_hours)

    # Build Major Windows (±75 min around Zenith and Nadir)
    major_windows: List[SolunarWindow] = []
    for dt_zen in moon_events_zenith:
        w_start = dt_zen - timedelta(minutes=75)
        w_end = dt_zen + timedelta(minutes=75)
        # Include window if it intersects the target day
        if w_end.date() >= target_date and w_start.date() <= target_date:
            major_windows.append(SolunarWindow(
                start=w_start.strftime("%H:%M"),
                end=w_end.strftime("%H:%M"),
                window_type="major",
                description="Zenit Lunare (Culminazione)"
            ))

    for dt_nad in moon_events_nadir:
        w_start = dt_nad - timedelta(minutes=75)
        w_end = dt_nad + timedelta(minutes=75)
        if w_end.date() >= target_date and w_start.date() <= target_date:
            major_windows.append(SolunarWindow(
                start=w_start.strftime("%H:%M"),
                end=w_end.strftime("%H:%M"),
                window_type="major",
                description="Nadir Lunare (Underfoot)"
            ))

    # Build Minor Windows (±45 min around Moonrise and Moonset)
    minor_windows: List[SolunarWindow] = []
    for dt_r in moon_events_rise:
        w_start = dt_r - timedelta(minutes=45)
        w_end = dt_r + timedelta(minutes=45)
        if w_end.date() >= target_date and w_start.date() <= target_date:
            minor_windows.append(SolunarWindow(
                start=w_start.strftime("%H:%M"),
                end=w_end.strftime("%H:%M"),
                window_type="minor",
                description="Levata della Luna"
            ))

    for dt_s in moon_events_set:
        w_start = dt_s - timedelta(minutes=45)
        w_end = dt_s + timedelta(minutes=45)
        if w_end.date() >= target_date and w_start.date() <= target_date:
            minor_windows.append(SolunarWindow(
                start=w_start.strftime("%H:%M"),
                end=w_end.strftime("%H:%M"),
                window_type="minor",
                description="Calo della Luna"
            ))

    return SolunarData(
        moon_phase_name=phase_name,
        moon_illumination=illumination,
        moon_distance_km=moon_dist_km,
        moon_age_days=moon_age_days,
        is_perigee=is_perigee,
        moonrise=moonrise_str or "--:--",
        moonset=moonset_str or "--:--",
        moon_transit=transit_str or "--:--",
        moon_underfoot=nadir_str or "--:--",
        sunrise=sunrise_str or "--:--",
        sunset=sunset_str or "--:--",
        solar_noon=solar_noon_str or "12:00",
        civil_dawn=civil_dawn_str or "--:--",
        civil_dusk=civil_dusk_str or "--:--",
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
    Applies continuous proximity boosting to major and minor window centers.
    """
    dt_hour = datetime.combine(target_date, time(hour, 0))

    is_major = False
    is_minor = False
    max_boost = 0.0

    # Evaluate Major Windows (peak boost ~18 pts, Gaussian decay)
    for w in solunar_data.major_windows:
        try:
            sh, sm = map(int, w.start.split(":"))
            eh, em = map(int, w.end.split(":"))
            # Center of the window
            dt_s = datetime.combine(target_date, time(sh, sm))
            dt_e = datetime.combine(target_date, time(eh, em))
            if dt_e < dt_s:
                dt_e += timedelta(days=1)
            center = dt_s + (dt_e - dt_s) / 2
            diff_min = abs((dt_hour - center).total_seconds()) / 60.0
            if diff_min <= 75.0:
                is_major = True
                boost = 18.0 * math.exp(-0.5 * (diff_min / 35.0) ** 2)
                if boost > max_boost:
                    max_boost = boost
        except Exception:
            continue

    # Evaluate Minor Windows (peak boost ~10 pts)
    if not is_major:
        for w in solunar_data.minor_windows:
            try:
                sh, sm = map(int, w.start.split(":"))
                eh, em = map(int, w.end.split(":"))
                dt_s = datetime.combine(target_date, time(sh, sm))
                dt_e = datetime.combine(target_date, time(eh, em))
                if dt_e < dt_s:
                    dt_e += timedelta(days=1)
                center = dt_s + (dt_e - dt_s) / 2
                diff_min = abs((dt_hour - center).total_seconds()) / 60.0
                if diff_min <= 45.0:
                    is_minor = True
                    boost = 10.0 * math.exp(-0.5 * (diff_min / 25.0) ** 2)
                    if boost > max_boost:
                        max_boost = boost
            except Exception:
                continue

    daily_base = compute_daily_solunar_baseline(target_date)
    scale = max(0.25, min(1.3, daily_base / 75.0))
    final_score = round(max(10, min(98, daily_base + max_boost * scale)))

    return final_score, is_major, is_minor
