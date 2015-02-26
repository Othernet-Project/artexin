"""
fetch_to_dir.py: Fetch specified pages into seaprate directories

This demo script uses the low-level methods from the artexin package to fetch
and extract articles from a few different pages on the web.

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os
import time

from artexin.extract import extract, process_images, strip_links
from artexin.fetch import fetch_rendered
from artexin.preprocessors import pp_wikipedia


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1


PAGES = [
    ('http://www.nasa.gov/press/2014/may/nasa-releases-earth-day-global-selfie-mosaic-of-our-home-planet',
     'nasa_selfies'),
    ('http://en.wikipedia.org/wiki/Sunflower',
     'sunflower',
     [pp_wikipedia]),
    ('http://en.wikipedia.org/wiki/Logarithm',
     'logarithm',
     [pp_wikipedia]),
    ('http://freepythontips.wordpress.com/2013/07/30/20-python-libraries-you-cant-live-without/',
     '20_python_libs')
]


def writefiles(url, name, preprocessors=[]):
    dirpath = os.path.join('/vagrant/', name)
    htmlpath = os.path.join(dirpath, '%s.html' % name)
    print("Fetching `%s`" % url)
    c = fetch_rendered(url)
    print("Processing HTML")
    for p in preprocessors:
        c = p(c)
    title, html = extract(c)
    try:
        os.mkdir(dirpath)
    except OSError:
        pass
    print("Processing and downloading images")
    html, images = process_images(html, url, dirpath)
    print("Stripping links")
    html = strip_links(html)
    print("Page has %s images" % len(images))
    print("Writing HTML to %s" % htmlpath)
    f = open(htmlpath, 'w')
    f.write(html.encode('utf-8', errors='remove'))
    f.close()

if __name__ == '__main__':
    start = time.time()
    for page in PAGES:
        writefiles(*page)
    duration = time.time() - start
    print("Took %s seconds" % duration)
