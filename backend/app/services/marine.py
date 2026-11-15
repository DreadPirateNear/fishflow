from typing import Dict, Any, Optional, Tuple
import httpx
from app.models.schemas import MarineData


async def fetch_marine_forecast(
    lat: float,
    lon: float,
    forecast_days: int = 7
) -> Tuple[Optional[MarineData], Dict[str, Any]]:
    """
    Fetches marine forecast from Open-Meteo Marine API.
    Returns (summary_marine_data, hourly_marine_dict).
    If coordinates are inland or no marine data is available, returns (None, {}).
    """
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "wave_height",
            "wave_direction",
            "wave_period",
            "sea_surface_temperature",
        ],
        "forecast_days": forecast_days,
        "timezone": "auto"
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                return None, {}
            data = response.json()
            hourly = data.get("hourly", {})
            wave_heights = hourly.get("wave_height", [])
            wave_periods = hourly.get("wave_period", [])
            wave_directions = hourly.get("wave_direction", [])
            sea_temps = hourly.get("sea_surface_temperature", [])

            # Check if there is valid non-null data for coastal/marine areas
            valid_wave = next((v for v in wave_heights if v is not None), None)
            valid_temp = next((v for v in sea_temps if v is not None), None)
            valid_period = next((v for v in wave_periods if v is not None), None)
            valid_direction = next((v for v in wave_directions if v is not None), None)

            if valid_wave is None and valid_temp is None:
                return None, {}

            marine_summary = MarineData(
                sea_surface_temperature=round(valid_temp, 1) if valid_temp is not None else None,
                wave_height=round(valid_wave, 2) if valid_wave is not None else None,
                wave_period=round(valid_period, 1) if valid_period is not None else None,
                wave_direction=round(valid_direction, 0) if valid_direction is not None else None,
                is_marine=True
            )
            return marine_summary, hourly
    except Exception:
        # Graceful fallback for inland locations or network issues
        return None, {}
