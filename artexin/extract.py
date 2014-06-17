"""
extract.py: Extract article text from a HTML page

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import urllib.parse as urlparse
import tempfile
import os

from breadability.readable import Article
from bs4 import BeautifulSoup, Tag

from htmlutils import get_cls
from urlutils import *
from fetch import fetch_image


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1
__all__ = ('extract', 'process_images', 'strip_links',)


PROCESSED_IMG_DIR = tempfile.gettempdir()


def get_title(soup):
    """ Get HTML title from the parsed document

    Function will look at ``<title>``, and headings level 1 through 3 and use
    the first tag that matches. If it finds no matching tag, it returns None.

    Example::

        >>> c = BeautifulSoup('''<html>
        ... <head>
        ... <title>Foo bar</title>
        ... </head>
        ... <body></body>
        ... </html>''')
        >>> str(get_title(c))
        'Foo bar'

        >>> c = BeautifulSoup('''<html>
        ... <head></head>
        ... <body><h1>Foo bar baz</h1></body>
        ... </html>''')
        >>> str(get_title(c))
        'Foo bar baz'

        >>> c = BeautifulSoup('''<html>
        ... <head></head>
        ... <body>
        ... <h2>Foo bar baz 1</h2>
        ... <h2>Foo bar baz 2</h2>
        ... </body>
        ... </html>''')
        >>> str(get_title(c))
        'Foo bar baz 1'

        >>> c = BeautifulSoup('''<html>
        ... <head></head>
        ... <body>
        ... <p>Foo bar baz</p>
        ... </body>
        ... </html>''')
        >>> get_title(c)
        ''

    :param soup:    Soup object
    :returns:       Document's title or None
    """
    try:
        return next((e for e in [soup.title, soup.h1, soup.h2, soup.h3]
                    if e is not None)).string
    except StopIteration:
        return ''


def extract(html):
    """ Extract an article from given URL

    Example::

        >>> from fetch import fetch_content
        >>> c = fetch_content('http://hetland.org/writing/instant-hacking.html')
        >>> t, s = extract(c)
        >>> 'What is Programming?' in s
        True
        >>> '<a href="./../research">Research</a>' in s
        False
        >>> '<div id="navigation">' in s
        False

    :param html:        String containing the HTML document
    :param **kwargs:    Extra arguments for readability's ``Document()`` class
    :returns:           Two-tuple containing document title and article body
    """
    # Extract article
    doc = Article(html, return_fragment=False)

    # Create basic <head> tag with <title> and charset tags
    clean_html = doc.readable
    soup = BeautifulSoup(clean_html)
    title_text = get_title(soup)
    head = soup.new_tag('head')
    title = soup.new_tag('title')
    title.string = title_text
    meta_charset = soup.new_tag('meta', charset='utf-8')
    meta_equiv = soup.new_tag('meta', content="text/html; charset='utf-8'")
    meta_equiv['name'] = 'http-equiv'  # new_tag() doesn't allow 'name' kwarg
    soup.html.insert(0, head)
    soup.head.append(meta_charset)
    soup.head.append(meta_equiv)
    soup.head.append(title)

    # Add doctype
    final = '<!DOCTYPE html>\n' + soup.prettify()
    return (title_text, final)


def process_images(html, base_url, imgdir=PROCESSED_IMG_DIR):
    """ Return list of absolute URLs for all images in pecified HTML

    Images found in the HTML will be downloaded. If the image file is not
    reachable or invalid, the <img> element will be stripped. Please note that
    network connections problems may also cause this to happen.

    The downloaded images will have a new filename in the following format:
    ``imageNNNN`` where ``NNNN`` is the index of its first appearance in the
    document.

    The ``imgdir`` should point to a directory where the images will be
    downloaded and stored temporarily in order to determine their format. The
    images are not processed in any way. It defaults to system's temporary
    directory or value of ``tempfile.tempdir`` when it is set to a value other
    than ``None``.

    Example::

        >>> imgurl = '/img/logo.png'
        >>> docurl = 'https://www.outernet.is/test.html'  # not a real URL, tho
        >>> html = '<html><body><p><img src="%s"></p></body></html>' % imgurl
        >>> html, images = process_images(html, docurl)
        >>> len(images)
        1
        >>> '/tmp/image0000.png' in images
        True
        >>> os.path.exists(images[0])
        True

    :param html:        String containing the HTML document
    :param base_url:    Base URL of the document
    :param imgdir:      Directory to use for temporary image storage
    :returns:           Tuple of processed document and image path list
    """

    # TODO: Also process links that point to larger versions of the image.

    seen = []  # original image URLs that have been seen
    images = []  # image paths
    soup = BeautifulSoup(html)
    base, doc_path = split(base_url)
    proto = base.split(':')[0]

    for img in soup.find_all('img'):
        src = img.get('src')

        if not src:
            img.decompose()  # Remove <img> tags with empty src
            continue

        if src in seen:
            # This image has already been processed, so we don't want to do it
            # again. Just use the existing data.
            idx = seen.index(src)
            img.src = os.path.basename(images[idx])
            continue

        imgpath_base = os.path.join(imgdir, 'image%04d' % len(images))

        if is_http_url(src):
            imgurl = normalize_scheme(src, proto)
        else:
            imgurl = full_url(base, absolute_path(src, doc_path))

        try:
            imgpath = fetch_image(imgurl, imgpath_base)[1]
            images.append(imgpath)
        except Exception:
            # FIXME: ``Exception`` might be a bit too broad
            img.decompose()  # No usable image, so kill the tag
            continue

        # Rewrite the path to point to image
        img['src'] = './%s' % os.path.basename(imgpath)

        # Register as seen
        seen.append(src)

    return str(soup), images


def strip_links(html):
    """ Strips all links that don't point to fragments

    Example::

        >>> html = '<html><body><a href="/foo">foo</a></body></html>'
        >>> strip_links(html)
        '<html><body>foo</body></html>'

    :param html:    HTML source
    :returns:       Processed HTML
    """
    soup = BeautifulSoup(html)
    for tag in soup.find_all('a'):
        if not tag.get('href', '').startswith('#'):
            tag.unwrap()
    return str(soup)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

