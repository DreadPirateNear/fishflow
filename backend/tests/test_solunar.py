from datetime import date
from app.services.solunar import calculate_solunar_data, get_moon_phase_info, compute_hourly_solunar_score


def test_moon_phase_info():
    test_date = date(2026, 11, 1)
    phase_name, illum, is_perigee = get_moon_phase_info(test_date)
    assert isinstance(phase_name, str)
    assert 0.0 <= illum <= 1.0
    assert isinstance(is_perigee, bool)


def test_calculate_solunar_data():
    lat = 44.05
    lon = 12.56
    test_date = date(2026, 11, 1)
    solunar = calculate_solunar_data(lat, lon, test_date)

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



def test_compute_hourly_solunar_score():
    lat = 44.05
    lon = 12.56
    test_date = date(2026, 11, 1)
    solunar = calculate_solunar_data(lat, lon, test_date)

    score, is_major, is_minor = compute_hourly_solunar_score(12, test_date, solunar)
    assert 0 <= score <= 100
    assert isinstance(is_major, bool)
    assert isinstance(is_minor, bool)
