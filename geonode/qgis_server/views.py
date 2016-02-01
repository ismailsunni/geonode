__author__ = 'ismailsunni, etienne'
__project_name__ = 'geonode'
__filename__ = 'views'
__date__ = '1/29/16'
__copyright__ = 'imajimatika@gmail.com, etienne@kartoza.com'


import os
import logging
import zipfile
import StringIO
from os.path import exists, dirname, split, join
from os import makedirs, listdir
from sys import maxsize
from django.http import HttpResponse, Http404
from geonode.settings import QGIS_SERVER_CONFIG
from celery_worker import render_tile

from django.http import HttpResponse
from django.db.models import ObjectDoesNotExist
from geonode.layers.models import Layer
from geonode.qgis_server.models import QGISServerLayer

logger = logging.getLogger('geonode.qgis_server.views')


def download_zip(request, layername):
    try:
        layer = Layer.objects.get(name=layername)
    except ObjectDoesNotExist:
        logger.debug('No layer found for %s' % layername)
        return

    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        logger.debug('No QGIS Server Layer for existing layer %s' % layername)
        return

    basename, _ = os.path.splitext(qgis_layer.base_layer_path)
    # Files (local path) to put in the .zip
    filenames = []
    for ext in QGISServerLayer.accepted_format:
        target_file = basename + '.' + ext
        if os.path.exists(target_file):
            filenames.append(target_file)

    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    zip_subdir = layer.name
    zip_filename = "%s.zip" % zip_subdir

    # Open StringIO to grab in-memory ZIP contents
    s = StringIO.StringIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        logger.debug('fpath: %s' % fpath)
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        logger.debug('fdir: %s' % fdir)
        logger.debug('fname: %s' % fname)

        zip_path = os.path.join(zip_subdir, fname)
        logger.debug('zip_path: %s' % zip_path)

        # Add file, at correct path
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(s.getvalue(), mimetype = "application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp

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
