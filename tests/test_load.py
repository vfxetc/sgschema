from . import *


class TestLoading(TestCase):

    def test_load_entity_tags(self):

        s = Schema()
        s.load({
            'entities': {'Entity': {
                'tags': ['a'],
            }},
            'entity_tags': {'b': ['Entity']},
        })

        self.assertIn('a', s.entities['Entity'].tags)
        self.assertIn('b', s.entities['Entity'].tags)
        self.assertIn('Entity', s.entity_tags['a'])
        self.assertIn('Entity', s.entity_tags['b'])

    def test_load_field_tags(self):

        s = Schema()
        s.load({
            'Entity': {
                'fields': {
                    'sg_type': {
                        'tags': ['a'],
                    },
                },
                'field_tags': {
                    'b': ['sg_type'],
                },
            },
        })

        self.assertIn('a', s.entities['Entity'].fields['sg_type'].tags)
        self.assertIn('b', s.entities['Entity'].fields['sg_type'].tags)
        self.assertIn('sg_type', s.entities['Entity'].field_tags['a'])
        self.assertIn('sg_type', s.entities['Entity'].field_tags['b'])

    def test_load_entity_aliases(self):

        s = Schema()
        s.load({
            'entities': {'Entity': {
                'aliases': ['A'],
            }},
            'entity_aliases': {'B': 'Entity'},
        })

        self.assertIn('A', s.entities['Entity'].aliases)
        self.assertIn('B', s.entities['Entity'].aliases)
        self.assertEqual('Entity', s.entity_aliases['A'])
        self.assertEqual('Entity', s.entity_aliases['B'])

    def test_load_field_aliases(self):

        s = Schema()
        s.load({
            'Entity': {
                'fields': {
                    'sg_type': {
                        'aliases': ['a'],
                    },
                },
                'field_aliases': {
                    'b': 'sg_type',
                },
            },
        })

        self.assertIn('a', s.entities['Entity'].fields['sg_type'].aliases)
        self.assertIn('b', s.entities['Entity'].fields['sg_type'].aliases)
        self.assertEqual('sg_type', s.entities['Entity'].field_aliases['a'])
        self.assertEqual('sg_type', s.entities['Entity'].field_aliases['b'])

