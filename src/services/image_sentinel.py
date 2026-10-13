from core.config import sentinel_config
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, BBox, CRS, bbox_to_dimensions
from PIL import ImageEnhance, Image

from core.error import SearchError
from services.evalscripts import get_evalscript

def get_sentinel_image(datetime, bbox):
    b = False
    for resolution in [10, 20, 60]:
        size = bbox_to_dimensions(bbox, resolution=resolution)
        if size[0] <= 2500 and size[1] <= 2500:
            b = True
            break
    if not b:
        raise SearchError("Слишком большой размер изображения")
    
    evalscript_true_color = get_evalscript(["B04", "B03", "B02"])

    request_true_color = SentinelHubRequest(
        evalscript=evalscript_true_color,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A.define_from("s2l2a_cdse", service_url=sentinel_config().sh_base_url),
                time_interval=(datetime, datetime),
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        size=size,
        config=sentinel_config(),
    )

    true_color_imgs = request_true_color.get_data()

    img = Image.fromarray(true_color_imgs[0])
    enhanced = ImageEnhance.Brightness(img).enhance(3)
    #enhanced.show()

    return {"image": enhanced, 
            "resolution": resolution, 
            "size": size}