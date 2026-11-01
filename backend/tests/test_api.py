import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_forecast_endpoint_structure():
    # Live integration test for Rimini/Adriatic coast (lat=44.05, lon=12.56)
    response = client.get("/api/v1/forecast?lat=44.05&lon=12.56&date=2026-11-01")
    assert response.status_code == 200
    data = response.json()
    assert "daily_score" in data
    assert "daily_rating" in data
    assert "hourly_activity" in data
    assert len(data["hourly_activity"]) == 24
    assert "solunar" in data
    assert "weather_current" in data


def test_forecast_summary_endpoint():
    response = client.get("/api/v1/forecast/summary?lat=44.05&lon=12.56&days=7")
    assert response.status_code == 200
    data = response.json()
    assert "days" in data
    assert len(data["days"]) >= 7


def test_search_endpoint():
    response = client.get("/api/v1/search?q=Venezia")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "latitude" in data[0]
        assert "longitude" in data[0]


def test_reverse_geocode_endpoint():
    response = client.get("/api/v1/reverse-geocode?lat=44.407&lon=8.927")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "latitude" in data
    assert "longitude" in data
    assert "display_name" in data


def test_auto_location_endpoint():
    response = client.get("/api/v1/location/auto")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "latitude" in data
    assert "longitude" in data
    assert "display_name" in data
    assert isinstance(data["latitude"], float)
    assert isinstance(data["longitude"], float)


def test_forecast_and_summary_consistency():
    lat = 44.05
    lon = 12.56
    summary_resp = client.get(f"/api/v1/forecast/summary?lat={lat}&lon={lon}&days=7")
    assert summary_resp.status_code == 200
    summary_days = summary_resp.json()["days"]
    assert len(summary_days) > 0
    target_day = summary_days[0]
    target_date = target_day["date"]

    forecast_resp = client.get(f"/api/v1/forecast?lat={lat}&lon={lon}&date={target_date}")
    assert forecast_resp.status_code == 200
    forecast_data = forecast_resp.json()

    assert forecast_data["daily_score"] == target_day["score"]
    assert forecast_data["daily_rating"] == target_day["rating"]



