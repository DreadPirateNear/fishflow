from typing import Dict, Any, Optional
from datetime import date, timedelta
import httpx


WMO_DESCRIPTIONS = {
    0: "Sereno",
    1: "Prevalentemente sereno",
    2: "Parzialmente nuvoloso",
    3: "Coperto",
    45: "Nebbia",
    48: "Nebbia con brina",
    51: "Pioviggine leggera",
    53: "Pioviggine moderata",
    55: "Pioviggine densa",
    56: "Pioviggine gelata leggera",
    57: "Pioviggine gelata densa",
    61: "Pioggia leggera",
    63: "Pioggia moderata",
    65: "Pioggia forte",
    66: "Pioggia gelata leggera",
    67: "Pioggia gelata forte",
    71: "Neve leggera",
    73: "Neve moderata",
    75: "Neve forte",
    77: "Granuli di neve",
    80: "Rovesci lievi",
    81: "Rovesci moderati",
    82: "Rovesci violenti",
    85: "Rovesci di neve leggeri",
    86: "Rovesci di neve forti",
    95: "Temporale",
    96: "Temporale con grandine leggera",
    99: "Temporale con grandine forte",
}


def get_weather_description(code: int) -> str:
    return WMO_DESCRIPTIONS.get(code, "Variabile")


def kmh_to_knots(kmh: float) -> float:
    return round(kmh / 1.852, 1)


async def fetch_weather_forecast(
    lat: float,
    lon: float,
    forecast_days: int = 7,
    past_days: int = 1
) -> Dict[str, Any]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "surface_pressure",
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "uv_index",
        ],
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "wind_speed_10m_max",
            "sunrise",
            "sunset"
        ],
        "forecast_days": forecast_days,
        "past_days": past_days,
        "timezone": "auto"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def generate_offline_weather_fallback(lat: float, lon: float, target_date: date) -> Dict[str, Any]:
    """
    Generates neutral offline fallback weather data when external APIs are unreachable.
    Allows local PyEphem solunar predictions to proceed uninterrupted.
    """
    solar_offset_sec = int(round(lon / 15.0) * 3600)
    times = []
    # Generate 48 hours (yesterday + today) for pressure trends
    for d_offset in [-1, 0, 1]:
        d = target_date + timedelta(days=d_offset)
        for h in range(24):
            times.append(f"{d.isoformat()}T{h:02d}:00")

    num_hours = len(times)
    return {
        "latitude": lat,
        "longitude": lon,
        "utc_offset_seconds": solar_offset_sec,
        "timezone": "Offline/LocalSolar",
        "hourly": {
            "time": times,
            "surface_pressure": [1013.25] * num_hours,
            "temperature_2m": [18.0] * num_hours,
            "apparent_temperature": [18.0] * num_hours,
            "relative_humidity_2m": [60.0] * num_hours,
            "precipitation_probability": [0.0] * num_hours,
            "precipitation": [0.0] * num_hours,
            "weather_code": [0] * num_hours,
            "cloud_cover": [30.0] * num_hours,
            "wind_speed_10m": [8.0] * num_hours,
            "wind_direction_10m": [180.0] * num_hours,
            "wind_gusts_10m": [12.0] * num_hours,
            "uv_index": [3.0] * num_hours,
        },
        "daily": {
            "weather_code": [0] * 7,
            "temperature_2m_max": [20.0] * 7,
            "temperature_2m_min": [14.0] * 7,
            "wind_speed_10m_max": [10.0] * 7,
            "sunrise": [f"{(target_date + timedelta(days=i)).isoformat()}T06:30" for i in range(7)],
            "sunset": [f"{(target_date + timedelta(days=i)).isoformat()}T18:30" for i in range(7)]
        }
    }
