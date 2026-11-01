from typing import Dict, Any, Optional
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
