from shapely import box

from services.geocoder import coords_to_bbox, loc_to_coords
from services.image_sentinel import bbox_size, scl_mask, fetch_scene
from services.search_sentinel import search_sentinel

from analysis.cloud_cover import cloud_percent

from core.error import SearchError
from core.config import basicBands

from sentinelhub import Geometry, CRS
from datetime import datetime

import logging
import time

logger = logging.getLogger(__name__)

def search(location: str = None, 
           geometry: tuple[float, float] | Geometry | None = None,
           delta: float = 0.1, 
           time_interval: tuple[str, str] = (None, None)):
    if time_interval == (None, None):
        time_interval = ("2023-01-01", datetime.now().strftime("%Y-%m-%d"))
    
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

    # t = time.perf_counter()
    metadata_list = search_sentinel(sh_geometry, time_interval)
    # logger.info("каталог: %.1f с", time.perf_counter() - t)

    size = bbox_size(sh_geometry, resolutions=[60])[0]
    candidates = []
    for metadata in metadata_list:
        # t = time.perf_counter()
        percent = cloud_percent(*scl_mask(datetime=metadata["datetime"], geometry=sh_geometry, size=size))
        # logger.info("SCL %s: %.1f с", metadata["datetime"], time.perf_counter() - t)

        if percent is not None:
            candidates.append((percent, metadata))

    if candidates == []:
        raise SearchError("В зоне нет пикселей с данными ни в одном из снимков")

    percent, metadata = min(candidates, key=lambda x: x[0])
    metadata["cloud_cover"] = round(percent, 2)

    # t = time.perf_counter()
    scene = fetch_scene(datetime=metadata["datetime"],
                        geometry=sh_geometry,
                        metadata=metadata,
                        address=address,
                        coords=coords,
                        band_names=basicBands)
    # logger.info("итоговый запрос каналов: %.1f с", time.perf_counter() - t)

    return scene