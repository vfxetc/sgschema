from .utils import cached_property

class Field(dict):

    def __init__(self, entity, name):
        
        self.entity = entity
        self.name = name

        self.allowed_entity_types = set()
        self.data_type = None

        self._aliases = set()
        self._tags = set()

    @cached_property
    def aliases(self):
        aliases = set(self._aliases)
        for k, v in self.entity._field_aliases.iteritems():
            if v == self.name:
                aliases.add(k)
        return aliases

    @cached_property
    def tags(self):
        tags = set(self._tags)
        for k, v in self.entity._field_tags.iteritems():
            if self.name in v:
                tags.add(k)
        return tags

    def _reduce_raw(self, schema, raw_field):

        self.data_type = raw_field['data_type']['value']

        raw_private = schema._raw_private['entity_fields'][self.entity.name].get(self.name, {})

        if raw_private.get('identifier_column'):
            # It would be nice to add a "name" alias, but that might be
            # a little too magical.
            self._aliases.add('shotgun:name')

        if self.data_type in ('entity', 'multi_entity'):
            types_ = raw_private['allowed_entity_types'] or []
            self.allowed_entity_types = set(types_[:])

    def _load(self, raw):
        self.allowed_entity_types.update(raw.pop('allowed_entity_types', ()))
        self.data_type = raw.pop('data_type', self.data_type)
        self._aliases.update(raw.pop('aliases', ()))
        self._tags.update(raw.pop('tags', ()))
        if raw:
            raise ValueError('unknown field tags: %s' % ', '.join(sorted(raw)))

    def _dump(self):
        return {k: v for k, v in (
            ('aliases', sorted(self.aliases)),
            ('allowed_entity_types', sorted(self.allowed_entity_types)),
            ('data_type', self.data_type),
            ('tags', sorted(self.tags)),
        ) if v}

