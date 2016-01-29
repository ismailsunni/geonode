# -*- coding: utf-8 -*-

from os.path import splitext, join, basename
from qgis.core import (
    QgsApplication,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsMapSettings,
    QgsMapLayerRegistry,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsRectangle,
    QgsMapRendererSequentialJob)
from PyQt4.QtCore import QSize

from geonode.settings import QGIS_SERVER_CONFIG
from gis_tools import num2deg

__author__ = 'etienne'
__project_name__ = 'geonode'
__filename__ = 'view'
__date__ = '1/29/16'
__copyright__ = 'etienne@kartoza.com'


class Renderer(object):
    def __init__(self):
        """Constructor for the QGIS app."""
        self.qgis_app = QgsApplication(
            [], False, QGIS_SERVER_CONFIG['qgis_path'])
        self.qgis_app.initQgis()
        self.map_settings = QgsMapSettings()
        self.map_settings.setOutputSize(QSize(256, 256))
        epsg_3857 = QgsCoordinateReferenceSystem('EPSG:3857')
        epsg_4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        self.map_settings.setDestinationCrs(epsg_3857)
        self.map_settings.setCrsTransformEnabled(True)
        self.transform = QgsCoordinateTransform(epsg_4326, epsg_3857)
        self.map_layer_registry = QgsMapLayerRegistry.instance()

        self.layer = None

    def _set_layer(self, layer):
        self.layer = layer
        name = basename(splitext(self.layer['name'])[0])
        path = join(QGIS_SERVER_CONFIG['layer_directory'], self.layer['name'])
        if self.layer['type'] == 'vector':
            qgis_layer = QgsVectorLayer(path, name, 'ogr')
        else:
            qgis_layer = QgsRasterLayer(path, name)

        if not qgis_layer.isValid():
            raise Exception('Layer not valid.')

        self.map_layer_registry.addMapLayer(qgis_layer)
        self.map_settings.setLayers([qgis_layer.id()])

    def _remove_layer(self):
        self.map_settings.setLayers([])
        self.map_layer_registry.removeAllMapLayers()

    def make_tile(self, layer, z, x, y):
        """Generate a tile according the X,Y and the zoom."""
        tile_path = QGIS_SERVER_CONFIG['tile_path']
        self._set_layer(layer)

        top, left = num2deg(x, y, z)
        bottom, right = num2deg(x + 1, y + 1, z)
        rectangle = QgsRectangle(
            self.transform.transform(left, bottom),
            self.transform.transform(right, top))
        self.map_settings.setExtent(rectangle)
        job = QgsMapRendererSequentialJob(self.map_settings)
        job.start()
        job.waitForFinished()
        tile_filename = tile_path % (self.layer['id'], z, x, y)
        job.renderedImage().save(tile_filename)

        self._remove_layer()
