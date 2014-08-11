#!/usr/bin/env python3

"""
test_url.py: Tool that outputs files as they would be output by collect

This script can be used to test specified URLs. It outputs HTML and image files
to a desired directory in a form that would be output by the article extraction
process.

It deliberately does not handle any exceptions so all errors can be
troubleshooted.

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import sys
import os
from os.path import dirname as up, abspath, join
import time

sys.path.insert(0, up(up(abspath(__file__))))
sys.path.insert(0, join(up(up(abspath(__file__))), 'artexin'))

from artexin.extract import extract, strip_links, process_images
from artexin.pack import percent_escape
from artexin.fetch import fetch_rendered, fetch_content
from artexin.preprocessor_mappings import get_preps


def collect(url, output_dir, fetch_method='rendered'):
    start = time.time()
    if fetch_method == 'rendered':
        page = fetch_rendered(percent_escape(url))
    else:
        page = fetch_content(url)
    print(page)
    for preprocessor in get_preps(url):
        page = preprocessor(page)
    title, html = extract(page)
    html = strip_links(html)
    html, images = process_images(html, url, output_dir)
    with open(join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    return time.time() - start


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='simulate article extraction')
    parser.add_argument('url', metavar='URL', help='URL of the page to parse')
    parser.add_argument('--out', metavar='PATH', help='output directory '
                        '(default: current directory)', default='.')
    parser.add_argument('--no-javascript', help="Run page's javascript",
                        action='store_true')
    args = parser.parse_args()

    method = args.no_javascript and 'plain' or 'rendered'

    print("Collecting '%s' into '%s'"  % (args.url, args.out))
    took = collect(args.url, args.out, method)
    print("Took %s seconds" % round(took, 2))

