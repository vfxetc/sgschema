from . import *


class TestResolveEntities(TestCase):

    def setUp(self):

        self.s = s = Schema()
        s.load({
            'entities': {
                'Entity': {
                    'aliases': ['A', 'with:Namespace'],
                    'tags': ['X'],
                }
            },
            'entity_aliases': {
                'B': 'Entity',
            },
            'entity_tags': {
                'Y': ['Entity'],
            }
        })

    def test_explicit(self):
        self.assertEqual(self.s.resolve('!Entity'), ['Entity'])
        self.assertEqual(self.s.resolve('$A'), ['Entity'])
        self.assertEqual(self.s.resolve('$B'), ['Entity'])
        self.assertEqual(self.s.resolve('#X'), ['Entity'])
        self.assertEqual(self.s.resolve('#Y'), ['Entity'])

    def test_namespace(self):
        self.assertEqual(self.s.resolve('$with:Namespace'), ['Entity'])

    def test_implicit(self):
        self.assertEqual(self.s.resolve('Entity'), ['Entity'])
        self.assertEqual(self.s.resolve('A'), ['Entity'])
        self.assertEqual(self.s.resolve('B'), ['Entity'])

    def test_missing(self):
        self.assertEqual(self.s.resolve('#Missing'), [])
        self.assertEqual(self.s.resolve('$Missing'), [])
        self.assertEqual(self.s.resolve('!Missing'), ['Missing'])
        self.assertEqual(self.s.resolve('Missing'), ['Missing'])
        self.assertRaises(ValueError, self.s.resolve, 'Missing', strict=True)

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
                        'sg_type': {},
                        'name': {},
                        'sg_name': {},
                    },
                    'field_aliases': {
                        'b': 'attr',
                    },
                    'field_tags': {
                        'y': ['attr'],
                    }
                }
            },
        })

    def test_explicit(self):
        self.assertEqual(self.s.resolve('Entity', '!attr'), ['attr'])
        self.assertEqual(self.s.resolve('Entity', '$a'), ['attr'])
        self.assertEqual(self.s.resolve('Entity', '$b'), ['attr'])
        self.assertEqual(self.s.resolve('Entity', '#x'), ['attr'])
        self.assertEqual(self.s.resolve('Entity', '#y'), ['attr'])

    def test_namespace(self):
        self.assertEqual(self.s.resolve('Entity', '$with:namespace'), ['attr'])
        self.assertEqual(self.s.resolve('Entity', 'with:namespace'), ['attr'])

    def test_implicit(self):
        self.assertEqual(self.s.resolve('Entity', 'attr'), ['attr'])
        self.assertEqual(self.s.resolve('Entity', 'a'), ['attr'])
        self.assertEqual(self.s.resolve('Entity', 'b'), ['attr'])

    def test_prefix(self):
        self.assertEqual(self.s.resolve('Entity', 'sg_type'), ['sg_type'])
        self.assertEqual(self.s.resolve('Entity', 'type'), ['sg_type'])
        self.assertEqual(self.s.resolve('Entity', '!type'), ['type'])

        self.assertEqual(self.s.resolve('Entity', 'sg_name'), ['sg_name'])
        self.assertEqual(self.s.resolve('Entity', 'name'), ['name']) # different!
        self.assertEqual(self.s.resolve('Entity', '!name'), ['name'])

    def test_missing_entity(self):
        self.assertRaises(ValueError, self.s.resolve, 'Missing', 'field_name')

    def test_missing(self):
        self.assertEqual(self.s.resolve('Entity', '$missing'), [])
        self.assertEqual(self.s.resolve('Entity', '#missing'), [])
        self.assertEqual(self.s.resolve('Entity', '!missing'), ['missing'])
        self.assertEqual(self.s.resolve('Entity', 'missing'), ['missing'])
        self.assertRaises(ValueError, self.s.resolve, 'Entity', 'missing', strict=True)

