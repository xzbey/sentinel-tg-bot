from shapely import box

from services.geocoder import coords_to_bbox, loc_to_coords
from services.image_sentinel import get_sentinel_image
from services.search_sentinel import search_sentinel

from core.error import SearchError

from sentinelhub import Geometry, CRS
from datetime import datetime

def search(location: str = None, 
           geometry: tuple[float, float] | Geometry | None = None,
           delta: float = 0.1, 
           time_interval: tuple[str, str] = ("2023-01-01", datetime.now().strftime("%Y-%m-%d"))):
    
    if location is not None:
        place = loc_to_coords(location, delta)
        address = place["address"]
        coords = place["coords"]
        sh_geometry = Geometry(box(*coords), crs=CRS.WGS84)

    elif type(geometry) == tuple:
        lon, lat = geometry
        address = f"Точка из файла ({lon:.5f}, {lat:.5f})"
        coords = coords_to_bbox(*geometry, delta)
        sh_geometry = Geometry(box(*coords), crs=CRS.WGS84)

    elif type(geometry) == Geometry:
        address = "Полигон из файла"
        coords = tuple(geometry.bbox)
        sh_geometry = geometry

    else:
        raise SearchError("Не задана локация для поиска")
        
    metadata = search_sentinel(sh_geometry, time_interval)

    image_data = get_sentinel_image(metadata["datetime"], sh_geometry)

    return {
        "address": address, 
        "coords": coords, 
        "metadata": metadata, 
        "tiff": image_data["tiff"],
        "preview": image_data["preview"],
        "resolution": image_data["resolution"],
        "size": image_data["size"]
        }