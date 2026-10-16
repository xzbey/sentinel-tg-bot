from shapely import Geometry

from core.config import sentinel_config
from sentinelhub import SentinelHubCatalog, DataCollection
from sentinelhub.exceptions import DownloadFailedException
from itertools import islice

from core.error import SearchError, sentinelhub_error

def search_sentinel(geometry: Geometry, time_interval: tuple[str, str]):
    catalog = SentinelHubCatalog(config=sentinel_config())

    try:
        search_catalog = list(islice(catalog.search(
            DataCollection.SENTINEL2_L2A,
            geometry=geometry,
            time=time_interval,
            fields={"include": ["id", "properties.datetime", "properties.eo:cloud_cover"], "exclude": []},
        ), 200))

    except DownloadFailedException as e:
        raise sentinelhub_error(e)

    if not search_catalog:
        raise SearchError(f"Нет данных за период {time_interval[0]} - {time_interval[1]}")

    result = min(search_catalog, key=lambda x: x["properties"]["eo:cloud_cover"])
    return {"id": result["id"], 
            "datetime": result["properties"]["datetime"][:10], 
            "cloud_cover": result["properties"]["eo:cloud_cover"]}