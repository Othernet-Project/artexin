#!/usr/bin/env bash

# runtests.sh: Run doctests found in artexin modules
#
# author: 	Outernet Inc <branko@outernet.is>
# version: 	0.1
#

set -e

cd /vagrant/artexin
/usr/local/bin/nosetests --with-doctest *.py