
- test the loading and resolution of aliases and tags

- caches of the raw schema; both public ones and the private one
- cache of the reduced schema

- role assignments for columns, so that our tools that
  access roles (via a special syntax) instead of actual column names

  e.g.: PublishEvent.$version -> PublishEvent.sg_version_1

  Can have non-alnum in there, e.g.: PublishEvent.$sgpublish:publish:type

- entity type renames, so that we can use custom entities for
  whatever we want, e.g.:

  MyType: CustomEntity02

- Arbitrary tags/meta, e.g. if something is used by sgcache or not.
  
  EntityType.field: sgcache: include: true

  Could we then have xpath like expressions?
  e.g.: EntityType.[sgcache.include==true]
        PublishEvent.[sgpublish.is_core]

  Tags: PublishEvent.#sgsession:core -> {sg_code,sg_type,...}

- Automatic sg_ prefix detection:
  Publish.type -> PublishEvent.sg_type

  Have a "doctor" which tells us the potential problems with our schema,
  such as two columns that are the same minus the prefix

- Force a specific name, to skip the rewriting rules, e.g.: Publish.!type
  This is more in SGSession (or other consumers)


- Public API:

    schema.resolve_entity('$Publish') -> ['PublishEvent']
    schema.resolve_field('PublishEvent', 'type') -> ['sg_type']

- Create a standard-ish set of tags and aliases:
    $parent pointing to typical parent

- Include backrefs in reduced schema? Known as "inverse_association" in private
  schema.























