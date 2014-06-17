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
from itertools import repeat

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
        return str(next((e for e in [soup.title, soup.h1, soup.h2, soup.h3]
                         if e is not None)).string)
    except StopIteration:
        return ''


def extract(html, **kwargs):
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
    doc = Article(html, return_fragment=False, **kwargs)

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


def prepare_url(url, base, docpath):
    """ Prepare image URL for processing

    This function converts non-absolute URLs to absolute ones, and adds the
    scheme to scheme-less (multi-scheme) URLs.

        >>> prepare_url('/foo/bar', 'http://www.example.com', '/foo')

    :param url:     URL
    :param base:    Base URL of the document (FQDN)
    :param docpath: Path of the document without the base
    :result:        Prepared URL
    """
    proto = base.split(':')[0]
    if is_http_url(url):
        return normalize_scheme(url, proto)
    return full_url(base, absolute_path(url, docpath))


def process_image(data):
    """ Download and process single image

    :param data:    Tuple of image data (index, src URL, base URL of document)
    :returns:       Either image path if image was successfully downloaded and
                    stored, or ``None`` otherwise
    """
    idx, imgurl, imgdir = data
    imgpath_base = os.path.join(imgdir, 'image%04d' % idx)
    try:
        imgpath = fetch_image(imgurl, imgpath_base)[1]
        return imgpath
    except Exception:
        # FIXME: ``Exception`` might be a bit too broad
        return None


def imgsrc(path):
    """ Get ``src`` attribute value from image path

    Example::

        >>> imgsrc('/tmp/foo.png')
        './foo.png'

    :param path:    Path of the image on disk
    :returns:       Value for the ``src`` attribute
    """
    return './%s' % os.path.basename(path)


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

    seen = []     # All unique paths that have been seen thus far
    tags = []     # List of tags belonging to unique paths
    dupes = []    # Duplicate images (tuple: tag, index in uniques)
    images = []  # list of valid image paths
    soup = BeautifulSoup(html)

    # The reason uniques have a bit of cruft is we anticipate sending all
    # necessary data to process the image as a single tuple to another
    # function. This is done so that data can be serialized and sent to another
    # process which may not necessarily have access to variables in this scope.

    # Split all images into those with unique image tags and duplicates
    for img in soup.find_all('img'):
        src = img.get('src')
        if src is None:
            img.decompose()  # Don't keep images with no src
            continue
        if src in seen:
            dupes.append([img, seen.index(src)])
        else:
            seen.append(src)
            tags.append(img)

    nurls = len(seen)  # Number of unique URLs
    fornurls = lambda x: repeat(x, nurls)  # Repeat anything ``nurls`` times

    # Prepare all URLs
    base, docpath = split(base_url)
    urls = map(prepare_url, seen, fornurls(base), fornurls(docpath))

    # Process all unique images
    imgdata = ((idx, url, imgdir) for idx, url in enumerate(urls))
    # TODO: Make the following line branch off into separate (light) thread
    results = list(map(process_image, imgdata))

    # Update src in all image tags
    for tag, imgpath in zip(tags, results):
        if imgpath is None:
            tag.decompose()
        else:
            tag['src'] = imgsrc(imgpath)
            images.append(imgpath)

    # Update src in all dupes
    for tag, idx in dupes:
        imgpath = results[idx]
        if imgpath is None:
            tag.decompose()
        else:
            tag['src'] = imgsrc(imgpath)

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

