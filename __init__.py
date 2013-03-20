#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Flask, render_template
from flask.ext.flatpages import FlatPages
from flask_frozen import Freezer
import sass
import markdown
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

    extensions.extend(['fenced_code', 'def_list'])

    import mdx_mathjax as mathjax
    extensions.append(mathjax.makeExtension())

    return markdown.markdown(render_jinja2(text), extensions)


def render_jinja2(text):
    from jinja2 import Environment
    env = Environment(extensions=[ShpamlExtension])
    return env.from_string(text).render()


from jinja2.ext import Extension


class ShpamlExtension(Extension):

    tags = set(['shpaml'])

    def __init__(self, env):
        super(ShpamlExtension, self).__init__(env)

    def parse(self, parser):
        from jinja2 import nodes
        lineno = parser.stream.next().lineno
        body = parser.parse_statements(['name:endshpaml'], drop_needle=True)
        return nodes.CallBlock(
            self.call_method('_shpaml', []),
            [],
            [],
            body
        ).set_lineno(lineno)

    def _shpaml(self, caller):
        from shpaml import convert_text
        return convert_text(caller())


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


class Hist(object):

    def __init__(self, commit):
        from datetime import datetime
        self.time = datetime.fromtimestamp(commit.committed_date)
        self.message = commit.message


class Site(object):

    def make_hist(self, page):
        path = os.path.join(FLATPAGES_ROOT, page.path + '.md')
        return [Hist(self.repo.rev_parse(c)) for c in
                self.git.log('--pretty=%H', '--follow', '--', path).split('\n')]

    def __init__(self, name):
        self.title = name

        app = Flask(
            __name__,
            static_folder=os.path.join(ROOT, 'static'),
            template_folder=os.path.join(ROOT, 'templates')
        )
        self.app = app
        app.config.from_object(__name__)
        pages = FlatPages(app)

        import git
        self.git = git.Git(os.getcwd())
        self.repo = git.Repo(os.getcwd())

        @app.route('/')
        def index():
            return render_template('index.html', pages=pages, title=self.title)

        @app.route('/<path:path>.html')
        def page(path):
            page = pages.get_or_404(path)
            return render_template('page.html', page=page, hist=self.make_hist(page))

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

    def build(self, output_path=os.path.join(os.getcwd(), 'build')):
        self.app.config['FREEZER_DESTINATION'] = output_path
        freezer = Freezer(self.app)
        freezer.freeze()

    def run(self, port=8000):
        self.app.run(port=port)
