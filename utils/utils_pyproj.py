

from pyproj import CRS, Transformer


def create_crs(lat: float, lon: float) -> CRS:
    """Create a projected Coordinate Reference System centered at lat&lon (based on Traverse Mercator)."""
    new_crs_string = (
        "+proj=tmerc +ellps=WGS84 +datum=WGS84 +units=m +no_defs +lon_0="
        + str(lon)
        + " lat_0="
        + str(lat)
        + " +x_0=0 +y_0=0 +k_0=1"
    )
    crs2 = CRS.from_string(new_crs_string)

    return crs2


def reproject_to_crs(
    lat: float, lon: float, crs_from, crs_to, direction="FORWARD"
) -> tuple[float]:
    """Reproject a point to a different Coordinate Reference System."""
    transformer = Transformer.from_crs(crs_from, crs_to, always_xy=True)
    pt = transformer.transform(lon, lat, direction=direction)

    return pt[0], pt[1]


def getBbox(lat, lon, r):
    
    projectedCrs = create_crs(lat, lon)
    lonPlus1, latPlus1 = reproject_to_crs(1, 1, projectedCrs, "EPSG:4326")
    scaleX = lonPlus1 - lon
    scaleY = latPlus1 - lat

    bbox = (lat-r*scaleY, lon-r*scaleX, lat+r*scaleY, lon+r*scaleX)
    return bbox 
