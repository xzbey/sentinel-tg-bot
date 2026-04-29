from config import sentinel_config
from sentinelhub import SentinelHubCatalog, DataCollection #pip install sentinelhub
from itertools import islice

def search_sentinel(bbox, time_interval):

    catalog = SentinelHubCatalog(config=sentinel_config())

    search_catalog = list(islice(catalog.search(
        DataCollection.SENTINEL2_L2A,
        bbox=bbox,
        time=time_interval,
        fields={"include": ["id", "properties.datetime", "properties.eo:cloud_cover"], "exclude": []},
    ), 200))

    if not search_catalog:
        return {"success": False, 
                "error": "Нет данных за период " + time_interval}

    result = min(search_catalog, key=lambda x: x["properties"]["eo:cloud_cover"])
    return {"success": True, 
            "data": {"id": result["id"], "datetime": result["properties"]["datetime"][:10], "cloud_cover": result["properties"]["eo:cloud_cover"]}}