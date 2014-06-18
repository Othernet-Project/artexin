#!/usr/bin/env bash

# start: Run the web application
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

PY=python3
SRCDIR="/vagrant"
WEBAPP="$SRCDIR/artexin_webui"
APPMOD="$WEBAPP/app.py"

cd $SRCDIR
PYTHONPATH=$SRCDIR $PY $APPMOD --debug --server=cherrypy --cdir=/vagrant
