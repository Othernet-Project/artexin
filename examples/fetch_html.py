"""
fetch_html.py: Fetch HTML for a single page and write it into a file

This demo script uses the low-level methods from the artexin package to fetch
and extract relevant text from a single web page. The page is chosen to contain
a significant amount of boilerplate template code but no significant
JavaScript.

Also demonstrates the use of extra keyword arguments in ``extract()`` call.

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import time

from artexin.extract import extract
from artexin.fetch import fetch_content

__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1


if __name__ == '__main__':
    start = time.time()
    url = 'http://www.html-5-tutorial.com/all-html-tags.htm'
    c = fetch_content(url)
    title, html = extract(c, url=url)
    print("Fetched `%s`" % title)
    with open('/vagrant/test.html', 'w') as f:
        f.write(html)
    print("Finished in %s seconds" % (time.time() - start))
