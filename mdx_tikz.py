#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from markdown import *
import markdown
#from markdown.extensions import *
import markdown.extensions
from markdown.blockprocessors import BlockProcessor
from markdown.util import AtomicString, etree
from tempfile import mkdtemp
import os
from os import path
from subprocess import check_call
from shutil import rmtree
import glob
import logging


ROOT = os.path.dirname(__file__)


def default_prefix(r, uri):
    '''Remove the prefix for namespace `uri`.'''
    r.set('xmlns', uri)
    prefix = '{' + uri + '}'
    for e in r.getiterator():
        if e.tag.startswith(prefix):
            _, e.tag = e.tag.split('}')


def strip_whitespace(r):
    '''Strip all whitespace (bit too agressive)'''
    for e in r.getiterator():
        e.text = e.text and e.text.strip()
        e.tail = e.tail and e.tail.strip()


def collapse_groups(r):
    '''TikZ SVG sets only one attribute per group. Collapse groups with disjoint attributes.'''
    if len(list(r)) == 1 and r.tag == r[0].tag and set(r.attrib.keys()).isdisjoint(set(r[0].attrib.keys())):
        r.attrib.update(r[0].attrib)
        for x in r[0]:
            r.append(x)
        r.remove(r[0])
        collapse_groups(r)
    else:
        for x in r:
            collapse_groups(x)


def scale_attr(attr, scale):
    return str(scale * float(attr[:-2])) + attr[-2:]


def process(r):
    default_prefix(r, 'http://www.w3.org/2000/svg')
    strip_whitespace(r)
    # cause color error
    #collapse_groups(r)
    scale = 2
    r.attrib['width'] = scale_attr(r.attrib['width'], scale)
    r.attrib['height'] = scale_attr(r.attrib['height'], scale)


class TikzBlockProcessor(BlockProcessor):
    '''Compile tikzpicture-blocks to SVG.'''
    cache = {}
    BEGIN = r'\begin{tikzpicture}'
    END = r'\end{tikzpicture}'

    def test(self, parent, block):
        return self.BEGIN in block and self.END in block

    def compile(self, tikz):
        '''Compile previously unseen TikZ blocks'''
        if tikz not in self.cache:
            tmp = mkdtemp()
            tex = path.join(tmp, 'job.tex')

            with open(os.path.join(ROOT, 'tikz.tex.in'), 'rb') as f:
                template = f.read()

            with open(tex, 'wb') as f:
                f.write(template % tikz.encode('utf-8'))

            # Run Tex4Ht, creates SVG file(s).
            logging.info('before call tex4ht')
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with open(os.path.join(tmp, 'log'), 'w') as f:
                    check_call(['mk4ht', 'htlatex', 'job', 'xhtml'], shell=True, stdout=f, stderr=f)
            finally:
                os.chdir(cwd)
            logging.info('tex4ht done')
            # SVGs:
            results = list(glob.glob(path.join(tmp, '*.svg')))
            if results:
                self.cache[tikz] = etree.parse(results[0])
            # Cleanup
            rmtree(tmp)
        return self.cache.get(tikz)

    def run(self, parent, blocks):
        tikz = blocks.pop(0)
        svg = self.compile(tikz)
        if svg:  # success
            svg = svg.getroot()
            process(svg)
            parent.append(svg)
        else:  # error
            pre = etree.SubElement(parent, 'pre')
            code = etree.SubElement(pre, 'code')
            code.text = AtomicString(tikz)


class TikzExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.parser.blockprocessors.add('tikz', TikzBlockProcessor(md.parser), '>code')


def makeExtension(configs=None):
    return TikzExtension(configs)


if __name__ == '__main__':
    # Watch folder, compile all.
    #from pyinotify import *
    import pyinotify
    md = markdown.Markdown(output_format='xhtml5', extensions=[TikzExtension()])

    class CompileHandler(pyinotify.ProcessEvent):
        def process_IN_MODIFY(self, event):
            base, ext = path.splitext(event.pathname)
            if ext in ['.md', '.markdown']:
                print event.pathname
                outfile = base + '.html'
                md.convertFile(input=event.pathname, output=outfile)
                print '  =>', outfile

    wm = pyinotify.WatchManager()
    handler = pyinotify.CompileHandler()
    notifier = pyinotify.Notifier(wm, default_proc_fun=handler)
    wm.add_watch('.', pyinotify.ALL_EVENTS, rec=True, auto_add=True)
    print 'Monitoring. Press ^C to exit.'
    notifier.loop()
