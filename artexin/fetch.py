"""
fetch.py: fetch and process content from the web
"""

from __future__ import unicode_literals

import os
from urllib2 import urlopen
from cStringIO import StringIO
import tempfile

from bs4 import BeautifulSoup
from PIL import Image


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1
__all__ = ('fetch_content', 'get_parsed', 'get_title')


IEXTENSIONS = {  # Image file extensions
    'BMP':   '.bmp',
    'DCX':   '.dcx',
    'EPS':   '.eps',
    'GIF':   '.gif',
    'IM':    '.im',
    'JPEG':  '.jpg',
    'PCD':   '.pcd',
    'PCX':   '.pcx',
    'PDF':   '.pdf',
    'PNG':   '.png',
    'PPM':   '.pbm',
    'PSD':   '.psd',
    'TIFF':  '.tif',
    'XBM':   '.xbm',
    'XPM':   '.xpm',
}


def fetch_content(url):
    """ Fetches content from specified URL

    The response is a raw bytestring::

        >>> c = fetch_content('http://www.example.com/')
        >>> b'<title>Example Domain</title>' in c
        True

    Failures are propagated as they are without any error trapping::

        >>> c = fetch_content('http://nonexistent/')
        Traceback (most recent call last):
        ...
        URLError: ...

    :param url:     Document's URL
    :returns:       Document contents as bytestring
    """
    return urlopen(url).read()


def fetch_image(url, path):
    """ Fetches image from given URL

    When image cannot be fetched or not usable, it propagates appropriate
    exceptions from ``urllib2`` or Pillow/PIL.

    Example::

        >>> url = 'https://www.outernet.is/img/logo.png'
        >>> fmt, full_path = fetch_image(url, '/tmp/logo')
        >>> fmt
        'PNG'
        >>> full_path
        u'/tmp/logo.png'

        # Trying to fetch non-existent image
        >>> url = 'http://nonexistent/'
        >>> fetch_image(url, '/tmp/logo')
        Traceback (most recent call last):
        ...
        URLError: <urlopen error [Errno -2] Name or service not known>

        # Trying to fetch something that isn't a file
        >>> url = 'http://www.outernet.is/'
        >>> fetch_image(url, '/tmp/nonimage')
        Traceback (most recent call last):
        ...
        IOError: ...

    :param url:     Image's URL
    :param path:    Image path without extension
    :returns:       Tuple containing image format and temporary image path
    """
    content = fetch_content(url)

    # Store the content in temporary file
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(content)
    tmp.close()

    # Open the content as image and deduce its format
    img = Image.open(StringIO(content))
    img.verify()  # caller will have to trap exceptions
    fmt = img.format

    # Calculate the full path of the image and move the temporary file there
    full_path = "%s%s" % (path, IEXTENSIONS[fmt])
    os.rename(tmp.name, full_path)

    return fmt, full_path


def get_parsed(url):
    """ Fetches content from specified URL and returns beautiful soup

    This function retuns a BeautifulSoup-wrapped object representing the
    fetched HTML content.

    For instance::

        >>> b = get_parsed('http://www.example.com/')
        >>> isinstance(b, BeautifulSoup)
        True

    :param url:                 Document's URL
    :returns BeautifulSoup:     Parsed document as Soup object
    """
    c = fetch_content(url)
    return BeautifulSoup(c)


if __name__ == '__main__':
    import doctest
    # We use optionflags=doctest.IGNORE_EXCEPTION_DETAIL to ignore the
    # slight differences between Python 2.7.x and Python 3.x URLError
    # exception.
    doctest.testmod(optionflags=doctest.IGNORE_EXCEPTION_DETAIL)
