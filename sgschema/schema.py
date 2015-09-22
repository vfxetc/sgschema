import ast
import json
import os
import re
import copy

import requests
import yaml

from .entity import Entity
from .field import Field
from .utils import cached_property, merge_update


class Schema(object):

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
        
        # SG.schema_field_read() is the same data per-entity as SG.schema_read().
        # SG.schema_entity_read() contains global name and visibility of each
        # entity type, but the visibility is likely to just be True for everything.
        self._raw_fields = sg.schema_read()
        self._raw_entities = sg.schema_entity_read()

        # We also want the private schema which drives the website.
        # See <http://mikeboers.com/blog/2015/07/21/a-complete-shotgun-schema>.

        session = requests.Session()
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
            data = {entity.name: entity._dump() for entity in self.entities.itervalues()}
            with open(path, 'w') as fh:
                fh.write(json.dumps(data, indent=4, sort_keys=True))

    def load_directory(self, dir_path):
        for file_name in os.listdir(dir_path):
            if file_name.startswith('.') or not file_name.endswith('.json'):
                continue
            self.load(self, os.path.join(dir_path, file_name))

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

        # Load the two direct fields.
        for type_name, value in raw_schema.pop('entities', {}).iteritems():
            self._get_or_make_entity(type_name)._load(value)

        merge_update(self._entity_aliases, raw_schema.pop('entity_aliases', {}))
        merge_update(self._entity_tags   , raw_schema.pop('entity_tags',    {}))

        if raw_schema:
            raise ValueError('unknown keys: %s' % ', '.join(sorted(raw_schema)))
        return

        # Load any indirect fields.
        for key, values in raw_schema.iteritems():
            if key.startswith('entity_'):
                entity_attr = key[7:]
                for type_name, value in values.iteritems():
                    self.entities[type_name]._load({entity_attr: value})
            elif key.startswith('field_'):
                field_attr = key[6:]
                for type_name, fields in values.iteritems():
                    for field_name, value in fields.iteritems():
                        self.entities[type_name].fields[field_name]._load({field_attr: value})
            else:
                raise ValueError('unknown complex field %s' % key)

    def resolve(self, entity_spec, field_spec=None, auto_prefix=True, implicit_aliases=True, strict=False):

        if field_spec is None: # We are resolving an entity.

            m = re.match(r'^([!#$]?)([\w:-]+)$', entity_spec)
            if not m:
                raise ValueError('%r cannot be an entity' % entity_spec)
            operation, entity_spec = m.groups()

            if operation == '!':
                return [entity_spec]
            if operation == '#':
                return list(self.entity_tags.get(entity_spec, ()))
            if operation == '$':
                try:
                    return [self.entity_aliases[entity_spec]]
                except KeyError:
                    return []

            if entity_spec in self.entities:
                return [entity_spec]

            if implicit_aliases and entity_spec in self.entity_aliases:
                return [self.entity_aliases[entity_spec]]

            if strict:
                raise ValueError('%r is not an entity' % entity_spec)

            return [entity_spec]

        # When resolving a field, the entity must exist.
        try:
            entity = self.entities[entity_spec]
        except KeyError:
            raise ValueError('%r is not an entity' % entity_spec)

        m = re.match(r'^([!#$]?)([\w:-]+)$', field_spec)
        if not m:
            raise ValueError('%r cannot be a field' % field_spec)
        operation, field_spec = m.groups()

        if operation == '!':
            return [field_spec]
        if operation == '#':
            return list(entity.field_tags.get(field_spec, ()))
        if operation == '$':
            try:
                return [entity.field_aliases[field_spec]]
            except KeyError:
                return []

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

    schema.entities['PublishEvent'].aliases.add('Publish')
    schema.entities['PublishEvent'].aliases.add('sgpublish:Publish')
    schema.entities['PublishEvent'].fields['sg_type'].aliases.add('type')
    schema.entities['PublishEvent'].fields['sg_type'].tags.add('sgcache:include')

    schema.dump('sandbox/reduced.json')

    t = time.time()
    schema = Schema()
    schema.load('sandbox/reduced.json')
    print 1000 * (time.time() - t)

    print schema.entity_aliases['Publish']
    print schema.entities['PublishEvent'].field_aliases['type']
    print schema.entities['PublishEvent'].field_tags['identifier_column']
