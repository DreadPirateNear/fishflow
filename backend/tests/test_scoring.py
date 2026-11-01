from datetime import date
from app.services.scoring import (
    compute_barometric_score,
    compute_light_score,
    compute_wind_weather_score,
    get_rating_label,
    compute_24h_activity
)
from app.services.solunar import calculate_solunar_data


def test_barometric_scoring():
    # Ideal slow drop: high score
    assert compute_barometric_score(-1.5) == 95
    # Stable: moderate
    assert compute_barometric_score(0.0) == 65
    # Rapid rise: severe penalty
    assert compute_barometric_score(3.0) == 20


def test_rating_labels():
    assert get_rating_label(85) == "Eccellente"
    assert get_rating_label(60) == "Buona"
    assert get_rating_label(40) == "Media"
    assert get_rating_label(25) == "Bassa"
    assert get_rating_label(15) == "Molto bassa"


def test_24h_activity_computation():
    lat = 44.05
    lon = 12.56
    test_date = date(2026, 11, 1)
    solunar = calculate_solunar_data(lat, lon, test_date)

    mock_weather_hourly = {
        "time": [f"2026-11-01T{h:02d}:00" for h in range(24)],
        "surface_pressure": [1013.0 - (h * 0.1) for h in range(24)],
        "temperature_2m": [15.0 + (h * 0.2) for h in range(24)],
        "wind_speed_10m": [10.0 for _ in range(24)],
        "wind_direction_10m": [180.0 for _ in range(24)],
        "cloud_cover": [40.0 for _ in range(24)],
        "weather_code": [1 for _ in range(24)]
    }

    activities = compute_24h_activity(
        lat=lat,
        lon=lon,
        target_date=test_date,
        solunar_data=solunar,
        weather_hourly=mock_weather_hourly,
        marine_wave_height=0.4
    )

    assert len(activities) == 24
    for a in activities:
        assert 0 <= a.score <= 100
        assert a.rating in ["Molto bassa", "Bassa", "Media", "Buona", "Eccellente"]
        assert a.hour in range(24)


def test_2026_11_01_calibrated_scoring():
    lat = 38.1157
    lon = 13.3615
    target_date = date(2026, 11, 1)
    solunar = calculate_solunar_data(lat, lon, target_date)

    mock_weather = {
        "time": [f"2026-11-01T{h:02d}:00" for h in range(24)],
        "surface_pressure": [1013.25 for _ in range(24)],
        "temperature_2m": [18.0 for _ in range(24)],
        "wind_speed_10m": [8.0 for _ in range(24)],
        "wind_direction_10m": [300.0 for _ in range(24)],
        "cloud_cover": [40.0 for _ in range(24)],
        "weather_code": [2 for _ in range(24)]
    }

    activities = compute_24h_activity(
        lat=lat,
        lon=lon,
        target_date=target_date,
        solunar_data=solunar,
        weather_hourly=mock_weather
    )

    scores = [h.score for h in activities]
    daily_score = round(sum(scores) / len(scores))
    assert 15 <= daily_score <= 22, f"Expected daily score between 15 and 22, got {daily_score}"
    assert get_rating_label(daily_score) == "Molto bassa"

