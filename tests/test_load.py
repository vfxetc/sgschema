import json

from . import *


class TestLoading(TestCase):

    def test_load_entity_tags(self):
        s = Schema()
        s.load({
            'entities': {
                'Entity': {},
            },
            'entity_tags': {
                'X': ['Entity'],
            },
        })
        self.assertIn('Entity', s.entity_tags['X'])

    def test_load_field_tags(self):
        s = Schema()
        s.load({
            'Entity': {
                'fields': {
                    'sg_type': {}
                },
                'field_tags': {
                    'x': ['sg_type'],
                },
            },
        })
        self.assertIn('sg_type', s.entities['Entity'].field_tags['x'])

    def test_load_entity_aliases(self):
        s = Schema()
        s.load({
            'entities': {
                'Entity': {}
            },
            'entity_aliases': {'X': 'Entity'},
        })
        self.assertEqual('Entity', s.entity_aliases['X'])

    def test_load_field_aliases(self):
        s = Schema()
        s.load({
            'Entity': {
                'fields': {
                    'sg_type': {},
                },
                'field_aliases': {
                    'x': 'sg_type',
                },
            },
        })
        self.assertEqual('sg_type', s.entities['Entity'].field_aliases['x'])

    def test_serialize(self):

        raw = {
            'entities': {
                'Entity': {
                    'fields': {
                        'sg_type': {},
                    },
                    'field_aliases': {
                        'x': 'sg_type',
                    },
                },
            },
            'entity_aliases': {
                'Alias': 'Entity',
            },
            'entity_tags': {
                'Tag': ['Entity'],
            },
        }

        schema = Schema()
        schema.load(raw)

        raw2 = json.loads(json.dumps(raw))

        self.assertEqual(raw, raw2)
        