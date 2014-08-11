#!/usr/bin/env python3

"""
pack_standalone.py: Pack standalone content that has no URL

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os
import sys
import json
import time
import hashlib
import datetime
from os.path import dirname as up, abspath, join

from bs4 import BeautifulSoup

sys.path.insert(0, up(up(abspath(__file__))))
sys.path.insert(0, join(up(up(abspath(__file__))), 'artexin'))

from artexin.pack import zipdir
from artexin.extract import get_title
from lib.content_crypto import sign_content

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif',)
KEYRING = '/var/lib/artexin'


def read_title(dest):
    # Read out the title of the file
    with open(join(dest, 'index.html'), 'r') as f:
        soup = BeautifulSoup(f.read())
    return get_title(soup)


def get_hash(url):
    md5 = hashlib.md5()
    md5.update(url.encode('utf=8'))
    return md5.hexdigest()


def is_image(path):
    return os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS


def count_images(dest):
    count = 0
    for base_dir, subdirs, files in os.walk(dest):
        for f in files:
            if is_image(f):
                count += 1
    return count


def get_timestamp(timestamp):
    return timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')


def pack_directory(dest, out, url, keyring, key, passphrase,
                   domain='outernet'):
    title = read_title(dest)
    checksum = get_hash(url)
    timestamp = datetime.datetime.now()

    # Construct metadata
    metadata = {}
    metadata['url'] = '%s/%s' % (domain, url)
    metadata['domain'] = domain
    metadata['images'] = count_images(dest)
    metadata['title'] = read_title(dest)
    metadata['timestamp'] = get_timestamp(timestamp)

    # Write metadata
    with open(os.path.join(dest, 'info.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(metadata, indent=2))

    # Rename directory
    npath = join(up(out), checksum)
    os.rename(dest, npath)
    dest = npath

    # Package the directory
    zippath = os.path.join(out, '%s.zip' % checksum)
    zipdir(zippath, dest)
    signed = sign_content(zippath, keyring, key, passphrase, output_dir=out)
    os.unlink(zippath)
    if not os.path.exists(signed):
            # Python-gnupg will silently fail. It will log a warning, but won't
            # raise any exceptions. The only way to know is to test if the file
            # exists. If the file does not exist, we assume it failed.
            os.unlink(zippath)
    return signed, timestamp, metadata, checksum


if __name__ == '__main__':
    import csv
    import argparse

    parser = argparse.ArgumentParser(description='Package stand-alone content')
    parser.add_argument('--key', metavar='ID', help='ID of the GnuPG key to '
                        'use for signing the content', required=True)
    parser.add_argument('source', metavar='INPUT_DIRECTORY',
                        help='input (content) directory')
    parser.add_argument('out', metavar='OUTPUT_PATH', help='outptu directory',
                        default='.')
    args = parser.parse_args()

    passphrase = input('Key passphrase: ')
    url = input('Enter page identifier (leave empty to use directory name): ')
    url = url or os.path.basename(args.source.strip('/'))
    domain = input("Enter domain (leave empty for 'outernet'): ")
    domain = domain or 'outernet'

    print('Source: %s' % args.source)
    print('URL: %s' % url)
    print('Domain: %s' % domain)

    signed, timestamp, meta, checksum = pack_directory(args.source, args.out,
                                                       url, KEYRING, args.key,
                                                       passphrase, domain)

    size = os.stat(signed).st_size


    report_file = 'report-%s.csv' % (timestamp.strftime('%Y-%m-%d_%H-%M'))

    with open(report_file, 'w', newline='') as f:
        csv = csv.writer(f, delimiter=',', quotechar='"')
        csv.writerow(['url', 'size', 'time', 'hash', 'title', 'image'])
        csv.writerow([meta['url'], size, 0, checksum, meta['title'],
                      meta['images']])

    print("Finished.")

