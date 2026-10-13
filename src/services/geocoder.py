from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import math

from core.error import SearchError

geolocator = Nominatim(user_agent="sentinel-tg-bot", timeout=10)

def loc_to_coords(location, delta = 0.05):
    try:
        loc = geolocator.geocode(location)

    except GeocoderTimedOut:
        raise SearchError("Сервер не отвечает")
    except GeocoderUnavailable:
        raise SearchError("Сервер недоступен")

    if not loc:
        raise SearchError("Адрес не найден")
    
    delta_lon = delta / math.cos(math.radians(loc.latitude))
    return {"address": loc.address, 
            "coords": (
                loc.longitude - delta_lon, 
                loc.latitude - delta, 
                loc.longitude + delta_lon,
                loc.latitude + delta)
            }