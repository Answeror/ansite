#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Page(object):

    def __init__(self, impl, hist):
        self.impl = impl
        self.hist = hist

    @property
    def mtime(self):
        return self.hist[0].time if self.hist else self.ctime

    @property
    def ctime(self):
        for key in ('ctime', 'time', 'date'):
            if key in self.meta:
                return self.meta[key]
        return None

    @property
    def meta(self):
        return self.impl.meta

    @meta.setter
    def meta(self, value):
        self.impl.meta = value

    @property
    def body(self):
        return self.impl.body

    @body.setter
    def body(self, value):
        self.impl.body = value

    @property
    def path(self):
        return self.impl.path

    @path.setter
    def path(self, value):
        self.impl.path = value

    def __getitem__(self, key):
        return self.impl[key]


class Pages(object):

    def __init__(self, impl, make_hist):
        self.impl = impl
        self.make_hist = make_hist

    def __iter__(self):
        for page in self.impl:
            yield Page(page, self.make_hist(page))

    def get_or_404(self, path):
        return self.impl.get_or_404(path)

    def init_app(self, app):
        return self.impl.init_app(app)

    def reload(self):
        return self.impl.reload()
