from io import BytesIO

from numpy import ndarray
from rasterio.features import shapes
from geopandas import GeoDataFrame
from rasterio.crs import CRS
from affine import Affine

from analysis.class_render import CLASS_NAMES
from core.error import VectorizationError

import warnings
warnings.filterwarnings("ignore", message="Setting the shape on a NumPy array", category=DeprecationWarning)

def vectorization(array: ndarray, transform: Affine, crs: CRS) -> BytesIO:
    mask = array != 0

    result = (
        {"properties": {"fid": i + 1, "class_type": int(v), "class_name": CLASS_NAMES[v]}, "geometry": s}
        for i, (s, v) in enumerate(shapes(array, mask=mask, transform=transform, connectivity=4))
    )
    gpf = GeoDataFrame.from_features(list(result),crs=crs)

    metric_gpf = gpf.to_crs(gpf.estimate_utm_crs())
    gpf["area_km2"] = (metric_gpf.area / 1000000).round(4)

    buf = BytesIO()
    gpf.to_file(buf, driver="GPKG")

    size = len(buf.getvalue()) / (1024 * 1024)
    if size > 50:
        raise VectorizationError("Файл слишком большой!")

    buf.seek(0)
    return buf