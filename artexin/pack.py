"""
pack.py: package files for transport over Outernet

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import copy
import datetime
import hashlib
import logging
import os
import shutil
import tempfile
import zipfile
import urllib.parse as urlparse

try:
    import simplejson as json
except ImportError:
    import json

from . import __version__ as _version, __author__ as _author
from .content_crypto import sign_content
from .fetch import fetch_rendered, fetch_content
from .extract import extract, no_extract, strip_links, process_images


__version__ = _version
__author__ = _author
__all__ = ('zipdir', 'collect', 'create_zipball', 'BASE_DIR')


COMPRESSION = zipfile.ZIP_DEFLATED
BASE_DIR = tempfile.gettempdir()
TS_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
ESCAPE_MAPPINGS = (
    ('%', '%25'),
    ('(', '%2528'),
    (')', '%2529'),
    ('[', '%255B'),
    (']', '%255D'),
)


def percent_escape(url):
    for s, t in ESCAPE_MAPPINGS:
        url = url.replace(s, t)
    return url


def serialize_datetime(date_obj):
    return date_obj.strftime(TS_FORMAT)


def hash_data(*args):
    md5 = hashlib.md5()

    for data in args:
        md5.update(bytes(str(data), 'utf-8'))

    return md5.hexdigest()


def zipdir(path, dirpath):
    """ Create a zipball at ``path`` containing the directory at ``dirpath``

    :param path:        Path of the zipball
    :param dirpath:     Path of the directory to zip up
    """
    # Get the path of the directory's parent
    basepath = os.path.dirname(dirpath)

    # Compress all directory contents
    with zipfile.ZipFile(path, 'w', COMPRESSION) as zipball:
        for base_dir, subdirs, files in os.walk(dirpath):
            for path in files:
                cpath = os.path.join(base_dir, path)
                zipball.write(cpath, os.path.relpath(cpath, basepath))
        zipball.testzip()


def create_zipball(src_dir, meta, out_dir, keep_dir=False, keyring=None,
                   key=None, passphrase=None):
    """Copies the contents of the passed in `src_dir` to a newly created folder
    inside `out_dir`. Generates an info.json file from the passed in meta
    information and writes it into the newly created folder inside `out_dir`.
    Zip the newly created folder inside `out_dir` and save the zip file into
    `outdir`.
    Optionally preserve the newly created folder inside `out_dir`.
    Optionally encrypt the zip file, replacing it with the signed one.

    :param src_dir:     Source directory where the html and other resources are
    :param meta:        Meta information to be added to info.json as well
    :param out_dir:     Path where the zipball will be saved
    :param keep_dir:    Boolean, if True the newly created folder in `out_dir`
                        will be preserved
    :param keyring:     Keyring directory
    :param key:         Key to use for signing
    :param passphrase:  Key passphrase
    """
    meta = copy.copy(meta)

    checksum = hash_data(meta['url'])

    timestamp = meta['timestamp']
    meta['timestamp'] = serialize_datetime(timestamp)

    # Create the destination directory
    dest = os.path.join(out_dir, checksum)
    if os.path.exists(dest):
        shutil.rmtree(dest)

    shutil.copytree(src_dir, dest)

    # FIXME: Handle failure
    meta_path = os.path.join(dest, 'info.json')
    with open(meta_path, 'w', encoding='utf-8') as meta_file:
        meta_file.write(json.dumps(meta, indent=2))

    zippath = os.path.join(out_dir, '{0}.zip'.format(checksum))
    zipdir(zippath, dest)  # FIXME: Handle failure

    if not keep_dir:
        shutil.rmtree(dest)

    # Encrypt zip file
    if all([keyring, key, passphrase]):
        signed = sign_content(zippath,
                              keyring,
                              key,
                              passphrase,
                              output_dir=out_dir)
        if not os.path.exists(signed):
            # Python-gnupg will silently fail. It will log a warning, but won't
            # raise any exceptions. The only way to know is to test if the file
            # exists. If the file does not exist, we assume it failed.
            os.unlink(zippath)
            meta.update({'timestamp': timestamp,
                         'error': "Error signing '{0}'".format(zippath)})
            return meta

        os.unlink(zippath)
        zippath = signed

    meta.update({'zipfile': zippath,
                 'size': os.stat(zippath).st_size,
                 'hash': checksum,
                 # Pass timestamp as native datetime object
                 'timestamp': timestamp})
    return meta


def collect(url, keyring=None, key=None, passphrase=None, prep=[], meta={},
            base_dir=BASE_DIR, keep_dir=False, javascript=True,
            do_extract=True):
    """ Collect at ``url`` into a directory within ``base_dir`` and zip it

    The directory is created within ``base_dir`` that is named after the md5
    checksum of the ``identifier``.

    If the target directory already exists, it will be unlinked first.

    Metadata format:

    - ``url``: URL of the page
    - ``domain``: domain of the URL
    - ``timestamp``: time when page was retrieved
    - ``title``: page title
    - ``images``: number of images

    The above keys are writtein in the JSON file. The following keys are
    returned in addition:

    - ``zipfile``: path to package file (zip or sig)
    - ``size``: size of the package
    - ``hash``: checksum of the page URL

    :param url:         Identifier for the batch (usually URL of the page)
    :param keyring:     Keyring directory
    :param key:         Key to use for signing
    :param passphrase:  Key passphrase
    :param prep:        Iterable containing HTML preprocessors from
                        ``artexin.preprocessors``
    :param meta:        Document extra metadata
    :param base_dir:    Base directory in which to operate
    :param keep_dir:    Keep the directory in which content was collected
    :param javascript:  Whether to execute JavaScript on the page
    :param do_extract:  Whether to perform article extraction
    :returns:           Full path of the newly created zipball
    """
    meta = copy.copy(meta)
    # Common metadata
    meta.update({'url': url,
                 'domain': urlparse.urlparse(url).netloc})
    # Fetch and prepare the HTML
    try:
        if javascript:
            page = fetch_rendered(percent_escape(url))
        else:
            page = fetch_content(url)
    except Exception as err:
        # We will trap any exceptions and return a meta object with 'error' key
        # set to exception object. This won't help debugging a whole lot, but
        # it will give us a peek into what went down. We will also log the
        # exception just in case.
        logging.exception('Error %s while processing %s' % (err, url))
        meta.update({'timestamp': datetime.datetime.utcnow(),
                     'error': str(err)})
        return meta

    timestamp = datetime.datetime.utcnow()

    for preprocessor in prep:
        page = preprocessor(page)

    if do_extract:
        title, html = extract(page)  # FIXME: Handle failure
    else:
        title, html = no_extract(page)

    title = title.strip()
    html = strip_links(html)

    temp_dir = tempfile.mkdtemp()
    # Process images
    html, images = process_images(html, url, imgdir=temp_dir)
    # Write the HTML file
    # FIXME: Handle failure
    html_path = os.path.join(temp_dir, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as html_file:
        html_file.write(html)

    meta.update({'timestamp': timestamp,
                 'title': title,
                 'images': len(images)})

    meta = create_zipball(src_dir=temp_dir,
                          meta=meta,
                          out_dir=base_dir,
                          keep_dir=keep_dir,
                          keyring=keyring,
                          key=key,
                          passphrase=passphrase)
    # Cleanup
    shutil.rmtree(temp_dir)

    return meta


if __name__ == '__main__':
    import doctest
    doctest.testmod()
