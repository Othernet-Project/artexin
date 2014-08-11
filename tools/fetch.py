#!/usr/bin/env python3

"""
fetch.py: Fetch specified pages from a text file and zip them up

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import sys
import os
from os.path import dirname as up, abspath, join
import time
import hashlib
import datetime

sys.path.insert(0, up(up(abspath(__file__))))
sys.path.insert(0, join(up(up(abspath(__file__))), 'artexin'))

from artexin.pack import collect
from artexin.preprocessor_mappings import get_preps

FAILLOG = 'failed.urls'
LOG = 'report-%s.csv' % datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
KEYRING = '/var/lib/artexin'



def hash_url(url):
    md5 = hashlib.md5()
    md5.update(bytes(url, 'utf-8'))
    return md5.hexdigest()


def isdone(url, path):
    return os.path.exists(join(path, '%s.sig' % hash_url(url)))


def fetch_and_zip(page, key, passphrase, out, javascript=True,
                  do_extract=True):
    start = time.time()
    meta = collect(page, keyring=KEYRING, key=key, passphrase=passphrase,
                   prep=get_preps(page), base_dir=out, javascript=javascript,
                   do_extract=do_extract)
    took = time.time() - start
    print('Took %s seconds' % (took))
    return took, meta


if __name__ == '__main__':
    import argparse
    import urllib
    import csv

    parser = argparse.ArgumentParser(description='Outernet content '
                                     'preparation script')
    parser.add_argument('--key', metavar='ID', help='ID of the GnuPG key to '
                        'use for signing the content', required=True)
    parser.add_argument('urllist', metavar='PATH', help='path to the file '
                        'containing a list of URLs (once URL per line)')
    parser.add_argument('--out', metavar='PATH', help='output directory '
                        '(default is /vagrant)', default='/vagrant')
    parser.add_argument('--no-js', help='do not execute any JavaScript',
                        action='store_false')
    parser.add_argument('--verbatim', help='do not perform article extraction',
                        action='store_false')
    parser.add_argument('--debug', help='raise all exceptions',
                        action='store_true')
    args = parser.parse_args()

    passphrase = input('Key passphrase: ')
    pfile = args.urllist
    with open(pfile, 'r') as ulist:
        urllist = [u.strip() for u in ulist.read().split('\n')
                   if u.strip() != '']

    faillog = open(FAILLOG, 'w')
    oklog = open(LOG, 'w', newline='')
    report = csv.writer(oklog, delimiter=',', quotechar='"')
    processed = []
    count = 1

    start = time.time()
    report.writerow(['url', 'size', 'time', 'hash', 'title', 'images'])

    for url in urllist:
        print("Processing '%s' (%s/%s)" % (url, count, len(urllist)))
        count += 1

        if url in processed:
            print("Duplicate URL '%s', skipping" % url)
            continue

        if isdone(url, args.out):
            print("Already finished '%s', skipping" % url)
            continue

        # Check URL
        try:
            urllib.request.urlopen(url)
        except Exception as e:
            print("Error processing '%s': %s" % (url, e))
            faillog.write(url + '\n')
            if args.debug:
                raise
            continue

        # Fetch and zip
        try:
            took, meta = fetch_and_zip(url, args.key, passphrase, args.out,
                                       javascript=bool(args.no_js),
                                       do_extract=bool(args.verbatim))
        except Exception as e:
            print("Error processing '%s': %s" % (url, e))
            faillog.write(url + '\n')
            if args.debug:
                raise
            continue

        error = meta.get('error')

        if error is not None:
            print("Error processing '%s': %s" % (url, error))
            faillog.write(url + '\n')
            continue

        # Write metadata to CSV file
        report.writerow([url, meta['size'], took, meta['hash'], meta['title'],
                         meta['images']])
        processed.append(url)

    end = time.time() - start
    report.writerow(['time taken:', round(end, 2)])

    faillog.close()
    oklog.close()

    print("Total time taken: %s seconds" % round(end, 2))
    print("Total URLs successfully packaged: %s" % len(processed))

