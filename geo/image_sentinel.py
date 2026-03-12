from .config import config
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, BBox, CRS, bbox_to_dimensions
from PIL import ImageEnhance, Image

def get_sentinel_image(datetime, bbox):
    b = False
    for resolution in [10, 20, 60]:
        size = bbox_to_dimensions(bbox, resolution=resolution)
        if size[0] <= 2500 and size[1] <= 2500:
            b = True
            break
    if not b:
        return {"success": False, 
                "error": "Слишком большой размер изображения"}

    #print(f"Image shape at {resolution} m resolution: {size} pixels")
    
    evalscript_true_color = """
        //VERSION=3

        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04"]
                }],
                output: {
                    bands: 3
                }
            };
        }

        function evaluatePixel(sample) {
            return [sample.B04, sample.B03, sample.B02];
        }
    """

    request_true_color = SentinelHubRequest(
        evalscript=evalscript_true_color,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(datetime, datetime),
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        size=size,
        config=config,
    )

    true_color_imgs = request_true_color.get_data()

    img = Image.fromarray(true_color_imgs[0])
    enhanced = ImageEnhance.Brightness(img).enhance(3)
    #enhanced.show()

    return {"success": True, "data": enhanced, "resolution": resolution, "size": size}