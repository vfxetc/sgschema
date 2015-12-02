
class Field(object):

    def __init__(self, entity, name):
        
        self.entity = entity
        self.name = name

        #: Type names allowed for ``entity`` or ``multi_entity`` fields.
        self.allowed_entity_types = set()
        self.data_type = None

        #: Default value of the field; set for ``checkbox``, ``list``, and
        #: ``status_list`` fields.
        self.default_value = None

        #: Allowed values for ``list`` and ``status_list`` fields.
        self.valid_values = None

    def _reduce_raw(self, schema, raw_field):

        self.data_type = raw_field['data_type']['value']
        self.default_value = raw_field['properties']['default_value']['value']

        raw_private = schema.raw_private['entity_fields'][self.entity.name].get(self.name, {})

        if raw_private.get('identifier_column'):
            # It would be nice to add a "name" alias, but that might be
            # a little too magical.
            self.entity.field_aliases['shotgun:name'] = self.name

        if self.data_type in ('entity', 'multi_entity'):
            types_ = raw_private['allowed_entity_types'] or []
            self.allowed_entity_types = set(types_[:])

        elif self.data_type in ('list', 'status_list'):
            self.valid_values = raw_field['properties']['valid_values']['value'][:]

    def _load(self, raw):
        self.allowed_entity_types.update(raw.pop('allowed_entity_types', ()))
        self.data_type = raw.pop('data_type', self.data_type)
        self.default_value = raw.pop('default_value', None)
        self.valid_values = list(raw.pop('valid_values', ()))
        if raw:
            raise ValueError('unknown field keys: %s' % ', '.join(sorted(raw)))

    def _dump(self):
        return dict((k, v) for k, v in (
            ('allowed_entity_types', sorted(self.allowed_entity_types)),
            ('data_type', self.data_type),
            ('default_value', self.default_value),
            ('valid_values', self.valid_values),
        ) if v)

