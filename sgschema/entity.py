from .field import Field
from .utils import cached_property


class Entity(object):
    
    def __init__(self, schema, name):
        
        self.schema = schema
        self.name = name
        
        self.fields = {}

        self._aliases = set()
        self._tags = set()

        self._field_aliases = {}
        self._field_tags = {}

    @cached_property
    def field_aliases(self):
        field_aliases = dict(self._field_aliases)
        for field in self.fields.itervalues():
            for alias in field._aliases:
                field_aliases[alias] = field.name
        return field_aliases

    @cached_property
    def field_tags(self):
        field_tags = {k: set(v) for k, v in self._field_tags.iteritems()}
        for field in self.fields.itervalues():
            for tag in field._tags:
                field_tags.setdefault(tag, set()).add(field.name)
        return field_tags

    @cached_property
    def aliases(self):
        aliases = set(self._aliases)
        for k, v in self.schema._entity_aliases.iteritems():
            if v == self.name:
                aliases.add(k)
        return aliases

    @cached_property
    def tags(self):
        tags = set(self._tags)
        for k, v in self.schema._entity_tags.iteritems():
            if self.name in v:
                tags.add(k)
        return tags

    def _get_or_make_field(self, name):
        try:
            return self.fields[name]
        except KeyError:
            return self.fields.setdefault(name, Field(self, name))

    def _reduce_raw(self, schema, raw_entity):
        pass

    def _load(self, raw):
        for name, value in raw.pop('fields', {}).iteritems():
            self._get_or_make_field(name)._load(value)

        self._field_aliases.update(raw.pop('field_aliases', {}))
        self._field_tags.update(raw.pop('field_tags', {}))

        self._aliases.update(raw.pop('aliases', ()))
        self._tags.update(raw.pop('tags', ()))

        if raw:
            raise ValueError('unknown entity keys: %s' % ', '.join(sorted(raw)))

    def _dump(self):
        return {k: v for k, v in (
            ('fields', {field.name: field._dump() for field in self.fields.itervalues()}),
            ('tags', sorted(self.tags)),
            ('aliases', sorted(self.aliases)),
        ) if v}
