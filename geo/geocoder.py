from geopy.geocoders import Nominatim #pip install geopy
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import math

geolocator = Nominatim(user_agent="sentinel-tg-bot", timeout=10)

def loc_to_coords(location, delta = 0.05):
    try:
        loc = geolocator.geocode(location)

        if loc:
            delta_lon = delta / math.cos(math.radians(loc.latitude))
            return {"success": True,
                    "address": loc.address, "coords": (
                        loc.longitude - delta_lon, 
                        loc.latitude - delta, 
                        loc.longitude + delta_lon,
                        loc.latitude + delta)}
                        
        else:
            return {"success": False,
                    "error": "Адрес не найден"}

    except GeocoderTimedOut:
        return {"success": False,
                "error": "Сервер не отвечает"}
    except GeocoderUnavailable:
        return {"success": False,
                "error": "Сервер недоступен"}
    except Exception as e:
        return {"success": False,
                "error": e}