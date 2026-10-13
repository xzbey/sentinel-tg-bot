from services.geocoder import loc_to_coords
from services.image_sentinel import get_sentinel_image
from services.search_sentinel import search_sentinel

from sentinelhub import BBox, CRS
from datetime import datetime

def search(location, delta=0.1, time_interval=("2023-01-01", datetime.now().strftime("%Y-%m-%d"))):
    place = loc_to_coords(location, delta=delta)

    bbox = BBox(bbox=place["coords"], crs=CRS.WGS84)

    metadata = search_sentinel(bbox, time_interval=time_interval)

    image_data = get_sentinel_image(metadata["datetime"], bbox)

    return {"address": place["address"], 
            "coords": place["coords"], 
            "metadata": metadata, 
            "image": image_data["image"],
            "resolution": image_data["resolution"],
            "size": image_data["size"]}