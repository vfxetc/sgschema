from . import *


class TestResolveStructures(TestCase):

    def setUp(self):
        self.s = Schema()
        self.s.load({
            'entities': {
                'Entity': {
                    'fields': {
                        'attr': {},
                        'sg_version': {},
                        'sg_type': {},
                        'name': {},
                        'sg_name': {},
                    },
                    'field_aliases': {
                        'alias': 'attr',
                        'with:namespace': 'attr',
                    },
                    'field_tags': {
                        'tagone': ['attr'],
                        'tagtwo': ['multi_a', 'multi_b'],
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
                '$alias': 'attr_value',
                '#tagtwo': 'xxx',
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

