import collections
import functools
import importlib
import pkgutil
import re

CMD_HANDLERS = collections.defaultdict(dict)
RE_HANDLERS = collections.defaultdict(lambda: collections.defaultdict(list))


def cmd(name, callback=None):
    if callback is None:
        return functools.partial(cmd, name)
    CMD_HANDLERS[callback.__module__][name] = callback
    return callback


def regex(pattern, callback=None):
    if callback is None:
        return functools.partial(regex, pattern)
    pattern = re.compile(pattern)
    RE_HANDLERS[callback.__module__][pattern].append(callback)
    return callback


def discover_builtins():
    import nnc.ext as builtins_pkg

    path = builtins_pkg.__path__
    pkg_prefix = builtins_pkg.__package__ + '.'

    for mod in pkgutil.iter_modules(path, pkg_prefix):
        yield importlib.import_module(mod.name)
