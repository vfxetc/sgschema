import json
import os
import re

import requests
import yaml



class Schema(object):

    def __init__(self):

        self._raw_fields = None
        self._raw_entities = None
        self._raw_private = None

        self.entities = {}
        self.fields = {}
        self.entity_aliases = {}
        self.field_aliases = {}
        self.field_tags = {}
        

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

            self.entities[type_name] = entity = {}
            for name in ('name', ):
                entity[name] = raw_entity[name]['value']

        for type_name, raw_fields in self._raw_fields.iteritems():

            raw_fields = self._raw_fields[type_name]
            self.fields[type_name] = fields = {}

            for field_name, raw_field in raw_fields.iteritems():

                fields[field_name] = field = {}

                for key in 'name', 'data_type':
                    field[key] = raw_field[key]['value']

                raw_private = self._raw_private['entity_fields'][type_name].get(field_name, {})

                if raw_private.get('identifier_column'):
                    field['identifier_column'] = True
                    self.identifier_columns[type_name] = field_name

                if field['data_type'] in ('entity', 'multi_entity'):
                    types_ = raw_private['allowed_entity_types'] or []
                    field['allowed_entity_types'] = types_[:]

    def _dump_prep(self, value):
        if isinstance(value, unicode):
            return value.encode("utf8")
        elif isinstance(value, dict):
            return {self._dump_prep(k): self._dump_prep(v) for k, v in value.iteritems()}
        elif isinstance(value, (tuple, list)):
            return [self._dump_prep(x) for x in value]
        else:
            return value

    def dump(self, dir_path):
        for name in 'fields', 'entities', 'private':
            value = getattr(self, '_raw_' + name)
            if value:
                with open(os.path.join(dir_path, 'raw_%s.json' % name), 'w') as fh:
                   fh.write(json.dumps(value, indent=4, sort_keys=True))
        for name in ('fields',):
            value = getattr(self, name)
            if value:
                with open(os.path.join(dir_path, name + '.json'), 'w') as fh:
                    fh.write(json.dumps(self._dump_prep(value), indent=4, sort_keys=True))

    def load(self, dir_path, raw=False):
        
        if not raw:
            for name in ('fields', 'entities'):
                path = os.path.join(dir_path, name + '.json')
                if os.path.exists(path):
                    with open(path) as fh:
                        setattr(self, name, json.load(fh))
            if self.fields:
                self._build_associations()

        if raw or not self.fields:
            for name in 'fields', 'entities', 'private':
                path = os.path.join(dir_path, 'raw_%s.json' % name)
                if os.path.exists(path):
                    with open(path) as fh:
                        setattr(self, '_raw_' + name, json.load(fh))
            self._reduce_raw()



if __name__ == '__main__':

    import time
    from shotgun_api3_registry import connect

    sg = connect(use_cache=False)

    schema = Schema()

    if False:
        schema.read(sg)
    else:
        schema.load('sandbox', raw=True)

    schema.dump('sandbox')

    t = time.time()
    schema.load('sandbox')
    print 1000 * (time.time() - t)

