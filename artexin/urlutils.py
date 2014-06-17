"""
urlutils.py: tools for manipulating URLs

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import re
import urllib.parse as urlparse
import itertools
from posixpath import join


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1
__all__ = ('mask', 'split', 'normalize', 'base_path', 'join', 'absolute_path',
           'is_http_url', 'normalize_scheme', 'full_url')


MULTISLASH = re.compile(r'\/+')
FLIP = lambda x: 1 ^ x  # flips the bit in ``x`` (1 becomes 0, 0 becomes 1)
ROOT_MASK = (1, 1, 0, 0, 0, 0)  # used with urlparse() results
TAIL_MASK = tuple(map(FLIP, ROOT_MASK))  # reverse of ROOT_MASK


def mask(iterable, mask, empty=''):
    """ Masks elements in ``iter`` using a iterable of booleans

    For each value ``In`` of iterable ``iterable``, a member of the ``mask``
    iterable with same index ``Mn`` is tested. If ``Mn`` is ``True``, ``In`` is
    kept. Otherwise, it is replaced by ``empty``.

    Example::

        >>> i = [1, 2, 3, 4]
        >>> m = [0, 1, 1, 0]
        >>> e = None
        >>> list(mask(i, m, e))
        [None, 2, 3, None]

        # ``empty`` defaults to empty string
        >>> i = ['foo', 'bar', 'baz']
        >>> m = [0, 0, 1]
        >>> list(mask(i, m))
        ['', '', 'baz']

    :param iterable:    Iterable to be masked
    :param mask:        The mask iterable
    :param empty:       The value to be used when mask evaluates to ``False``
                        (default: empty string)
    :return:            Iterator containing masked values
    """
    return tuple(map(lambda m, i: i if m else empty, mask, iterable))


def split(url):
    """ Splits the path between root (scheme + FQDN) and rest of the URL

    Example::

        >>> split('http://example.com/foo')
        ('http://example.com', '/foo')
        >>> split('/foo/bar')
        ('', '/foo/bar')
        >>> split('https://user:pwd@www.test.com/foo/bar')
        ('https://user:pwd@www.test.com', '/foo/bar')
        >>> split('http://localhost/?foo=bar')
        ('http://localhost', '/?foo=bar')
        >>> split('http://localhost/foo?bar=baz')
        ('http://localhost', '/foo?bar=baz')

        # FIXME: This example does not work as expected, no idea why
        >>> split('http://localhost?foo=bar')
        ('http://localhost', '/?foo=bar')

    :param url:     URL to strip the root from
    :returns:       path with root stripped
    """
    parsed = urlparse.urlparse(url)
    base = urlparse.urlunparse(mask(parsed, ROOT_MASK))
    stripped = urlparse.urlunparse(mask(parsed, TAIL_MASK))
    if stripped[0] != '/':
        return '/' + stripped
    return base, stripped


def normalize(path):
    """ Convert all .. and . to appropriate paths

    Leading double dots are left alone.

    Example::

        >>> normalize('a/../b')
        'b'
        >>> normalize('/foo/bar/../baz/./fam')
        '/foo/baz/fam'
        >>> normalize('../foo/bar')
        '../foo/bar'
        >>> normalize('.././../foo/bar')
        '../../foo/bar'
        >>> normalize('.././../foo/../bar')
        '../../bar'

    :param path:    Full path to resource
    :returns:       Normalized path
    """
    comps = path.split('/')
    parts = []
    accumulate_dots = True
    for comp in comps:
        if comp == '..':
            if accumulate_dots:
                parts.append(comp)
            else:
                parts.pop()
        elif comp == '.':
            continue
        else:
            parts.append(comp)
            accumulate_dots = False
    return '/'.join(parts)


def base_path(path):
    """ Get base path of a web resource

    This function treats the path as folder structure and keeps URLs that
    end in ``/`` as they are, stripping anything that appears after the last
    ``/`` except the ``/`` itself.

    Example::

        >>> base_path('/foo/bar/baz/')
        '/foo/bar/baz/'
        >>> base_path('/foo/bar/baz')
        '/foo/bar/'
        >>> base_path('/')
        '/'
        >>> base_path('')
        '/'
        >>> base_path('foo')
        '/'
        >>> base_path('foo/bar')
        'foo/'
        >>> base_path('/foo/bar/../baz')
        '/foo/'
        >>> base_path('../foo/fam/')
        '../foo/fam/'

    :param path:    Full path of the resource
    :returns:       The base path
    """
    path = normalize(path)
    comps = path.split('/')
    if comps[-1] != '':
        comps[-1] = ''
    if len(comps) == 1:
        return '/'
    return '/'.join(comps)


def absolute_path(path, base):
    """ Return absolute path of ``path`` relative to ``base``

    Example::

        >>> absolute_path('foo/bar/', '/')
        '/foo/bar/'
        >>> absolute_path('../foo1/bar1/baz1', '/foo/bar/baz')
        '/foo/foo1/bar1/baz1'
        >>> absolute_path('/foo/bar/baz', '/baz')
        '/foo/bar/baz'

    :param path:    Path for which to calculate the absolute path
    :param base:    Path on which the base the calculation
    :returns:       Absolute path
    """
    base = base_path(base)
    return normalize(join(base, path))


def is_http_url(url):
    """ Test if ``url`` represents a full HTTP/HTTPS URL with FQDN

    Example::

        >>> is_http_url('http://www.example.com/')
        True
        >>> is_http_url('http//foobar')
        False
        >>> is_http_url('https://example')
        True
        >>> is_http_url('/foo')
        False
        >>> is_http_url('http://www.example.com/foo')
        True
        >>> is_http_url('//www.example.com')
        True

    :param url:     URL to test
    :returns:       True if URL is full url with scheme and FQDN
    """
    return any([url.startswith(i) for i in ('http://', 'https://', '//')])


def full_url(base, rest):
    """ Merges the base of the URL with rest of it (path, query params, etc)

    If the ``base`` URL contains more than just the scheme and host (e.g.,
    'http://www.example.com/foo/bar/baz') the path and other info will be
    stripped (e.g., '/foo/bar/baz' would be stripped).

    Any missing bits will be replaced by empty string.

    Example::

        >>> full_url('http://example.com', '/foo/bar')
        'http://example.com/foo/bar'
        >>> full_url('http://example.com/foo', '/foo/bar')
        'http://example.com/foo/bar'
        >>> full_url('http://example.com', 'foo/bar')
        'http://example.com/foo/bar'
        >>> full_url('', 'foo/bar')
        'foo/bar'

    :param base:    Base URL (scheme, domain)
    :param rest:    Rest of the url (path, query params, fragments, etc)
    """
    base = urlparse.urlparse(base)
    rest = urlparse.urlparse(rest)
    return urlparse.urlunparse(base[:2] + rest[2:])


def normalize_scheme(url, scheme='http'):
    """ Normalize URL so it has a scheme if it is a mutli-scheme URL

    Example::

        >>> normalize_scheme('http://www.example.com', 'http')
        'http://www.example.com'
        >>> normalize_scheme('//example.com', 'http')
        'http://example.com'

    :param url:     URL to be normalized
    :param scheme:  Scheme to use for the URL
    """
    if url.startswith('//'):
        return scheme + ':' + url
    return url

if __name__ == '__main__':
    import doctest
    doctest.testmod()
