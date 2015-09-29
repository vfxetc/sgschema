import copy
import itertools
import json
import os
import re

from .entity import Entity
from .field import Field
from .utils import cached_property, merge_update


class Schema(object):

    _cache_instances = {}

    @classmethod
    def from_cache(cls, base_url):

        # If it is a Shotgun instance, grab the url.
        if not isinstance(base_url, basestring):
            base_url = base_url.base_url

        # Try to return a single instance.
        try:
            return cls._cache_instances[base_url]
        except KeyError:
            pass

        import pkg_resources
        for ep in pkg_resources.iter_entry_points('sgschema_cache'):
            func = ep.load()
            cache = func(base_url)
            if cache is not None:
                break
        else:
            raise ValueError('cannot find cache for %s' % base_url)

        schema = cls()
        schema.load(cache)

        # Cache it so we only load it once.
        cls._cache_instances[base_url] = schema
        return schema

    def __init__(self):

        self._raw_fields = None
        self._raw_entities = None
        self._raw_private = None

        self.entities = {}

        self._entity_aliases = {}
        self._entity_tags = {}

    @cached_property
    def entity_aliases(self):
        entity_aliases = dict(self._entity_aliases)
        for entity in self.entities.itervalues():
            for alias in entity._aliases:
                entity_aliases[alias] = entity.name
        return entity_aliases

    @cached_property
    def entity_tags(self):
        entity_tags = {k: set(v) for k, v in self._entity_tags.iteritems()}
        for entity in self.entities.itervalues():
            for tag in entity._tags:
                entity_tags.setdefault(tag, set()).add(entity.name)
        return entity_tags

    def _get_or_make_entity(self, name):
        try:
            return self.entities[name]
        except KeyError:
            return self.entities.setdefault(name, Entity(self, name))

    def read(self, sg):
        
        # Most of the time we don't need this, so don't bother importing.
        from requests import Session

        # SG.schema_field_read() is the same data per-entity as SG.schema_read().
        # SG.schema_entity_read() contains global name and visibility of each
        # entity type, but the visibility is likely to just be True for everything.
        self._raw_fields = sg.schema_read()
        self._raw_entities = sg.schema_entity_read()

        # We also want the private schema which drives the website.
        # See <http://mikeboers.com/blog/2015/07/21/a-complete-shotgun-schema>.

        session = Session()
        session.cookies['_session_id'] = sg.get_session_token()
        
        js = session.get(sg.base_url + '/page/schema').text
        encoded = js.splitlines()[0]
        m = re.match(r'^SG\.schema = new SG\.Schema\((.+)\);\s*$', encoded)
        if not m:
            raise ValueError('schema does not appear to be at %s/page/schema' % sg.base_url)

        self._raw_private = json.loads(m.group(1))

        self._reduce_raw()

    def _reduce_raw(self):
        
        for type_name, raw_entity in self._raw_entities.iteritems():
            entity = self._get_or_make_entity(type_name)
            entity._reduce_raw(self, raw_entity)

        for type_name, raw_fields in self._raw_fields.iteritems():
            entity = self._get_or_make_entity(type_name)
            for field_name, raw_field in raw_fields.iteritems():
                field = entity._get_or_make_field(field_name)
                field._reduce_raw(self, raw_field)

    def dump(self, path, raw=False):
        if raw:
            with open(path, 'w') as fh:
                fh.write(json.dumps({
                    'raw_fields': self._raw_fields,
                    'raw_entities': self._raw_entities,
                    'raw_private': self._raw_private,
                }, indent=4, sort_keys=True))
        else:
            data = {'entities': {entity.name: entity._dump() for entity in self.entities.itervalues()}}
            with open(path, 'w') as fh:
                fh.write(json.dumps(data, indent=4, sort_keys=True))

    def load_directory(self, dir_path):
        for file_name in os.listdir(dir_path):
            if file_name.startswith('.') or not file_name.endswith('.json'):
                continue
            self.load(os.path.join(dir_path, file_name))

    def load_raw(self, path):

        raw = json.loads(open(path).read())
        keys = 'raw_entities', 'raw_fields', 'raw_private'

        # Make sure we have the right keys, and only the right keys.
        missing = [k for k in keys if k not in raw]
        if missing:
            raise ValueError('missing keys in raw schema: %s' % ', '.join(missing))
        if len(keys) != 3:
            extra = [k for k in raw if k not in keys]
            raise ValueError('extra keys in raw schema: %s' % ', '.join(extra))

        for k in keys:
            setattr(self, '_' + k, raw[k])

        self._reduce_raw()

    def load(self, input_):

        if isinstance(input_, basestring):
            encoded = open(input_).read()
            raw_schema = json.loads(encoded)
        elif isinstance(input_, dict):
            raw_schema = copy.deepcopy(input_)
        else:
            raise TypeError('require str path or dict schema')

        # If it is a dictionary of entity types, pretend it is in an "entities" key.
        title_cased = sum(int(k[:1].isupper()) for k in raw_schema)
        if title_cased:
            if len(raw_schema) != title_cased:
                raise ValueError('mix of direct and indirect entity specifications')
            raw_schema = {'entities': raw_schema}

        for type_name, value in raw_schema.pop('entities', {}).iteritems():
            self._get_or_make_entity(type_name)._load(value)

        merge_update(self._entity_aliases, raw_schema.pop('entity_aliases', {}))
        merge_update(self._entity_tags   , raw_schema.pop('entity_tags',    {}))

        if raw_schema:
            raise ValueError('unknown keys: %s' % ', '.join(sorted(raw_schema)))

    def resolve_entity(self, entity_spec, implicit_aliases=True, strict=False):

        op = entity_spec[0]
        if op == '!':
            return [entity_spec[1:]]
        if op == '#':
            return list(self.entity_tags.get(entity_spec[1:], ()))
        if op == '$':
            try:
                return [self.entity_aliases[entity_spec[1:]]]
            except KeyError:
                return []
        if not op.isalnum():
            raise ValueError('unknown entity operation for %r' % entity_spec)

        # Actual entity names have preference over implicit aliases.
        if entity_spec in self.entities:
            return [entity_spec]

        if implicit_aliases and entity_spec in self.entity_aliases:
            return [self.entity_aliases[entity_spec]]

        if strict:
            raise ValueError('%r is not an entity type' % entity_spec)

        return [entity_spec]

    def resolve_one_entity(self, entity_spec, **kwargs):
        res = self.resolve_entity(entity_spec, **kwargs)
        if len(res) == 1:
            return res[0]
        else:
            raise ValueError('%r returned %s entity types' % (entity_spec, len(res)))

    def _resolve_field(self, entity_spec, field_spec, auto_prefix=True, implicit_aliases=True, strict=False):

        try:
            entity = self.entities[entity_spec]
        except KeyError:
            raise ValueError('%r is not an entity type' % entity_spec)

        # These two are special, and should always be returned as-is.
        # We only need to do "type" in this way, since "id" usually exists
        # as a numeric field, but it feels right.
        if field_spec in ('id', 'type'):
            return [field_spec]

        op = field_spec[0]
        if op == '!':
            return [field_spec[1:]]
        if op == '#':
            return list(entity.field_tags.get(field_spec[1:], ()))
        if op == '$':
            try:
                return [entity.field_aliases[field_spec[1:]]]
            except KeyError:
                return []
        if not op.isalnum():
            raise ValueError('unknown field operation for %s %r' % (entity_spec, field_spec))

        # Actual field names have preference over automatic prefixes or
        # implicit aliases.
        if field_spec in entity.fields:
            return [field_spec]

        if auto_prefix:
            prefixed = 'sg_' + field_spec
            if prefixed in entity.fields:
                return [prefixed]

        if implicit_aliases and field_spec in entity.field_aliases:
            return [entity.field_aliases[field_spec]]

        if strict:
            raise ValueError('%r is not a field of %s' % (field_spec, entity_spec))

        return [field_spec]

    def resolve_field(self, entity_type, field_spec=None, auto_prefix=True, implicit_aliases=True, strict=False):

        spec_parts = field_spec.split('.')

        # Shortcut if there isn't anything fancy going on.
        if len(spec_parts) == 1:
            return self._resolve_field(entity_type, field_spec, auto_prefix, implicit_aliases, strict)

        # Crate list of [entity_type, field_spec] pairs.
        spec_pairs = [[spec_parts[i-1] if i else None, spec_parts[i]] for i in xrange(0, len(spec_parts), 2)]
        spec_pairs[0][0] = entity_type

        # Resolve each pair.
        resolved_pair_sets = []
        for i, (entity_spec, field_spec), in enumerate(spec_pairs):
            resolved_pairs = []
            resolved_pair_sets.append(resolved_pairs)
            # Here entity types need not already exist; resolve them.
            entity_types = self.resolve_entity(entity_spec, implicit_aliases, strict)
            for entity_type in entity_types:
                for field_name in self._resolve_field(entity_type, field_spec, auto_prefix, implicit_aliases, strict):
                    resolved_pairs.append((entity_type, field_name))

        # Return the product of all resolved fields.
        resolved_fields = []
        for pairs in itertools.product(*resolved_pair_sets):
            field = '.'.join((entity_type + '.' if i else '') + field_name for i, (entity_type, field_name) in enumerate(pairs))
            resolved_fields.append(field)
        return resolved_fields











if __name__ == '__main__':

    import time
    from shotgun_api3_registry import connect

    sg = connect(use_cache=False)

    schema = Schema()

    if False:
        schema.read(sg)
        schema.dump('sandbox/raw.json', raw=True)
    else:
        schema.load_raw('sandbox/raw.json')

    schema.dump('sandbox/reduced.json')
    schema.dump('/tmp/reduced.json')

    t = time.time()
    schema = Schema()
    schema.load('/tmp/reduced.json')
    print 1000 * (time.time() - t)

