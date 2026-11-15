from datetime import date, timedelta
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import MarineData, SpotSearchItem, ReverseGeocodeResult, AutoLocationResponse

client = TestClient(app)

TODAY = date.today()

MOCK_WEATHER = {
    "latitude": 44.05,
    "longitude": 12.56,
    "utc_offset_seconds": 3600,
    "timezone": "Europe/Rome",
    "hourly": {
        "time": [f"{TODAY.isoformat()}T{h:02d}:00" for h in range(24)],
        "surface_pressure": [1013.25 - (h * 0.05) for h in range(24)],
        "temperature_2m": [15.0 + (h * 0.2) for h in range(24)],
        "apparent_temperature": [15.0 + (h * 0.2) for h in range(24)],
        "relative_humidity_2m": [65.0 for _ in range(24)],
        "precipitation_probability": [0.0 for _ in range(24)],
        "precipitation": [0.0 for _ in range(24)],
        "weather_code": [1 for _ in range(24)],
        "cloud_cover": [30.0 for _ in range(24)],
        "wind_speed_10m": [8.0 for _ in range(24)],
        "wind_direction_10m": [180.0 for _ in range(24)],
        "wind_gusts_10m": [12.0 for _ in range(24)],
        "uv_index": [3.0 for _ in range(24)],
    },
    "daily": {
        "time": [(TODAY + timedelta(days=d)).isoformat() for d in range(7)],
        "weather_code": [1] * 7,
        "temperature_2m_max": [20.0] * 7,
        "temperature_2m_min": [12.0] * 7,
        "wind_speed_10m_max": [10.0] * 7,
        "sunrise": [f"{(TODAY + timedelta(days=d)).isoformat()}T06:30" for d in range(7)],
        "sunset": [f"{(TODAY + timedelta(days=d)).isoformat()}T18:30" for d in range(7)]
    }
}

MOCK_MARINE_DATA = MarineData(
    sea_surface_temperature=17.5,
    wave_height=0.6,
    wave_period=4.5,
    wave_direction=110.0,
    is_marine=True
)

MOCK_MARINE_HOURLY = {
    "time": [f"{TODAY.isoformat()}T{h:02d}:00" for h in range(24)],
    "wave_height": [0.5 + (h * 0.02) for h in range(24)],
    "wave_period": [4.5 for _ in range(24)],
    "wave_direction": [110.0 for _ in range(24)]
}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@patch("app.api.routes.fetch_weather_forecast", new_callable=AsyncMock)
@patch("app.api.routes.fetch_marine_forecast", new_callable=AsyncMock)
def test_forecast_endpoint_mocked(mock_marine, mock_weather):
    mock_weather.return_value = MOCK_WEATHER
    mock_marine.return_value = (MOCK_MARINE_DATA, MOCK_MARINE_HOURLY)

    response = client.get(f"/api/v1/forecast?lat=44.05&lon=12.56&date={TODAY.isoformat()}")
    assert response.status_code == 200
    data = response.json()

    assert "daily_score" in data
    assert "daily_rating" in data
    assert "hourly_activity" in data
    assert len(data["hourly_activity"]) == 24
    assert data["hourly_activity"][0]["wave_height"] is not None
    assert "solunar" in data
    assert "weather_current" in data
    assert data["utc_offset_hours"] == 1.0
    assert data["timezone"] == "Europe/Rome"
    assert data["is_offline"] is False


@patch("app.api.routes.fetch_weather_forecast", new_callable=AsyncMock)
@patch("app.api.routes.fetch_marine_forecast", new_callable=AsyncMock)
def test_forecast_offline_resilience(mock_marine, mock_weather):
    # Simulate network failure / 502 prevention
    mock_weather.side_effect = Exception("Open-Meteo connection timed out")
    mock_marine.side_effect = Exception("Marine API connection failed")

    response = client.get(f"/api/v1/forecast?lat=44.05&lon=12.56&date={TODAY.isoformat()}")
    assert response.status_code == 200
    data = response.json()

    assert data["is_offline"] is True
    assert len(data["hourly_activity"]) == 24
    assert data["solunar"]["solar_noon"] is not None
    assert 0 <= data["daily_score"] <= 100


@patch("app.api.routes.fetch_weather_forecast", new_callable=AsyncMock)
def test_forecast_summary_endpoint(mock_weather):
    mock_weather.return_value = MOCK_WEATHER

    response = client.get("/api/v1/forecast/summary?lat=44.05&lon=12.56&days=7")
    assert response.status_code == 200
    data = response.json()
    assert "days" in data
    assert len(data["days"]) >= 7


@patch("app.api.routes.search_spots", new_callable=AsyncMock)
def test_search_endpoint(mock_search):
    mock_search.return_value = [
        SpotSearchItem(
            name="Venezia",
            display_name="Venezia, Veneto, Italia",
            latitude=45.438,
            longitude=12.335,
            category="place",
            type="city",
            is_marine=True
        )
    ]

    response = client.get("/api/v1/search?q=Venezia")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "Venezia"


@patch("app.api.routes.reverse_geocode", new_callable=AsyncMock)
def test_reverse_geocode_endpoint(mock_rev):
    mock_rev.return_value = ReverseGeocodeResult(
        name="Porto Antico",
        display_name="Porto Antico, Genova, Liguria, Italia",
        latitude=44.407,
        longitude=8.927,
        is_marine=True
    )

    response = client.get("/api/v1/reverse-geocode?lat=44.407&lon=8.927")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Porto Antico"
    assert data["is_marine"] is True


@patch("app.api.routes.get_auto_location", new_callable=AsyncMock)
def test_auto_location_endpoint(mock_auto):
    mock_auto.return_value = AutoLocationResponse(
        name="Porto Antico di Genova",
        display_name="Porto Antico, Genova, Liguria, Italia",
        latitude=44.4093,
        longitude=8.9248,
        is_marine=True
    )
    response = client.get("/api/v1/location/auto")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Porto Antico di Genova"
    assert data["latitude"] == 44.4093
    assert data["longitude"] == 8.9248


@patch("app.api.routes.fetch_weather_forecast", new_callable=AsyncMock)
@patch("app.api.routes.fetch_marine_forecast", new_callable=AsyncMock)
def test_forecast_inland_water_detection(mock_marine, mock_weather):
    mock_weather.return_value = MOCK_WEATHER
    mock_marine.return_value = (None, {})

    response = client.get(f"/api/v1/forecast?lat=45.8&lon=9.0&date={TODAY.isoformat()}")
    assert response.status_code == 200
    data = response.json()

    assert data["marine"] is None
    assert len(data["hourly_activity"]) == 24
    assert data["hourly_activity"][0]["wave_height"] is None
    assert data["hourly_activity"][0]["wave_period"] is None
    assert data["hourly_activity"][0]["wave_direction"] is None


def test_spa_index_served():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

