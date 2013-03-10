#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scss
from collections import OrderedDict


def compile(app):
    scss.LOAD_PATHS = app.config.get('SCSS_LOAD_PATHS')
    return _compile(
        app.config.get('SCSS_PATHS')
    )


def _compile(sources):
    c = scss.Scss(
        scss_vars={},
        scss_opts={
            'compress': True,
            'debug_info': True,
            'load_paths': scss.LOAD_PATHS
        }
    )
    c._scss_files = OrderedDict(tuple(
        (source, open(source, 'r').read()) for source in sources
    ))
    return c.compile()
