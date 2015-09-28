import os
from unittest import TestCase

from sgschema import Schema


def load_schema(name='mikeboers', raw=False):
    path = os.path.abspath(os.path.join(__file__, '..', 'schema', name + ('.raw' if raw else '') + '.json'))
    schema = Schema()
    if raw:
        schema.load_raw(path)
    else:
        schema.load(path)
    return schema

