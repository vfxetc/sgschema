from . import *


class TestResolveEntities(TestCase):

    def setUp(self):
        self.s = s = Schema()
        s.load({
            'entities': {
                'Entity': {},
                'Another': {},
            },
            'entity_aliases': {
                'Alias': 'Entity',
                'with:Namespace': 'Entity',
            },
            'entity_tags': {
                'TagOne': ['Entity'],
                'TagTwo': ['Entity', 'Another'],
            }
        })

    def test_explicit(self):
        self.assertEqual(self.s.resolve_entity('!Entity'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('$Alias'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('#TagOne'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('#TagTwo'), ['Entity', 'Another'])

    def test_namespace(self):
        self.assertEqual(self.s.resolve_entity('$with:Namespace'), ['Entity'])

    def test_implicit(self):
        self.assertEqual(self.s.resolve_entity('Entity'), ['Entity'])
        self.assertEqual(self.s.resolve_entity('Alias'), ['Entity'])

    def test_missing(self):
        self.assertEqual(self.s.resolve_entity('#Missing'), [])
        self.assertEqual(self.s.resolve_entity('$Missing'), [])
        self.assertEqual(self.s.resolve_entity('!Missing'), ['Missing'])
        self.assertEqual(self.s.resolve_entity('Missing'), ['Missing'])
        self.assertRaises(ValueError, self.s.resolve_entity, 'Missing', strict=True)

    def test_one(self):
        self.assertEqual(self.s.resolve_one_entity('Entity'), 'Entity')
        self.assertEqual(self.s.resolve_one_entity('!Entity'), 'Entity')
        self.assertEqual(self.s.resolve_one_entity('$Alias'), 'Entity')
        self.assertEqual(self.s.resolve_one_entity('#TagOne'), 'Entity')
        self.assertRaises(ValueError, self.s.resolve_one_entity, '#TagNone')
        self.assertRaises(ValueError, self.s.resolve_one_entity, '#TagTwo')

    def test_has_entity(self):
        self.assertTrue(self.s.has_entity('Entity'))
        self.assertTrue(self.s.has_entity('!Entity'))
        self.assertTrue(self.s.has_entity('$Alias'))
        self.assertTrue(self.s.has_entity('#TagOne'))
        self.assertFalse(self.s.has_entity('NotAnEntity'))
        self.assertFalse(self.s.has_entity('#TagNone'))
