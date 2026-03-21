from geo import loc_to_coords, search_sentinel, get_sentinel_image
from sentinelhub import BBox, CRS
from datetime import datetime

# github.com/xzbey | tg/xzbey

def search(location, delta=0.1, time_interval=("2023-01-01", datetime.now().strftime("%Y-%m-%d"))):
    # --------------------------- geocoder.py
    geocoder_data = loc_to_coords(location, delta=delta)

    if geocoder_data["success"]:
        coords = geocoder_data["coords"]
        address = geocoder_data["address"]
        #print(f"------- geocoder log -------\n {address}\n {coords}\n")
    else: 
        return {"success": False, "error": geocoder_data["error"]}
    # --------------------------- geocoder.py

    bbox = BBox(bbox=coords, crs=CRS.WGS84)

    # --------------------------- search_sentinel.py
    search_sentinel_data = search_sentinel(coords, bbox, time_interval=time_interval)

    if search_sentinel_data["success"]:
        metadata = search_sentinel_data["data"]
        #print(f"------- search_sentinel log -------]\n {metadata}\n")
    else:
        return {"success": False, "error": search_sentinel_data["error"]}
    # --------------------------- search_sentinel.py

    # --------------------------- image_sentinel.py
    #print("------- image_sentinel log -------")
    image_data = get_sentinel_image(metadata["datetime"], bbox)
    if not image_data["success"]:
        return {"success": False, "error": image_data["error"]}
    # --------------------------- image_sentinel.py

    return {"success": True, 
            "data": {"address": address, 
                     "coords": coords, 
                     "metadata": metadata, 
                     "image": image_data["data"],
                     "resolution": image_data["resolution"],
                     "size": image_data["size"]}}