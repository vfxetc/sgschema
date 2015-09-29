from . import *


class TestResolveStructures(TestCase):

    def setUp(self):

        self.s = s = Schema()
        s.load({
            'entities': {
                'Entity': {
                    'fields': {
                        'attr': {
                            'aliases': ['a', 'with:namespace'],
                            'tags': ['x'],

                        },
                        'sg_version': {},
                        'sg_type': {},
                        'name': {},
                        'sg_name': {},
                    },
                    'field_aliases': {
                        'b': 'attr',
                    },
                    'field_tags': {
                        'y': ['attr'],
                        'multi': ['multi_a', 'multi_b']
                    }
                }
            },
        })

    def test_single_entity(self):
        self.assertEqual(self.s.resolve_structure({
            'type': 'Entity',
            'version': 1
        }), {
            'type': 'Entity',
            'sg_version': 1,
        })

    def test_entity_list(self):
        self.assertEqual(self.s.resolve_structure([
            {
                'type': 'Entity',
                'version': 1
            },
            {
                'type': 'Entity',
                '$b': 'attr_value',
                '#multi': 'xxx',
            }
        ]), [
            {
                'type': 'Entity',
                'sg_version': 1,
            },
            {
                'type': 'Entity',
                'attr': 'attr_value',
                'multi_a': 'xxx',
                'multi_b': 'xxx',
            }
        ])

