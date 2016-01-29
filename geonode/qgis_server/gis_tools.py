# -*- coding: utf-8 -*-

from math import atan, degrees, sinh, pi, radians, log, cos, tan
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform


def num2deg(xtile, ytile, zoom):
    """Conversion of X,Y and zoom to lat/lon coordinates."""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
    lat_deg = degrees(lat_rad)
    return lat_deg, lon_deg


def deg2num(lat_deg, lon_deg, zoom):
    """Conversion of lat/lon coordinates and zoom to X,Y."""
    lat_rad = radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)
    return xtile, ytile


def geo_extent(extent, source_crs):
    """Convert the supplied extent to geographic coordinates.

    :param extent: Rectangle defining a spatial extent in any CRS.
    :type extent: QgsRectangle

    :param source_crs: Coordinate system used for input extent.
    :type source_crs: QgsCoordinateReferenceSystem

    :returns: Rectangle in geographic coordinates EPSG:4326.
    :rtype: QgsRectangle
    """

    geo_crs = QgsCoordinateReferenceSystem('EPSG:4326')
    transform = QgsCoordinateTransform(source_crs, geo_crs)
    return transform.transformBoundingBox(extent)
