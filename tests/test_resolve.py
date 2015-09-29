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
        self.assertEqual(self.s.resolve_field('Entity', '$missing'), [])
        self.assertEqual(self.s.resolve_field('Entity', '#missing'), [])
        self.assertEqual(self.s.resolve_field('Entity', '!missing'), ['missing'])
        self.assertEqual(self.s.resolve_field('Entity', 'missing'), ['missing'])
        self.assertRaises(ValueError, self.s.resolve_field, 'Entity', 'missing', strict=True)



class TestResolveDeepFields(TestCase):

    def setUp(self):
        self.s = s = load_schema()
        self.s.load({
            'Task': {
                'field_aliases': {
                    'status': 'sg_status_list',
                    'parent': 'entity',
                },
                'field_tags': {
                    'core': ['content', 'step', 'sg_status_list'],
                }
            },
            'Shot': {
                'field_aliases': {
                    'status': 'sg_status_list',
                },
                'field_tags': {
                    'core': ['code', 'description', 'sg_sequence'],
                }
            },

            'Asset': {
                'field_aliases': {
                    'status': 'sg_status_list',
                },
                'field_tags': {
                    'core': ['code', 'asset_type'],
                }
            },
        })

    def test_sanity(self):
        self.assertEqual(self.s.resolve_field('Task', 'sg_status_list'), ['sg_status_list'])
        self.assertEqual(self.s.resolve_field('Task', 'status_list'), ['sg_status_list'])
        self.assertEqual(self.s.resolve_field('Task', '$status'), ['sg_status_list'])

    def test_passthrough(self):
        self.assertEqual(self.s.resolve_field('Task', 'entity.Shot.sg_status_list'), ['entity.Shot.sg_status_list'])

    def test_explicit_aliases(self):
        self.assertEqual(self.s.resolve_field('Task', '$parent.Shot.$status'), ['entity.Shot.sg_status_list'])
        self.assertEqual(self.s.resolve_field('Task', '$parent.Shot.status_list'), ['entity.Shot.sg_status_list'])
        self.assertEqual(self.s.resolve_field('Task', 'entity.Shot.$status'), ['entity.Shot.sg_status_list'])

    def test_explicit_tags(self):
        self.assertEqual(self.s.resolve_field('Task', '$parent.Shot.#core'), ['entity.Shot.sg_sequence', 'entity.Shot.code', 'entity.Shot.description'])



