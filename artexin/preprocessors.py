"""
preprocessors.py: Preprocess HTML content before article extraction

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from bs4 import BeautifulSoup

from . import __version__ as _version, __author__ as _author


__version__ = _version
__author__ = _author
__all__ = ('pp_noop', 'pp_wikipedia',)



def pp_noop(html):
    """ Simply return the imput as is

    :param html:    String containing the HTML document
    :returns:       Processed HTML
    """
    return html


def pp_fixheaders(html):
    """ Fixes all headers so that top-most is always H1

    It promotes all headers so that H1 is the top-most header::

        >>> html = "<h2>This should be h1</h2><h3>Should be h2</h3>"
        >>> pp_fixheaders(html)
        '<html><body><h1>This should be h1</h1><h2>Should be h2</h2></body></html>'

    It will not do anything to lower levels if H1 is already top-most::

        >>> html = "<h1>This should be h1</h1><h3>But this is not h2</h3>"
        >>> pp_fixheaders(html)
        '<html><body><h1>This should be h1</h1><h3>But this is not h2</h3></body></html>'


    :param html:    String containing the HTML document
    :returns:       Processed HTML
    """
    soup = BeautifulSoup(html)
    adjust = None
    for level, h in enumerate(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], start=1):
        headings = soup.find_all(h)
        if headings and adjust is None:
            adjust = level - 1
        if adjust:
            for elem in headings:
                elem.name = 'h%s' % (level - adjust)
    return str(soup)


def pp_wikipedia(html):
    """ Preprocess Wikipedia article before extraction

    Simply calling the ``pp_wikipedia()`` function with HTML string returns
    the processed document as string.

        >>> from .fetch import fetch_content
        >>> c = fetch_content('http://en.wikipedia.org/wiki/Sunflower')
        >>> s = pp_wikipedia(c)

    It moves H1 into the content area so that it will be included during the
    extraction phase::

        >>> soup = BeautifulSoup(s)
        >>> soup.h1.parent.name
        'div'
        >>> soup.h1.parent['id']
        'mw-content-text'

        >>> '<h1 id="firstHeading" class="firstHeading" lang="en">' in s
        False
        >>> '<h1>Sunflower</h1>' in s
        True

    It will also remove any '[edit]' links::

        >>> '<a href="/w/index.php?title=Sunflower&amp' in s
        False

    Finally, it removes the 'zoom' links that are found next to images.

        >>> 'title="Enlarge">' in s
        False

    :param html:    String containing the HTML document
    :returns:       Processed HTML
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

    # Strip [EDIT] links
    for tag in soup.find_all('span', {'class': 'mw-editsection'}):
        tag.decompose()

    # Strip links to larger image
    for tag in soup.find_all('a', {'class': 'image'}):
        tag.unwrap()

    # Strip magnify icon
    for tag in soup.find_all('div', {'class': 'magnify'}):
        tag.decompose()

    # Convert all div.thumbcaption to p.thumbcaption
    for tag in soup.find_all('div', {'class': 'thumbcaption'}):
        tag.wrap(soup.new_tag('p'))
        tag.unwrap()

    # Remove all internal wiki links
    for tag in soup.find_all('a'):
        if tag.get('href', '').startswith('/wiki/'):
            tag.unwrap()

    # Remove create new page link
    for tag in soup.find_all('a', {'class': 'new'}):
        if tag.get('href', '').startswith('/w/index.php'):
            tag.unwrap()

    # Remove navbox
    for tag in soup.find_all('table', {'class': 'navbox'}):
        tag.decompose()

    # Remove wiki metadata
    for tag in soup.find_all('table', {'class': 'metadata'}):
        tag.decompose()

    # Remove small plainlinks
    for tag in soup.find_all('table', {'class': 'plainlinks'}):
        tag.decompose()

    # Remove hat notes
    for tag in soup.find_all('div', {'class': 'hatnote'}):
        tag.decompose()

    return str(soup)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
