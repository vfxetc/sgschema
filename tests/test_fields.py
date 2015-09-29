from . import *


class TestResolveFields(TestCase):

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
                        'multi': ['multi_a', 'multi_b'],
                    }
                }
            },
        })

    def test_explicit(self):
        self.assertEqual(self.s.resolve_field('Entity', '!attr'), ['attr'])
        self.assertEqual(self.s.resolve_field('Entity', '$a'), ['attr'])
        self.assertEqual(self.s.resolve_field('Entity', '$b'), ['attr'])
        self.assertEqual(self.s.resolve_field('Entity', '#x'), ['attr'])
        self.assertEqual(self.s.resolve_field('Entity', '#y'), ['attr'])

    def test_namespace(self):
        self.assertEqual(self.s.resolve_field('Entity', '$with:namespace'), ['attr'])
        self.assertEqual(self.s.resolve_field('Entity', 'with:namespace'), ['attr'])

    def test_implicit(self):
        self.assertEqual(self.s.resolve_field('Entity', 'attr'), ['attr'])
        self.assertEqual(self.s.resolve_field('Entity', 'a'), ['attr'])
        self.assertEqual(self.s.resolve_field('Entity', 'b'), ['attr'])

    def test_prefix(self):
        self.assertEqual(self.s.resolve_field('Entity', 'sg_version'), ['sg_version'])
        self.assertEqual(self.s.resolve_field('Entity', 'version'), ['sg_version']) # Auto-prefix.
        self.assertEqual(self.s.resolve_field('Entity', '!version'), ['version']) # Doesn't exist.

        self.assertEqual(self.s.resolve_field('Entity', 'sg_type'), ['sg_type'])
        self.assertEqual(self.s.resolve_field('Entity', 'type'), ['type']) # This overlaps the implicit "type"!
        self.assertEqual(self.s.resolve_field('Entity', '!type'), ['type'])

        self.assertEqual(self.s.resolve_field('Entity', 'sg_name'), ['sg_name'])
        self.assertEqual(self.s.resolve_field('Entity', 'name'), ['name']) # different!
        self.assertEqual(self.s.resolve_field('Entity', '!name'), ['name'])

    def test_missing_entity(self):
        self.assertRaises(ValueError, self.s.resolve_field, 'Missing', 'field_name')

    def test_missing(self):
        self.assertEqual(self.s.resolve_field('Entity', '$missing'), ['$missing'])
        self.assertEqual(self.s.resolve_field('Entity', '#missing'), [])
        self.assertEqual(self.s.resolve_field('Entity', '!missing'), ['missing'])
        self.assertEqual(self.s.resolve_field('Entity', 'missing'), ['missing'])
        self.assertRaises(ValueError, self.s.resolve_field, 'Entity', 'missing', strict=True)

    def test_one(self):
        self.assertEqual(self.s.resolve_one_field('Entity', 'sg_type'), 'sg_type')
        self.assertEqual(self.s.resolve_one_field('Entity', '$a'), 'attr')
        self.assertEqual(self.s.resolve_one_field('Entity', '#x'), 'attr')
        self.assertRaises(ValueError, self.s.resolve_one_field, 'Entity', '#missing')
        self.assertRaises(ValueError, self.s.resolve_one_field, 'Entity', '#multi')

    def test_many(self):
        self.assertEqual(self.s.resolve_field('Entity', ['sg_type', 'version', '#x', '#multi']), [
            'sg_type', 'sg_version', 'attr', 'multi_a', 'multi_b',
        ])

