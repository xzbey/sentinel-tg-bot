from dataclasses import dataclass, field
from sentinelhub import Geometry
from rasterio.crs import CRS
from asyncio import Lock
from numpy import ndarray, stack as npstack
from affine import Affine

@dataclass
class Scene:
    bands: dict[str, ndarray]
    geometry: Geometry
    size: tuple[int, int]
    resolution: int
    date: str
    crs: CRS
    transform: Affine
    metadata: dict
    address: str
    coords: tuple
    lock: Lock = field(default_factory=Lock)

    def missing(self, names: list[str]) -> list[str]:
        return [band for band in names if band not in self.bands]

    def add(self, name: str, array: ndarray) -> bool:
        if name not in self.bands:
            self.bands[name] = array
            return True
        return False

    def stack(self, names: list[str]) -> ndarray:
        return npstack([self.bands[name] for name in names], axis=-1)