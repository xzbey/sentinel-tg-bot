from typing import Any

import geopandas as gpd
from sentinelhub import Geometry, CRS
from shapely import make_valid
from shapely.geometry import Point, Polygon, MultiPolygon
from pyogrio.errors import DataSourceError
from io import BytesIO

from core.error import ParseError

def parse_file(data: bytearray):
    try:
        gpf = gpd.read_file(BytesIO(data), rows=1)
    except DataSourceError:
        raise ParseError("Битый файл")

    if gpf.empty:
        raise ParseError("Пустой файл")

    if gpf.crs and gpf.crs.to_epsg() != 4326:
        gpf = gpf.to_crs(epsg=4326)

    geom: Any = gpf.geometry.iloc[0]

    if geom is None or geom.is_empty:
        raise ParseError("Пустая геометрия в файле")

    if not geom.is_valid:
        geom = make_valid(geom)

    match geom:
        case Point() as point:
            return {
                "state": "point",
                "geometry": (point.x, point.y)
            }

        case Polygon() | MultiPolygon():
            return {
                "state": "polygon",
                "geometry": Geometry(geom, crs=CRS.WGS84)
            }

        case _:
            raise ParseError("Неправильный тип геометрии (поддерживаются только Point, Polygon, MultiPolygon)")
