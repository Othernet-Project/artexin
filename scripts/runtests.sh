#!/usr/bin/env bash

# runtests.sh: Run doctests found in artexin modules
#
# author: 	Outernet Inc <branko@outernet.is>
# version: 	0.1
#
# Copyright 2014, Outernet Inc.
# Some rights reserved.
# 
# This software is free software licensed under the terms of GPLv3. See COPYING
# file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
#

START=/vagrant
PKG="$START/artexin"

cd $PKG
/usr/local/bin/nosetests --with-doctest --doctest-options='+ELLIPSIS,+IGNORE_EXCEPTION_DETAIL' *.py

