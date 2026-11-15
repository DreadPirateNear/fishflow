from datetime import date
from app.services.scoring import (
    compute_barometric_score,
    compute_light_score_from_altitude,
    compute_wind_weather_score,
    get_rating_label,
    compute_24h_activity
)
from app.services.solunar import calculate_solunar_data


def test_barometric_scoring():
    # Ideal slow drop ahead of front: high score (90-98)
    assert 90 <= compute_barometric_score(-1.5) <= 98
    # Stable pressure: normal neutral activity (60-70)
    assert 60 <= compute_barometric_score(0.0) <= 70
    # Rapid rise / severe post-frontal rise: severe penalty (< 25)
    assert compute_barometric_score(3.0) <= 20


def test_light_scoring():
    # Twilight / golden hour: peak
    assert compute_light_score_from_altitude(0.0) >= 90
    # Harsh overhead sun: lower
    assert compute_light_score_from_altitude(50.0) <= 50
    # Dead of night
    assert compute_light_score_from_altitude(-30.0) == 35


def test_wind_weather_scoring():
    # Optimal wind 4-12 knots
    assert compute_wind_weather_score(8.0, 50.0, 1) >= 85
    # Glassy calm
    assert compute_wind_weather_score(1.0, 10.0, 1) <= 60
    # Thunderstorm penalty
    assert compute_wind_weather_score(8.0, 90.0, 95) <= 65


def test_rating_labels():
    assert get_rating_label(85) == "Eccellente"
    assert get_rating_label(60) == "Buona"
    assert get_rating_label(40) == "Media"
    assert get_rating_label(25) == "Bassa"
    assert get_rating_label(15) == "Molto bassa"


def test_24h_activity_computation_with_marine_hourly():
    lat = 44.05
    lon = 12.56
    test_date = date(2026, 11, 1)
    solunar = calculate_solunar_data(lat, lon, test_date, tz_offset_hours=1.0)

    mock_weather_hourly = {
        "time": [f"2026-11-01T{h:02d}:00" for h in range(24)],
        "surface_pressure": [1013.0 - (h * 0.1) for h in range(24)],
        "temperature_2m": [15.0 + (h * 0.2) for h in range(24)],
        "wind_speed_10m": [10.0 for _ in range(24)],
        "wind_direction_10m": [180.0 for _ in range(24)],
        "cloud_cover": [40.0 for _ in range(24)],
        "weather_code": [1 for _ in range(24)]
    }

    mock_marine_hourly = {
        "time": [f"2026-11-01T{h:02d}:00" for h in range(24)],
        "wave_height": [0.5 + (h * 0.05) for h in range(24)],
        "wave_period": [4.0 for _ in range(24)],
        "wave_direction": [90.0 for _ in range(24)]
    }

    activities = compute_24h_activity(
        lat=lat,
        lon=lon,
        target_date=test_date,
        solunar_data=solunar,
        weather_hourly=mock_weather_hourly,
        marine_hourly=mock_marine_hourly,
        tz_offset_hours=1.0
    )

    assert len(activities) == 24
    for h, a in enumerate(activities):
        assert 0 <= a.score <= 100
        assert a.rating in ["Molto bassa", "Bassa", "Media", "Buona", "Eccellente"]
        assert a.hour == h
        assert a.wave_height == round(0.5 + (h * 0.05), 2)
        assert a.wave_period == 4.0
        assert a.wave_direction == 90.0
