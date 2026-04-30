from config import sentinel_config
from sentinelhub import SentinelHubCatalog, DataCollection #pip install sentinelhub
from sentinelhub.exceptions import DownloadFailedException
from itertools import islice

def search_sentinel(bbox, time_interval):

    catalog = SentinelHubCatalog(config=sentinel_config())

    try:
        search_catalog = list(islice(catalog.search(
            DataCollection.SENTINEL2_L2A,
            bbox=bbox,
            time=time_interval,
            fields={"include": ["id", "properties.datetime", "properties.eo:cloud_cover"], "exclude": []},
        ), 200))
    except DownloadFailedException as e:
        err = str(e)
        if "401" in err or "Unauthorized" in err:
            return {"success": False, "error": "Ошибка авторизации Sentinel Hub (401). Проблема в client_id и client_secret."}
        elif "403" in err or "Forbidden" in err:
            if "expired" in err.lower():
                return {"success": False, "error": "Тестовый период Sentinel Hub истёк (403)."}
            return {"success": False, "error": "Доступ запрещён Sentinel Hub (403). Возможно, закончились токены."}
        return {"success": False, "error": f"Ошибка Sentinel Hub: {e}"}


    if not search_catalog:
        return {"success": False, 
                "error": "Нет данных за период " + time_interval}

    result = min(search_catalog, key=lambda x: x["properties"]["eo:cloud_cover"])
    return {"success": True, 
            "data": {"id": result["id"], "datetime": result["properties"]["datetime"][:10], "cloud_cover": result["properties"]["eo:cloud_cover"]}}