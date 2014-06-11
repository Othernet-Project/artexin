"""
extract.py: Extract article text from a HTML page

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from __future__ import unicode_literals, print_function

import urlparse
import tempfile
import os

from readability.readability import Document
from bs4 import BeautifulSoup, Tag

from htmlutils import get_cls
from urlutils import split, join, absolute_path, is_http_url, full_url
from fetch import fetch_image


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1
__all__ = ('extract', 'extract_wikipedia', 'process_image')


PROCESSED_IMG_DIR = tempfile.gettempdir()


def extract(html):
    """ Extract an article from given URL

    Example::

        >>> from fetch import fetch_content
        >>> c = fetch_content('http://hetland.org/writing/instant-hacking.html')
        >>> t, s = extract(c)
        >>> f = open('/vagrant/instant.html', 'w')
        >>> f.write(s.encode('utf-8'))
        >>> f.close()
        >>> '<h1>What is Programming?</h1>' in s
        True
        >>> '<a href="./../research">Research</a>' in s
        False
        >>> '<div id="navigation">' in s
        False

    :param html:    String containing the HTML document
    :returns:       Two-tuple containing document title and article body
    """
    doc = Document(html)
    return (doc.title(), doc.summary())


def extract_wikipedia(html):
    """ Extract Wikipedia article

    None of the article extractions libraries managed to extract the complete
    Wikipedia article with all relevant parts intact. Because of this, we
    decided to implement a separate extraction method for Wikipedia articles
    that address some of the issues (e.g., Missing H1 tag).

    Example:

        >>> from fetch import fetch_content
        >>> c = fetch_content('http://en.wikipedia.org/wiki/Sunflower')
        >>> t, s = extract_wikipedia(c)
        >>> f = open('/vagrant/sunflower.html', 'w')
        >>> f.write(s.encode('utf-8'))
        >>> f.close()
        >>> '<h1>Sunflower</h1>' in s
        True
        >>> '<a href="/w/index.php?title=Sunflower&amp' in s
        False

    :param html:    String containing the HTML document
    :returns:       Two-tuple containing document title and article body
    """
    soup = BeautifulSoup(html)

    # Move H1 into article body container and extract the body container
    title = soup.new_tag('h1')
    title.string = soup.h1.string
    artbody = soup.find('div', {'id': 'mw-content-text'})
    if artbody:
        # There is a body, so we can use it to replace the entire contents of
        # the <body> tag.
        artbody.insert(0, title)
        artbody.extract()
        soup.body.clear()
        soup.body.append(artbody)

    for tag in soup.find_all('span', {'class': 'mw-editsection'}):
        # Strip [EDIT] links
        tag.decompose()

    return extract(unicode(soup))


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

        imgpath = os.path.join(imgdir, 'image%04d' % len(images))

        if is_http_url(src):
            # External image URLs are used as they are
            try:
                images.append(fetch_image(src, imgpath)[1])
            except Exception:
                # FIXME: ``Exception`` might be a bit too broad
                img.decompose()  # No usable image, so kill the tag
        else:
            # With internal images, we need to convert the image URL to an
            # absolute URL
            imgurl = full_url(base, absolute_path(src, doc_path))
            try:
                imgpath = fetch_image(imgurl, imgpath)[1]
                images.append(imgpath)
            except Exception:
                # FIXME: ``Exception`` might be a bit too broad
                img.decompose()
                continue
        seen.append(src)
    print(seen)
    return unicode(soup), images


def get_title(c):
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
        >>> get_title(c) is None
        True

    :param c:   Soup object
    :returns:   Document's title or None
    """
    try:
        return next((e for e in [c.title, c.h1, c.h2, c.h3]
                    if e is not None)).string
    except StopIteration:
        return None


def process_anchor(c, fn):
    """ Process all anchors in the parsed document using ``fn``

    The function ``fn`` takes the ``href`` value as string (can be empty string
    of there is not ``href`` attribute) and is expected to return a string
    that represents the updated value.

    This function processes not only anchors, but also ``<link>`` elements.

    Examples::

        >>> c = BeautifulSoup('''
        ... <html>
        ... <head></head>
        ... <body>
        ... <a href="http://example.com/foo"></a>
        ... <a href="http://example.com/bar"></a>
        ... <a href="http://example.com/baz"></a>
        ... </body>
        ... </html>''')
        >>> c = process_anchor(c, lambda u: u + '?foo=12')
        >>> str(c.a.get('href'))
        'http://example.com/foo?foo=12'

    :param c:   Soup object
    :param fn:  Function to process the anchors
    :returns:   BeautifulSoup object of the document, with anchors processed
    """
    for a in c.find_all('a'):
        a['href'] = fn(a.get('href', ''))
    return c



if __name__ == '__main__':
    import doctest
    from fetch import fetch_content
    import shutil
    #doctest.testmod()

    def writefiles(url, name, extractor=extract):
        dirpath = os.path.join('/vagrant/', name)
        htmlpath = os.path.join(dirpath, '%s.html' % name)
        try:
            os.mkdir(dirpath)
        except OSError:
            pass
        c = fetch_content(url)
        title, html = extractor(c)
        html, images = process_images(html, url, dirpath)
        f = open(htmlpath, 'w')
        f.write(html.encode('utf-8', errors='remove'))
        f.close()


    writefiles('http://en.wikipedia.org/wiki/Sunflower', 'sunflower',
               extractor=extract_wikipedia)
