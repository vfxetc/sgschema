from . import *


class TestResolveEntities(TestCase):

    def setUp(self):

        self.s = s = Schema()
        s.load({
            'entities': {
                'Entity': {
                    'aliases': ['A', 'with:Namespace'],
                    'tags': ['X'],
                },
                'Another': {}
            },
            'entity_aliases': {
                'B': 'Entity',
            },
            'entity_tags': {
                'Y': ['Entity'],
                'Multiple': ['Entity', 'Another'],
            }
        })

    def test_explicit(self):
        self.assertEqual(self.s.resolve_entity('!Entity'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('$A'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('$B'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('#X'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('#Y'), ['Entity'])

    def test_namespace(self):
        self.assertEqual(self.s.resolve_entity('$with:Namespace'), ['Entity'])

    def test_implicit(self):
        self.assertEqual(self.s.resolve_entity('Entity'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('A'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('B'), ['Entity'])

    def test_missing(self):
        self.assertEqual(self.s.resolve_entity('#Missing'), [])
        self.assertEqual(self.s.resolve_entity('$Missing'), [])
        self.assertEqual(self.s.resolve_entity('!Missing'), ['Missing'])
        self.assertEqual(self.s.resolve_entity('Missing'), ['Missing'])
        self.assertRaises(ValueError, self.s.resolve_entity, 'Missing', strict=True)

    def test_one(self):
        self.assertEqual(self.s.resolve_one_entity('Entity'), 'Entity')
        self.assertEqual(self.s.resolve_one_entity('!Entity'), 'Entity')
        self.assertEqual(self.s.resolve_one_entity('$A'), 'Entity')
        self.assertEqual(self.s.resolve_one_entity('#X'), 'Entity')
        self.assertRaises(ValueError, self.s.resolve_one_entity, '#Missing')
        self.assertRaises(ValueError, self.s.resolve_one_entity, '#Multiple')