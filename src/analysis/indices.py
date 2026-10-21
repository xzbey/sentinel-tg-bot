from numpy import isfinite, ndarray, nan, errstate

from core.scene import Scene
from core.error import IndicesError

indices = {
    "NDVI": ["B08", "B04"],
    "MNDWI": ["B03", "B11"],
    "NDWI": ["B03", "B08"],
    "NBR": ["B08", "B12"],
    "NDBI": ["B11", "B08"]
}

def compute_index(scene: Scene, name: str) -> ndarray:
    if name not in indices:
        raise IndicesError(f"Индекса {name} не существует")

    a, b = [scene.bands[band] for band in indices[name]]

    with errstate(divide="ignore", invalid="ignore"):
        result = (a - b) / (a + b)
        
    result[~isfinite(result)] = nan
    result[scene.bands["dataMask"] == 0] = nan

    return result
