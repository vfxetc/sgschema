
- Public API:

    Schema.is_variable_len(spec) -> can it return non-one results?

    Schema.resolve_entity(xxx) -> list of entity types
    Schema.resolve_one_entity(xxx) -> one entity type or ValueError

    Schema.resolve_field(entity_type, field_spec) -> list of fields for entity_type
    Schema.resolve_one_field(...) -> one field or ValueError


- Create a standard-ish set of tags and aliases:
    $parent pointing to typical parent

- Include inverse_association (from private schema)


- *type -> explicit prefix matching

- basic key/value metadata store
    - sgactions:ticket_project: 66
