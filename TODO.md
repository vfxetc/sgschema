

- every json file has the same structure, there top-level keys signify what
  type of data it is, e.g. all raw data would be under a "raw_schema_read" field.
  This allows us to merge a directory of cached data, and so that various
  tools can have json files just about them on the SGSCHEMA_PATH, e.g.:

    sgevents.json:

    {
      'entity_aliases': {
        'sgevents:EventReceipt': 'CustomNonProjectEntity01'
      },
      'field_aliases': {
        'CustomNonProjectEntity01': {
          'type': 'sg_type'
        }
      },
      'field_tags': {
        'PublishEvent': {
          'sg_type': ['sgcache:include']
        }
      }
    }

    {
      'PublishEvent': {
        'aliases': ['sgpublish:Publish', 'Publish'],
        'fields': {
          'sg_type': {
            'aliases': ['sgpublish:type', 'type'],
            'data_type': 'text',
            'name': 'Type',
            'tags': ['sgcache:include'],
        }
      }
    }
  }

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

  Tags: PublishEvent.$sgpublish:core -> {sg_code,sg_type,...}

- Automatic sg_ prefix detection:
  Publish.type -> PublishEvent.sg_type

  Have a "doctor" which tells us the potential problems with our schema,
  such as two columns that are the same minus the prefix

- Force a specific name, to skip the rewriting rules, e.g.: Publish.!type
  This is more in SGSession (or other consumers)


- Are tags/alises forward or backward declared?
  
  schema.PublishEvent.aliases = ['Publish']
  vs
  schema.entity_aliases['Publish'] = 'PublishEvent'

  schema.PublishEvent.sg_type.aliases = ['type']
  schema.field_aliases['PublishEvent']['type'] = 'sg_type'
