from core.scene import Scene
from core.error import ClassificationError
from numpy import errstate, uint8, ones, select, ndarray, pad
from rasterio.features import sieve
from scipy.ndimage import binary_closing


LIMIT = {"water_min": 0.04, "water_max": 0.16, 
         "built_min": -0.7, "built_max": -0.1, 
         "veg_min": 0.1, "veg_max": 0.4}
DEFAULTS = {"water": 0.1, "built": -0.4, "veg": 0.25}


def parse_def(changing_dict: dict) -> dict:
    result_def = {"water": round(DEFAULTS["water"] + changing_dict["water"], 3), 
                  "built": round(DEFAULTS["built"] + changing_dict["built"], 3), 
                  "veg": round(DEFAULTS["veg"] + changing_dict["veg"], 3)}
    
    if result_def["water"] > LIMIT["water_max"]:
        raise ClassificationError("Максимальный лимит воды достигнут")
    if result_def["water"] < LIMIT["water_min"]:
        raise ClassificationError("Минимальный лимит воды достигнут")

    if result_def["built"] > LIMIT["built_max"]:
        raise ClassificationError("Минимальный лимит застройки достигнут")
    if result_def["built"] < LIMIT["built_min"]:
        raise ClassificationError("Максимальный лимит застройки достигнут")

    if result_def["veg"] > LIMIT["veg_max"]:
        raise ClassificationError("Минимальный лимит растительности достигнут")
    if result_def["veg"] < LIMIT["veg_min"]:
        raise ClassificationError("Максимальный лимит растительности достигнут")
    
    return result_def


def compute_classification(scene: Scene, 
                           changing_dict: dict = {"water": 0.0, "built": 0.0, "veg": 0.0}) -> ndarray:
    
    result_def = parse_def(changing_dict)
    
    b03, b04, b08, b11 = scene.bands["B03"], scene.bands["B04"], scene.bands["B08"], scene.bands["B11"]
    valid = scene.bands["dataMask"] == 1

    with errstate(divide="ignore", invalid="ignore"):
        ndvi  = (b08 - b04) / (b08 + b04)
        mndwi = (b03 - b11) / (b03 + b11)
        ndbi  = (b11 - b08) / (b11 + b08)

    water = (
        (mndwi > -0.1) & 
        (b08 < result_def["water"]) &
        (b11 < 0.05)
    )

    built_raw = (
        ((ndbi - ndvi) > result_def["built"]) &
        (b04 > 0.04)
    )

    built_closed = binary_closing(pad(built_raw, 2, mode="edge"), structure=ones((5, 5)))[2:-2, 2:-2]
    built = sieve(built_closed.astype(uint8), size=6, connectivity=8).astype(bool)

    veg = (
        (ndvi > result_def["veg"]) &
        (b08 > 0.1)
    )

    classes = select([water, built, veg], [1, 2, 3], default=4).astype("uint8")

    clean = sieve(classes, size=4, connectivity=4)
    clean[~valid] = 0

    return clean
