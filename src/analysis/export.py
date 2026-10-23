from core.scene import Scene

from numpy import clip, uint8
from PIL.Image import fromarray
from io import BytesIO
from rasterio.io import MemoryFile


def make_preview(scene: Scene, bands: list[str] = ["B04", "B03", "B02"]) -> BytesIO:
    preview = (clip(scene.stack(bands) * 3.0, 0, 1) * 255).astype(uint8)
    img = fromarray(preview)
    img.thumbnail((1280, 1280))

    preview_buf = BytesIO()
    img.save(preview_buf, format="JPEG", quality=85)
    preview_buf.seek(0)

    return preview_buf

def make_geotiff(scene: Scene, band_names: list[str]):
    meta = {
        "driver": "GTiff",
        "dtype": "float32",
        "nodata": None,
        "width": scene.size[0],
        "height": scene.size[1],
        "count": len(band_names),
        "crs": scene.crs,
        "transform": scene.transform,
        "compress": "deflate"
    }

    with MemoryFile() as memfile:
        with memfile.open(**meta) as dataset:
            for i, name in enumerate(band_names):
                dataset.write(scene.bands[name], i + 1)
        return memfile.read()