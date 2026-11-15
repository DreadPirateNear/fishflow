from datetime import date
from app.services.solunar import (
    calculate_solunar_data,
    get_moon_phase_info,
    compute_hourly_solunar_score,
    estimate_solar_tz_offset
)


def test_moon_phase_info():
    test_date = date(2026, 11, 1)
    phase_name, illum, is_perigee = get_moon_phase_info(test_date)
    assert isinstance(phase_name, str)
    assert 0.0 <= illum <= 1.0
    assert isinstance(is_perigee, bool)


def test_calculate_solunar_data_local():
    lat = 44.05
    lon = 12.56
    test_date = date(2026, 11, 1)
    solunar = calculate_solunar_data(lat, lon, test_date, tz_offset_hours=1.0)

    assert solunar.moonrise is not None
    assert solunar.moonset is not None
    assert solunar.sunrise is not None
    assert solunar.sunset is not None
    assert len(solunar.major_windows) > 0
    assert len(solunar.minor_windows) > 0
    assert solunar.moon_distance_km > 350000.0
    assert solunar.moon_age_days >= 0.0
    assert solunar.solar_noon is not None
    assert ":" in solunar.solar_noon
    assert solunar.day_duration_minutes + solunar.night_duration_minutes == 1440


def test_dynamic_timezone_new_york():
    # New York: lat 40.71, lon -74.00, standard time UTC-5
    lat = 40.71
    lon = -74.00
    test_date = date(2026, 11, 1)
    solunar_ny = calculate_solunar_data(lat, lon, test_date, tz_offset_hours=-5.0)

    # In local time, solar noon in NY must be close to 11:45-12:00
    noon_h, noon_m = map(int, solunar_ny.solar_noon.split(":"))
    assert 11 <= noon_h <= 12

    # Sunrise in NY in November is around 06:30 local time
    if solunar_ny.sunrise != "--:--":
        sr_h, sr_m = map(int, solunar_ny.sunrise.split(":"))
        assert 6 <= sr_h <= 7


def test_dynamic_timezone_tokyo():
    # Tokyo: lat 35.67, lon 139.65, standard time UTC+9
    lat = 35.67
    lon = 139.65
    test_date = date(2026, 11, 1)
    solunar_tokyo = calculate_solunar_data(lat, lon, test_date, tz_offset_hours=9.0)

    noon_h, noon_m = map(int, solunar_tokyo.solar_noon.split(":"))
    assert 11 <= noon_h <= 12


def test_solar_tz_offset_estimation():
    assert estimate_solar_tz_offset(12.56) == 1.0
    assert estimate_solar_tz_offset(-74.0) == -5.0
    assert estimate_solar_tz_offset(139.65) == 9.0


def test_compute_hourly_solunar_score():
    lat = 44.05
    lon = 12.56
    test_date = date(2026, 11, 1)
    solunar = calculate_solunar_data(lat, lon, test_date, tz_offset_hours=1.0)

    score, is_major, is_minor = compute_hourly_solunar_score(12, test_date, solunar)
    assert 0 <= score <= 100
    assert isinstance(is_major, bool)
    assert isinstance(is_minor, bool)
