import time
from typing import List, Dict, Any, Optional, Tuple
import httpx
from app.models.schemas import SpotSearchItem, ReverseGeocodeResult, AutoLocationResponse


# In-memory cache: query -> (timestamp, List[SpotSearchItem])
_GEOCODE_CACHE: Dict[str, Tuple[float, List[SpotSearchItem]]] = {}
_REVERSE_GEOCODE_CACHE: Dict[Tuple[float, float], Tuple[float, ReverseGeocodeResult]] = {}
_AUTO_LOCATION_CACHE: Dict[str, Tuple[float, AutoLocationResponse]] = {}
CACHE_TTL_SECONDS = 86400  # 24 hours


async def search_spots(query: str, limit: int = 6) -> List[SpotSearchItem]:
    q_clean = query.strip().lower()
    now = time.time()

    # Check cache
    if q_clean in _GEOCODE_CACHE:
        ts, items = _GEOCODE_CACHE[q_clean]
        if now - ts < CACHE_TTL_SECONDS:
            return items

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
                _GEOCODE_CACHE[q_clean] = (now, results)
    except Exception:
        pass

    return results


async def reverse_geocode(lat: float, lon: float) -> ReverseGeocodeResult:
    cache_key = (round(lat, 3), round(lon, 3))
    now = time.time()

    if cache_key in _REVERSE_GEOCODE_CACHE:
        ts, cached_item = _REVERSE_GEOCODE_CACHE[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return cached_item

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
                _REVERSE_GEOCODE_CACHE[cache_key] = (now, result)
                return result
    except Exception:
        pass

    return default_result


async def get_auto_location(client_ip: Optional[str] = None) -> AutoLocationResponse:
    """
    Geolocates client based on IP with in-memory caching and safe coastal fallback.
    """
    now = time.time()
    cache_key = client_ip.strip() if client_ip and client_ip.strip() else "auto_caller"

    # Check cache
    if cache_key in _AUTO_LOCATION_CACHE:
        ts, cached_loc = _AUTO_LOCATION_CACHE[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return cached_loc

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
                            _AUTO_LOCATION_CACHE[cache_key] = (now, result)
                            return result
                except Exception:
                    continue
    except Exception:
        pass

    _AUTO_LOCATION_CACHE[cache_key] = (now, fallback)
    return fallback


