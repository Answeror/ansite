#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Flask, render_template, abort, url_for
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

        from .page import Pages
        pages = Pages(FlatPages(app), self.make_hist)

        import git
        self.git = git.Git(os.getcwd())
        self.repo = git.Repo(os.getcwd())

        @app.route('/')
        def index():
            return render_template('index.html', pages=pages, title=self.title)

        @app.route('/<path:path>.html')
        def page(path):
            page = pages.get_or_404(path)
            # trigger frozen-flask
            if page.meta.get('json', False):
                url_for('page_json', path=path)
            kargs = { 'page': page }
            if 'hole' in page.meta:
                kargs['html'] = self._load_post_html(page.meta['hole'])
            else:
                kargs['hist'] = self.make_hist(page)
            return render_template('page.html', **kargs)

        @app.route('/whole.json')
        def whole():
            import json
            from datetime import date
            return json.dumps(
                [self._page_to_dict(self._fill_hole(page)) for page in pages],
                default=lambda o: str(o) if isinstance(o, date) else None
            ), 200, {'Content-Type': 'application/json'}

        @app.route('/<path:path>.json')
        def page_json(path):
            import json
            from datetime import date
            page = pages.get_or_404(path)
            if not page.meta.get('json', False):
                abort(404)
            return json.dumps(
                self._page_to_dict(self._fill_hole(page)),
                default=lambda o: str(o) if isinstance(o, date) else None
            ), 200, {'Content-Type': 'application/json'}

        @app.route('/search.html')
        def search():
            return render_template('search.html')

        @app.route('/style.css')
        def style():
            return sass.compile(app), 200, {'Content-Type': 'text/css'}

    def _load_remote(self, url):
        import urllib2
        return urllib2.urlopen(url).read()

    def _load_page(self, hole):
        import json
        return json.loads(self._load_remote('http://%s.json' % hole))

    def _load_html(self, hole):
        return self._load_remote('http://%s.html' % hole).decode('utf-8')

    def _load_post_html(self, hole):
        from pyquery import PyQuery as pq
        d = pq(self._load_html(hole))
        return d('.post').html()

    def _fill_hole(self, page):
        if 'hole' in page.meta:
            page.body = self._load_page(page.meta['hole'])['body']
        return page

    def _page_to_dict(self, page):
        from copy import copy
        d = copy(page.meta)
        d['body'] = page.body
        d['route'] = page.path + '.html'
        return d

    def build(self, output_path=os.path.join(os.getcwd(), 'build')):
        self.app.config['FREEZER_DESTINATION'] = output_path
        freezer = Freezer(self.app)
        freezer.freeze()

    def run(self, port=8000):
        self.app.run(port=port)
