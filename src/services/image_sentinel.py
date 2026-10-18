from io import BytesIO

import numpy as np
from shapely import Geometry
from rasterio.io import MemoryFile

from core.config import sentinel_config
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, bbox_to_dimensions
from sentinelhub.exceptions import DownloadFailedException
from PIL import Image

from core.error import SearchError, sentinelhub_error
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


def get_sentinel_image(datetime: str, geometry: Geometry):
    size, resolution = bbox_size(geometry)
    
    evalscript = get_evalscript(["B04", "B03", "B02", "dataMask"])

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
        arr = np.moveaxis(src.read(), 0, -1)
    preview = (np.clip(arr[:, :, :3] * 3.0, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(preview)
    img.thumbnail((1280, 1280))

    preview_buf = BytesIO()
    img.save(preview_buf, format="JPEG", quality=85)
    preview_buf.seek(0)

    return {"tiff": tiff_bytes,
            "preview": preview_buf, 
            "resolution": resolution, 
            "size": size}