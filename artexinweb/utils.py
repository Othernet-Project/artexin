# -*- coding: utf-8 -*-
import hashlib
import pkgutil


def discover(package):
    modules = pkgutil.iter_modules(package.__path__)

    for (module_finder, name, ispkg) in modules:
        __import__('.'.join([package.__name__, name]))


def hash_data(*args):
    md5 = hashlib.md5()

    for data in args:
        md5.update(bytes(str(data), 'utf-8'))

    return md5.hexdigest()
