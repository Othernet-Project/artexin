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

SRCDIR=/vagrant

cd $SRCDIR
PYTHONPATH=$SRCDIR py.test --doctest-modules artexin tests
