#-*- coding: utf-8 -*-
from os.path import exists, dirname, split, join
from os import makedirs, listdir
from sys import maxsize
from django.http import HttpResponse, Http404
from geonode.settings import QGIS_SERVER_CONFIG
from geonode.qgis_server.models import QGISServerLayer
from celery_worker import render_tile

__author__ = 'etienne'
__project_name__ = 'geonode'
__filename__ = 'view'
__date__ = '1/29/16'
__copyright__ = 'etienne@kartoza.com'


def tile(request, layer_id, z, x, y):
    x = int(x)
    y = int(y)
    z = int(z)

    # Fixme, check if the hash(layer_id) is in the database.

    layer_directory = QGIS_SERVER_CONFIG['layer_directory']
    # Fixme, fetch the filename from the database according to the hash and remove this var.
    layers = []
    for f in listdir(layer_directory):
        f = f.lower()
        if f.endswith(tuple(QGISServerLayer.vector_format)):
            file_name = split(join(layer_directory, f))[1]
            layers.append({
                'id': hex(hash(file_name) % ((maxsize + 1) * 2)),
                'name': file_name,
                'type': 'vector'
            })
        elif f.endswith('.tif'):
            file_name = split(join(layer_directory, f))[1]
            layers.append({
                'id': hex(hash(file_name) % ((maxsize + 1) * 2)),
                'name': file_name,
                'type': 'raster'
            })

    tile_filename = QGIS_SERVER_CONFIG['tile_path'] % (layer_id, z, x, y)
    if not exists(tile_filename):

        if not exists(dirname(tile_filename)):
            makedirs(dirname(tile_filename))

        for layer in layers:
            if layer['id'] == layer_id:
                process = render_tile.delay(layer, z, x, y)
                process.wait()
                break

    if not exists(tile_filename):
        raise Http404('The tile could not be found.')

    with open(tile_filename, 'rb') as f:
        return HttpResponse(f.read(), mimetype='image/png')
