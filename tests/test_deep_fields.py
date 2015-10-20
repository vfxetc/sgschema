from . import *


class TestResolveDeepFields(TestCase):

    def setUp(self):
        self.s = s = Schema()
        self.s.load({
            'Task': {
                'fields': {
                    'sg_status_list': {},
                },
                'field_aliases': {
                    'status': 'sg_status_list',
                    'parent': 'entity',
                },
                'field_tags': {
                    'core': ['content', 'step', 'sg_status_list'],
                }
            },
            'Shot': {
                'fields': {
                    'sg_status_list': {},
                },
                'field_aliases': {
                    'status': 'sg_status_list',
                },
                'field_tags': {
                    'core': ['code', 'description', 'sg_sequence'],
                }
            },

            'Asset': {
                'fields': {
                    'sg_status_list': {},
                },
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
        self.assertEqual(self.s.resolve_field('Task', '$parent.Shot.#core'), ['entity.Shot.code', 'entity.Shot.description', 'entity.Shot.sg_sequence'])



