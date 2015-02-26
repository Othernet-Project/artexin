"""
fetch_and_zip_batch.py: Fetch and zip specified pages in batch operation

This demo script uses the high-level functions from ``artexin.batch`` package
to process a set of pages.

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import time

from artexin.batch import batch


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1


PAGES = [
    'http://www.nasa.gov/press/2014/may/nasa-releases-earth-day-global-selfie-mosaic-of-our-home-planet',
    'http://en.wikipedia.org/wiki/Sunflower',
    'http://en.wikipedia.org/wiki/Logarithm',
    'http://freepythontips.wordpress.com/2013/07/30/20-python-libraries-you-cant-live-without/',
]


if __name__ == '__main__':
    start = time.time()
    results = batch(PAGES, base_dir='/vagrant', max_procs=8)
    took = time.time() - start

    for meta in results:
        print("Created: %s (%s bytes)" % (meta['zipfile'], meta['size']))

    print("Took %s seconds" % took)
