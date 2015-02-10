# -*- coding: utf-8 -*-


def registered(name):
    registered.handlers[name] = []

    def _registered(func):
        registered.handlers[name].append(func)

        def __registered(*args, **kwargs):
            return func(*args, **kwargs)

        return __registered

    return _registered
registered.handlers = dict()
