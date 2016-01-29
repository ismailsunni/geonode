# -*- coding: utf-8 -*-
from geosafe.celery import app
from renderer import Renderer

__author__ = 'etienne'
__project_name__ = 'geonode'
__filename__ = 'view'
__date__ = '1/29/16'
__copyright__ = 'etienne@kartoza.com'

renderer = Renderer()


@app.task
def render_tile(layer, z, x, y):
    global renderer
    renderer.make_tile(layer, z, x, y)
    return 0
