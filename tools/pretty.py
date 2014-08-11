#!/usr/bin/env python3

import sys
import bs4

source = sys.argv[1]

try:
    with open(source, 'r', encoding='utf-8') as f:
        soup = bs4.BeautifulSoup(f.read())
except Exception:
    with open(source, 'r', encoding='latin1') as f:
        soup = bs4.BeautifulSoup(f.read())

with open(source, 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
