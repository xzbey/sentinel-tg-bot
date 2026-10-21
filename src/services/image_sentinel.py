from shapely import Geometry
from rasterio.io import MemoryFile

from core.config import sentinel_config
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, bbox_to_dimensions
from sentinelhub.exceptions import DownloadFailedException

from core.error import SearchError, ParseError, sentinelhub_error
from core.scene import Scene
from services.evalscripts import get_evalscript


def bbox_size(geometry: Geometry, resolutions: list[int] = [10, 20, 60]):
    bbox = geometry.bbox
    b = False
    for resolution in resolutions:
        size = bbox_to_dimensions(bbox, resolution=resolution)
        if size[0] <= 2500 and size[1] <= 2500:
            b = True
            break
    if not b:
        raise SearchError("Слишком большой размер изображения")

    return (size, resolution)


def scl_mask(datetime: str, geometry: Geometry, size: tuple[int, int]):
    evalscript = get_evalscript(["dataMask", "SCL"], sampleType="UINT8")
    # resolution 60
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A.define_from("s2l2a_cdse", service_url=sentinel_config().sh_base_url),
                time_interval=(datetime, datetime),
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        geometry=geometry,
        size=size,
        config=sentinel_config(),
    )
    
    try:
        response = request.get_data(decode_data=False)[0]
    except DownloadFailedException as e:
        raise sentinelhub_error(e)

    tiff_bytes = response.content
    with MemoryFile(tiff_bytes) as memfile, memfile.open() as src:
        data_mask, scl = src.read()

    return (scl, data_mask)


def fetch_bands(datetime: str, geometry: Geometry, size: tuple[int, int], band_names: list[str]):    
    request = SentinelHubRequest(
        evalscript=get_evalscript(bands=band_names),
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A.define_from("s2l2a_cdse", service_url=sentinel_config().sh_base_url),
                time_interval=(datetime, datetime),
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        geometry=geometry,
        size=size,
        config=sentinel_config(),
    )

    try:
        response = request.get_data(decode_data=False)[0]
    except DownloadFailedException as e:
        raise sentinelhub_error(e)

    with MemoryFile(response.content) as memfile, memfile.open() as src:
        arr = src.read()
        if src.count != len(band_names):
            raise ParseError("Количество запрошенных каналов не совпадает с количеством полученных")
        
        return {"bands" : {band_names[i] : arr[i] for i in range(len(band_names))}, 
                "crs" : src.crs, 
                "transform" : src.transform}

def fetch_scene(datetime: str, geometry: Geometry, metadata: dict, address: str, coords: tuple, band_names: list[str]) -> Scene:
    size, resolution = bbox_size(geometry)

    fetched = fetch_bands(datetime, geometry, size, band_names)

    return Scene(bands=fetched["bands"], 
                 geometry=geometry,
                 size=size,
                 resolution=resolution,
                 date=datetime,
                 crs=fetched["crs"],
                 transform=fetched["transform"],
                 metadata=metadata,
                 address=address,
                 coords=coords)

def fix_bands(scene: Scene, band_names: list[str]):
    bands = scene.missing(band_names)
    if not bands:
        return

    fetched = fetch_bands(scene.date, scene.geometry, scene.size, bands)
    if fetched["crs"] == scene.crs and fetched["transform"] == scene.transform:
        for band, array in fetched["bands"].items():
            scene.add(band, array)
    else:
        raise ParseError("CRS/Transform на найденный снимок для дополнительных каналов не совпадают")

