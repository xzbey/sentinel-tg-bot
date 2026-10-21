from matplotlib.figure import Figure
from matplotlib import colormaps
from numpy import ndarray
from io import BytesIO
from rasterio.crs import CRS
from affine import Affine
from rasterio.io import MemoryFile

def make_index_preview(array: ndarray, title: str) -> BytesIO:
    h, w = array.shape
    scale = 1200 / max(h, w)
    fig = Figure(figsize=(w * scale / 100, h * scale / 100), dpi=100)

    cmap = colormaps["turbo"].copy()
    cmap.set_bad("black")

    ax = fig.add_subplot()
    ax.axis('off')
    ax.set_title(title)

    im = ax.imshow(array, cmap=cmap, vmin=-1, vmax=1, aspect="equal", interpolation="nearest")
    fig.colorbar(im, ax=ax)

    buf = BytesIO()
    fig.savefig(buf, format="JPEG")
    buf.seek(0)

    return buf

def make_index_geotiff(array: ndarray, crs: CRS, transform: Affine):
    h, w = array.shape
    meta = {
        "driver": "GTiff",
        "dtype": "float32",
        "nodata": None,
        "width": w,
        "height": h,
        "count": 1,
        "crs": crs,
        "transform": transform,
        "compress": "deflate"
    }

    with MemoryFile() as memfile:
        with memfile.open(**meta) as dataset:
            dataset.write(array, 1)
        return memfile.read()