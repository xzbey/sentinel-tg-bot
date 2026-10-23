from io import BytesIO
from analysis.render import make_index_preview
from core.scene import Scene
from analysis.export import make_preview
from core.error import ParseError
from core.config import allowableBands, MAX_CUSTOM_BANDS


composites_names = {
    "Ложный ИК": ["B08", "B04", "B03"],
    "SWIR": ["B12", "B08", "B04"],
    "Сельхоз": ["B11", "B08", "B02"]
}

def make_composite_preview(scene: Scene, bands: list[str]) -> BytesIO:
    match len(bands):
        case 1:
            return make_index_preview(scene.bands[bands[0]], title=bands[0])
        case 2:
            bands_in_2 = [*bands, bands[-1]]
            return make_preview(scene, bands_in_2)
        case 3:
            return make_preview(scene, bands)
        case _:
            return None

def parse_composite_text(text: str) -> list[str]:
    bands = text.upper().split(" ")
    if not bands:
        raise ParseError("Введите хотя бы один канал!")
    if len(bands) > MAX_CUSTOM_BANDS:
        raise ParseError(f"Превышено количество доступных каналов, максимум доступно {MAX_CUSTOM_BANDS}")

    for band in bands:
        if band not in allowableBands:
            raise ParseError(f"Найдено неизвестное слово в запросе: {band}!")

    return bands