#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Flask, render_template
from flask.ext.flatpages import FlatPages
from flask_frozen import Freezer
import sass
import markdown
import glob
import os


def render_markdown(text):
    try:
        import pygments
    except ImportError:
        extensions = []
    else:
        extensions = ['codehilite']

    from header import CutheadExtension
    extensions.append(CutheadExtension({}))

    extensions.append('fenced_code')

    import mdx_mathjax as mathjax
    extensions.append(mathjax.makeExtension())

    return markdown.markdown(text, extensions)


ROOT = os.path.dirname(__file__)
DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = '.md'
FREEZER_RELATIVE_URLS = True
SCSS_LOAD_PATHS = [os.path.join(ROOT, 'static/scss')]
SCSS_PATHS = (
    os.path.join(ROOT, 'static/scss/solarized.scss'),
    os.path.join(ROOT, 'static/scss/mine.scss'),
    os.path.join(ROOT, 'static/scss/theme.scss')
)
FREEZER_REMOVE_EXTRA_FILES = False
FLATPAGES_HTML_RENDERER = render_markdown
FLATPAGES_ROOT = os.path.join(os.getcwd(), 'pages')


app = Flask(
    __name__,
    static_folder=os.path.join(ROOT, 'static'),
    template_folder=os.path.join(ROOT, 'templates')
)
app.config.from_object(__name__)
pages = FlatPages(app)


@app.route('/')
def index():
    return render_template('index.html', pages=pages)


@app.route('/<path:path>.html')
def page(path):
    page = pages.get_or_404(path)
    return render_template('page.html', page=page)


def page_to_dict(page):
    from copy import copy
    d = copy(page.meta)
    d['body'] = page.body
    d['route'] = page.path + '.html'
    return d


@app.route('/whole.json')
def whole():
    import json
    from datetime import date
    return json.dumps(
        [page_to_dict(page) for page in pages],
        default=lambda o: str(o) if isinstance(o, date) else None
    ), 200, {'Content-Type': 'application/json'}


@app.route('/search.html')
def search():
    return render_template('search.html')


@app.route('/style.css')
def style():
    return sass.compile(app), 200, {'Content-Type': 'text/css'}


def build(output_path='build'):
    app.config['OUTPUT_PATH'] = output_path
    freezer = Freezer(app)
    freezer.freeze()


def run(port=8000):
    app.run(port=port)
