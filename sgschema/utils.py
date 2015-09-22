

class cached_property(object):

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        try:
            return obj.__dict__[self.__name__]
        except KeyError:
            obj.__dict__[self.__name__] = value = self.func(obj)
            return value


def merge_update(dst, src):

    for k, v in src.iteritems():

        if k not in dst:
            dst[k] = v
            continue

        e = dst[k]
        if isinstance(e, dict):
            merge_update(e, v)
        elif isinstance(e, list):
            e.extend(v)
        else:
            dst[k] = v

