# -*- coding: utf-8 -*-
import pkgutil


def discover(package):
    modules = pkgutil.iter_modules(package.__path__)

    for (module_finder, name, ispkg) in modules:
        __import__('.'.join([package.__name__, name]))
