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

    def test_recursion(self):

        entity = {
            'type': 'Entity',
            'version': 1
        }
        entity['self'] = entity

        out = self.s.resolve_structure([entity, entity])

        # Both items are the same entity.
        self.assertEqual(len(out), 2)
        entity = out[0]
        self.assertIs(entity, out[1])

        # It contains itself.
        self.assertIs(entity, entity['self'])
        
        entity.pop('self') # just remove it for comparison

        # Simple values.
        self.assertEqual(entity, {
            'type': 'Entity',
            'sg_version': 1,
        })



