from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import math

from core.error import SearchError

def coords_to_bbox(lon: float, lat: float, delta: float = 0.05) -> tuple[float]:
    delta_lon = delta / math.cos(math.radians(lat))
    return (
        lon - delta_lon,
        lat - delta,
        lon + delta_lon,
        lat + delta
    )

def loc_to_coords(location: str, delta: float = 0.05) -> dict:
    geolocator = Nominatim(user_agent="sentinel-tg-bot", timeout=10)
    try:
        loc = geolocator.geocode(location)
    except GeocoderTimedOut:
        raise SearchError("Сервер не отвечает")
    except GeocoderUnavailable:
        raise SearchError("Сервер недоступен")

    if not loc:
        raise SearchError("Адрес не найден")
    
    return {
        "address": loc.address,
        "coords": coords_to_bbox(loc.longitude, loc.latitude, delta)
        }