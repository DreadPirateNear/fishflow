import time
import asyncio
import logging
from collections import OrderedDict
from typing import List, Dict, Any, Optional, Tuple
import httpx
from app.models.schemas import SpotSearchItem, ReverseGeocodeResult, AutoLocationResponse

logger = logging.getLogger(__name__)


class BoundedLRUCache:
    def __init__(self, max_size: int = 500, ttl_seconds: float = 86400.0):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._data: OrderedDict[Any, Tuple[float, Any]] = OrderedDict()
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get(self, key: Any) -> Optional[Any]:
        async with self._get_lock():
            if key not in self._data:
                return None
            ts, val = self._data[key]
            if time.time() - ts > self.ttl_seconds:
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return val

    async def set(self, key: Any, val: Any) -> None:
        async with self._get_lock():
            now = time.time()
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = (now, val)
            while len(self._data) > self.max_size:
                self._data.popitem(last=False)


_GEOCODE_CACHE = BoundedLRUCache(max_size=500, ttl_seconds=86400.0)
_REVERSE_GEOCODE_CACHE = BoundedLRUCache(max_size=500, ttl_seconds=86400.0)
_AUTO_LOCATION_CACHE = BoundedLRUCache(max_size=200, ttl_seconds=86400.0)

_NOMINATIM_SEMAPHORE: Optional[asyncio.Semaphore] = None


def _get_nominatim_semaphore() -> asyncio.Semaphore:
    global _NOMINATIM_SEMAPHORE
    if _NOMINATIM_SEMAPHORE is None:
        _NOMINATIM_SEMAPHORE = asyncio.Semaphore(1)
    return _NOMINATIM_SEMAPHORE


async def search_spots(query: str, limit: int = 6) -> List[SpotSearchItem]:
    q_clean = query.strip().lower()

    cached = await _GEOCODE_CACHE.get(q_clean)
    if cached is not None:
        return cached

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": limit
    }
    headers = {
        "User-Agent": "FishFlow/1.0 (Homelab Fishing App; https://github.com/fishflow)"
    }

    results: List[SpotSearchItem] = []
    try:
        async with _get_nominatim_semaphore():
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    raw_data = response.json()
                    for item in raw_data:
                        cat = item.get("category", "")
                        typ = item.get("type", "")
                        is_marine = cat in ["water", "natural", "leisure"] or typ in [
                            "bay", "sea", "harbour", "beach", "coastline", "marina", "water"
                        ]
                        results.append(SpotSearchItem(
                            name=item.get("name") or item.get("display_name", "").split(",")[0],
                            display_name=item.get("display_name", ""),
                            latitude=float(item.get("lat")),
                            longitude=float(item.get("lon")),
                            category=cat,
                            type=typ,
                            is_marine=is_marine
                        ))
                    await _GEOCODE_CACHE.set(q_clean, results)
    except Exception as exc:
        logger.warning("Location search failed for query '%s': %s", query, exc)

    return results


async def reverse_geocode(lat: float, lon: float) -> ReverseGeocodeResult:
    cache_key = (round(lat, 3), round(lon, 3))

    cached = await _REVERSE_GEOCODE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    default_name = f"Spot ({lat:.3f}, {lon:.3f})"
    default_result = ReverseGeocodeResult(
        name=default_name,
        display_name=f"Coordinate: {lat:.4f}, {lon:.4f}",
        latitude=lat,
        longitude=lon,
        is_marine=True
    )

    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "zoom": 14,
        "addressdetails": 1
    }
    headers = {
        "User-Agent": "FishFlow/1.0 (Homelab Fishing App; https://github.com/fishflow)"
    }

    try:
        async with _get_nominatim_semaphore():
            async with httpx.AsyncClient(timeout=4.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    address = data.get("address", {})
                    name = (
                        data.get("name")
                        or address.get("locality")
                        or address.get("coastal")
                        or address.get("town")
                        or address.get("village")
                        or address.get("city")
                        or address.get("municipality")
                        or address.get("suburb")
                        or address.get("county")
                        or default_name
                    )
                    display_name = data.get("display_name") or default_result.display_name
                    cat = data.get("category", "")
                    typ = data.get("type", "")
                    is_marine = cat in ["water", "natural", "leisure"] or typ in [
                        "bay", "sea", "harbour", "beach", "coastline", "marina", "water", "ocean"
                    ]

                    result = ReverseGeocodeResult(
                        name=name,
                        display_name=display_name,
                        latitude=lat,
                        longitude=lon,
                        is_marine=is_marine
                    )
                    await _REVERSE_GEOCODE_CACHE.set(cache_key, result)
                    return result
    except Exception as exc:
        logger.warning("Reverse geocoding failed for (%s, %s): %s", lat, lon, exc)

    return default_result


async def get_auto_location(client_ip: Optional[str] = None) -> AutoLocationResponse:
    """
    Geolocates client based on IP with in-memory caching and safe coastal fallback.
    """
    cache_key = client_ip.strip() if client_ip and client_ip.strip() else "auto_caller"

    cached = await _AUTO_LOCATION_CACHE.get(cache_key)
    if cached is not None:
        return cached

    fallback = AutoLocationResponse(
        name="Porto Antico di Genova",
        display_name="Porto Antico, Genova, Liguria, Italia",
        latitude=44.4093,
        longitude=8.9248,
        is_marine=True
    )

    is_private = False
    if client_ip:
        ip = client_ip.strip()
        if (ip.startswith("127.") or ip.startswith("10.") or 
            ip.startswith("192.168.") or ip.startswith("172.") or 
            ip == "::1" or ip == "localhost"):
            is_private = True
    else:
        is_private = True

    endpoints = []
    if is_private:
        endpoints.append("https://ipwho.is/")
        endpoints.append("https://ipapi.co/json/")
        endpoints.append("https://freeipapi.com/api/json")
    else:
        endpoints.append(f"https://ipwho.is/{client_ip.strip()}")
        endpoints.append(f"https://ipapi.co/{client_ip.strip()}/json/")
        endpoints.append(f"https://freeipapi.com/api/json/{client_ip.strip()}")

    headers = {
        "User-Agent": "FishFlow/1.0 (Homelab Fishing App; https://github.com/fishflow)"
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            for url in endpoints:
                try:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        lat = data.get("latitude")
                        lon = data.get("longitude")
                        city = data.get("city") or data.get("cityName") or data.get("region")
                        country = data.get("country") or data.get("countryName")
                        
                        if lat is not None and lon is not None:
                            lat_f = float(lat)
                            lon_f = float(lon)
                            name = city or "La tua posizione"
                            display_name = f"{city}, {country}" if city and country else name
                            result = AutoLocationResponse(
                                name=name,
                                display_name=display_name,
                                latitude=round(lat_f, 4),
                                longitude=round(lon_f, 4),
                                is_marine=True
                            )
                            await _AUTO_LOCATION_CACHE.set(cache_key, result)
                            return result
                except Exception as exc:
                    logger.debug("IP endpoint %s failed: %s", url, exc)
                    continue
    except Exception as exc:
        logger.warning("Auto-location detection failed: %s", exc)

    await _AUTO_LOCATION_CACHE.set(cache_key, fallback)
    return fallback
