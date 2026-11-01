from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field


class SolunarWindow(BaseModel):
    start: str = Field(description="Start time HH:MM")
    end: str = Field(description="End time HH:MM")
    window_type: str = Field(description="'major' or 'minor'")
    description: str = Field(description="E.g. Moon Zenith or Moonrise")


class SolunarData(BaseModel):
    moon_phase_name: str
    moon_illumination: float = Field(ge=0.0, le=1.0)
    moon_distance_km: float = 384400.0
    moon_age_days: float = 0.0
    is_perigee: bool = False
    moonrise: Optional[str] = None
    moonset: Optional[str] = None
    moon_transit: Optional[str] = None
    moon_underfoot: Optional[str] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    solar_noon: Optional[str] = None
    civil_dawn: Optional[str] = None
    civil_dusk: Optional[str] = None
    day_duration_minutes: int = 720
    night_duration_minutes: int = 720
    major_windows: List[SolunarWindow] = []
    minor_windows: List[SolunarWindow] = []


class MarineData(BaseModel):
    sea_surface_temperature: Optional[float] = None
    wave_height: Optional[float] = None
    wave_period: Optional[float] = None
    wave_direction: Optional[float] = None
    is_marine: bool = False


class WeatherData(BaseModel):
    temperature_2m: float
    apparent_temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    surface_pressure: float
    pressure_trend_3h: float
    wind_speed_knots: float
    wind_direction: float
    wind_gusts_knots: Optional[float] = None
    cloud_cover: float
    weather_code: int
    weather_description: str
    precipitation: float
    precipitation_probability: Optional[float] = None
    uv_index: Optional[float] = None
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None


class HourlyActivity(BaseModel):
    time: str = Field(description="ISO timestamp YYYY-MM-DDTHH:00")
    hour: int = Field(ge=0, le=23)
    score: int = Field(ge=0, le=100, description="Normalized fish activity score (0-100)")
    rating: str = Field(description="'Molto bassa', 'Bassa', 'Media', 'Buona', 'Eccellente'")
    solunar_score: int
    barometric_score: int
    light_score: int
    weather_score: int
    temperature: float
    apparent_temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    pressure: float
    pressure_trend_3h: float
    wind_knots: float
    wind_direction: float
    wind_gusts_knots: Optional[float] = None
    precipitation: Optional[float] = 0.0
    precipitation_probability: Optional[float] = 0.0
    uv_index: Optional[float] = None
    weather_code: int
    wave_height: Optional[float] = None
    is_major_window: bool = False
    is_minor_window: bool = False


class ForecastResponse(BaseModel):
    date: str
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    daily_score: int = Field(ge=0, le=100)
    daily_rating: str
    hourly_activity: List[HourlyActivity]
    solunar: SolunarData
    weather_current: WeatherData
    marine: Optional[MarineData] = None


class DaySummary(BaseModel):
    date: str
    day_name: str
    day_number: int
    month_name: str
    score: int = Field(ge=0, le=100)
    rating: str
    moon_phase_name: str
    moon_phase_icon: str
    temp_min: float
    temp_max: float
    weather_code: int
    wind_knots_max: float


class ForecastSummaryResponse(BaseModel):
    latitude: float
    longitude: float
    days: List[DaySummary]


class SpotSearchItem(BaseModel):
    name: str
    display_name: str
    latitude: float
    longitude: float
    category: str
    type: str
    is_marine: bool = False


class ReverseGeocodeResult(BaseModel):
    name: str
    display_name: str
    latitude: float
    longitude: float
    is_marine: bool = False


class AutoLocationResponse(BaseModel):
    name: str
    display_name: str
    latitude: float
    longitude: float
    is_marine: bool = True


