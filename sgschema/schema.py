import copy
import itertools
import json
import os
import re

from .entity import Entity
from .field import Field
from .utils import merge_update


class Schema(object):

    _cache_instances = {}

    @classmethod
    def from_cache(cls, base_url):
        """Use setuptools' entry points to load a cached schema.

        Calls functions registered to "sgschema_cache", passing them a
        ``Schema`` instance and the base URL, giving them the oppourtunity
        to load from their caches.

        If a function wants to assert it is the last entry point, it can
        raise ``StopIteration``.

        The resulting ``Schema`` is memoized for the base URL, so it is only
        constructed once per Python session.

        :param str base_url: The ``shotgun.base_url`` to lookup the schema for.
        :returns: A ``Schema`` instance.

        """

        # If it is a Shotgun instance, grab the url.
        if not isinstance(base_url, basestring):
            base_url = base_url.base_url

        try:
            # Try to return a single instance.
            schema = cls._cache_instances[base_url]

        except KeyError:

            schema = cls()
            schema.load_entry_points(base_url, group='sgschema_cache')

            # Cache it so we only load it once.
            cls._cache_instances[base_url] = schema

        if not schema.entities:
            raise ValueError('no data cached')

        return schema

    def __init__(self):

        #: Result from ``shotgun.schema_read()``.
        self.raw_fields = None

        #: Result from ``shotgun.schema_entity_read()``.
        self.raw_entities = None

        #: Result from scraping ``{base_url}/page/schema``.
        self.raw_private = None

        self.entities = {}
        self.entity_aliases = {}
        self.entity_tags = {}

    def _get_or_make_entity(self, name):
        try:
            return self.entities[name]
        except KeyError:
            return self.entities.setdefault(name, Entity(self, name))

    def read(self, sg):
        """Read the raw public and private schemas from Shotgun.

        :param sg: The ``shotgun_api3.Shotgun`` instance to read the schema from.

        This reads the schema via ``Shotgun.schema_read()`` and
        ``Shotgun.schema_entity_read()``, as well as the "private" schema
        embedded into the Javascript of the Shotgun website.

        The raw schemas are then reduced, retaining only data types, and
        other info required for SGSchema's operations. It may be required
        to re-read (and cache) schema data as SGSchema is improved.

        """

        # Most of the time we don't need this, so don't bother importing.
        from requests import Session

        # SG.schema_field_read() is the same data per-entity as SG.schema_read().
        # SG.schema_entity_read() contains global name and visibility of each
        # entity type, but the visibility is likely to just be True for everything.
        self.raw_fields = sg.schema_read()
        self.raw_entities = sg.schema_entity_read()

        # We also want the private schema which drives the website.
        # See <http://mikeboers.com/blog/2015/07/21/a-complete-shotgun-schema>.

        session = Session()
        session.cookies['_session_id'] = sg.get_session_token()
        
        js = session.get(sg.base_url + '/page/schema').text
        encoded = js.splitlines()[0]
        m = re.match(r'^SG\.schema = new SG\.Schema\((.+)\);\s*$', encoded)
        if not m:
            raise ValueError('schema does not appear to be at %s/page/schema' % sg.base_url)

        self.raw_private = json.loads(m.group(1))

        self._reduce_raw()

    def _reduce_raw(self):
        
        for type_name, raw_entity in self.raw_entities.iteritems():
            entity = self._get_or_make_entity(type_name)
            entity._reduce_raw(self, raw_entity)

        for type_name, raw_fields in self.raw_fields.iteritems():
            entity = self._get_or_make_entity(type_name)
            for field_name, raw_field in raw_fields.iteritems():
                field = entity._get_or_make_field(field_name)
                field._reduce_raw(self, raw_field)

    def _dump(self):
        return dict((k, v) for k, v in (
            ('entities', self.entities),
            ('entity_aliases', self.entity_aliases),
            ('entity_tags', self.entity_tags),
        ) if v)

    def dump(self, path):
        """Save the schema as JSON to the given path.

        :param str path: The path to save to.

        """
        with open(path, 'w') as fh:
            fh.write(json.dumps(self, indent=4, sort_keys=True, default=lambda x: x._dump()))

    def load_directory(self, dir_path):
        """Load all ``.json`` and ``.yaml`` files in the given directory."""
        for file_name in os.listdir(dir_path):
            if file_name.startswith('.'):
                continue
            if os.path.splitext(file_name)[1] not in ('.json', '.yaml'):
                continue
            self.load(os.path.join(dir_path, file_name))

    def load_entry_points(self, base_url, group='sgschema_loaders', verbose=False):
        """Call pkg_resources' entry points to get schema data.

        This calls all entry points (sorted by name) in the given group,
        passing the ``Schema`` object, and the given ``base_url``. Any
        returned values will be passed to :meth:`load`.

        An entry point may raise ``StopIteration`` to force it to be the last.

        By convension, names starting with ``000_`` should provide basic (e.g.
        raw or reduced from raw) data, ``100_`` for package defaults, and ``500_``
        for site data, and `zzz_` for user overrides.

        :param str base_url: To be passed to all entry points.
        :param str group: The entry point group; defaults to ``sgschema_loaders``.
            Another common group is ``sgschema_cache``, which is used by
            :meth:`from_cache`.
        :param bool verbose: Print entrypoints as we go.

        """

        import pkg_resources

        entry_points = list(pkg_resources.iter_entry_points(group))
        entry_points.sort(key=lambda ep: ep.name)

        for ep in entry_points:
            if verbose:
                print 'loading from', ep.name
            func = ep.load()
            try:
                data = func(self, base_url)
            except StopIteration:
                return
            else:
                if data:
                    schema.load(data)

    def load(self, input_, recurse=True):
        """Load a JSON file or ``dict`` containing schema structures.

        If passed a string, we treat is as a path to a JSON or YAML file
        (where JSON is preferred due to speed).

        If passed a dict, it is handed off to :meth:`update`.

        If passed another iterable, we recurse passing every element back
        into this method. This is useful for entry points yielding paths.

        """

        if isinstance(input_, basestring):  
            encoded = open(input_).read()
            if input_.endswith('.json'):
                data = json.loads(encoded)
            elif input_.endswith('.yaml'):
                import yaml # Delay as long as possible.
                data = yaml.load(encoded)
            else:
                raise ValueError('unknown filetype %s' % os.path.splitext(input_))
            self.update(data)

        elif isinstance(input_, dict):
            self.update(input_)

        elif recurse:
            for x in input_:
                self.load(x, recurse=False)

        else:
            raise TypeError('load needs str, dict, or list')

    def update(self, *args, **kwargs):
        for arg in args:
            if not isinstance(arg, dict):
                raise TypeError('Schema.update needs dict')
            self._load(arg)
        if kwargs:
            self._load(kwargs)

    def _load(self, raw_schema):

        # We mutate this object, and aren't sure how any pickler will feel
        # about it.
        raw_schema = copy.deepcopy(raw_schema)

        # If it is a dictionary of entity types, pretend it is in an "entities" key.
        title_cased = sum(int(k[:1].isupper()) for k in raw_schema)
        if title_cased:
            if len(raw_schema) != title_cased:
                raise ValueError('mix of direct and indirect entity specifications')
            raw_schema = {'entities': raw_schema}

        for type_name, value in raw_schema.pop('entities', {}).iteritems():
            self._get_or_make_entity(type_name)._load(value)

        merge_update(self.entity_aliases, raw_schema.pop('entity_aliases', {}))
        merge_update(self.entity_tags   , raw_schema.pop('entity_tags',    {}))

        if raw_schema:
            raise ValueError('unknown schema keys: %s' % ', '.join(sorted(raw_schema)))

    def resolve_entity(self, entity_spec, implicit_aliases=True, strict=False):
        """Resolve an entity-type specification into a list of entity types.

        :param str entity_spec: An entity-type specification.
        :param bool implicit_aliases: Lookup aliases without explicit ``$`` prefix?
        :param bool strict: Raise ``ValueError`` if we can't identify the entity type?
        :returns: ``list`` of entity types (``str``).

        """
        op = entity_spec[0]
        if op == '!':
            return [entity_spec[1:]]
        if op == '#':
            return list(self.entity_tags.get(entity_spec[1:], ()))
        if op == '$':
            try:
                return [self.entity_aliases[entity_spec[1:]]]
            except KeyError:
                return []
        if not op.isalnum():
            raise ValueError('unknown entity operation for %r' % entity_spec)

        # Actual entity names have preference over implicit aliases.
        if entity_spec in self.entities:
            return [entity_spec]

        if implicit_aliases and entity_spec in self.entity_aliases:
            return [self.entity_aliases[entity_spec]]

        if strict:
            raise ValueError('%r is not an entity type' % entity_spec)

        return [entity_spec]

    def resolve_one_entity(self, entity_spec, **kwargs):
        """Resolve an entity-type specification into a single entity type.

        Parameters are the same as for :meth:`resolve_entity`.

        :raises ValueError: when zero or multiple entity types are resolved.

        """
        res = self.resolve_entity(entity_spec, **kwargs)
        if len(res) == 1:
            return res[0]
        else:
            raise ValueError('%r returned %s entity types' % (entity_spec, len(res)))

    def _resolve_field(self, entity_spec, field_spec, auto_prefix=True, implicit_aliases=True, strict=False):

        try:
            entity = self.entities[entity_spec]
        except KeyError:
            raise ValueError('%r is not an entity type' % entity_spec)

        # These two are special, and should always be returned as-is.
        # We only need to do "type" in this way, since "id" usually exists
        # as a numeric field, but it feels right.
        if field_spec in ('id', 'type'):
            return [field_spec]

        op = field_spec[0]
        if op == '!':
            return [field_spec[1:]]
        if op == '#':
            return list(entity.field_tags.get(field_spec[1:], ()))
        if op == '$':
            try:
                return [entity.field_aliases[field_spec[1:]]]
            except KeyError:
                # We need to maintain $FROM$, and we want this to fail
                # if it gets to Shotgun.
                return [field_spec]
        if not op.isalnum():
            raise ValueError('unknown field operation for %s %r' % (entity_spec, field_spec))

        # Actual field names have preference over automatic prefixes or
        # implicit aliases.
        if field_spec in entity.fields:
            return [field_spec]

        if auto_prefix:
            prefixed = 'sg_' + field_spec
            if prefixed in entity.fields:
                return [prefixed]

        if implicit_aliases and field_spec in entity.field_aliases:
            return [entity.field_aliases[field_spec]]

        if strict:
            raise ValueError('%r is not a field of %s' % (field_spec, entity_spec))

        return [field_spec]

    def resolve_field(self, entity_type, field_spec, auto_prefix=True, implicit_aliases=True, strict=False):
        """Resolve an field specification into a list of field names.

        :param str entity_type: An entity type (``str``).
        :param str field_spec: An field specification.
        :param bool auto_prefix: Lookup field with ``sg_`` prefix?
        :param bool implicit_aliases: Lookup aliases without explicit ``$`` prefix?
        :param bool strict: Raise ``ValueError`` if we can't identify the entity type?
        :returns: ``list`` of field names.

        """

        # Return a merge of lists of field specs.
        if isinstance(field_spec, (tuple, list)):
            res = []
            for x in field_spec:
                res.extend(self.resolve_field(entity_type, x, auto_prefix, implicit_aliases, strict))
            return res

        spec_parts = field_spec.split('.')

        # Shortcut if there isn't anything fancy going on.
        if len(spec_parts) == 1:
            return self._resolve_field(entity_type, field_spec, auto_prefix, implicit_aliases, strict)

        # Crate list of [entity_type, field_spec] pairs.
        spec_pairs = [[spec_parts[i-1] if i else None, spec_parts[i]] for i in xrange(0, len(spec_parts), 2)]
        spec_pairs[0][0] = entity_type

        # Resolve each pair.
        resolved_pair_sets = []
        for i, (entity_spec, field_spec), in enumerate(spec_pairs):
            resolved_pairs = []
            resolved_pair_sets.append(resolved_pairs)
            # Here entity types need not already exist; resolve them.
            entity_types = self.resolve_entity(entity_spec, implicit_aliases, strict)
            for entity_type in entity_types:
                for field_name in self._resolve_field(entity_type, field_spec, auto_prefix, implicit_aliases, strict):
                    resolved_pairs.append((entity_type, field_name))

        # Return the product of all resolved fields.
        resolved_fields = []
        for pairs in itertools.product(*resolved_pair_sets):
            field = '.'.join((entity_type + '.' if i else '') + field_name for i, (entity_type, field_name) in enumerate(pairs))
            resolved_fields.append(field)
        return resolved_fields

    def resolve_one_field(self, entity_type, field_spec, **kwargs):
        """Resolve a field specification into a single field name.

        Parameters are the same as for :meth:`resolve_fields`.

        :raises ValueError: when zero or multiple fields are resolved.

        """
        res = self.resolve_field(entity_type, field_spec, **kwargs)
        if len(res) == 1:
            return res[0]
        else:
            raise ValueError('%r returned %s %s fields' % (field_spec, len(res), entity_type))

    def resolve_structure(self, x, entity_type=None, **kwargs):
        """Traverse a nested structure resolving names in entities.

        Recurses into ``list``, ``tuple`` and ``dict``, looking for ``dicts``
        with both a ``type`` and ``id`` (e.g. they could be Shotgun entities),
        and resolves all other keys within them.

        All ``**kwargs`` are passed to :meth:`resolve_field`.

        Returns a copy of the nested structure.

        """

        if isinstance(x, (list, tuple)):
            return type(x)(self.resolve_structure(x, **kwargs) for x in x)

        elif isinstance(x, dict):
            entity_type = entity_type or x.get('type')
            if entity_type and entity_type in self.entities:
                new_values = {}
                for field_spec, value in x.iteritems():
                    value = self.resolve_structure(value)
                    for field in self.resolve_field(entity_type, field_spec, **kwargs):
                        new_values[field] = value
                return new_values
            else:
                return {
                    k: self.resolve_structure(v, **kwargs)
                    for k, v in x.iteritems()
                }

        else:
            return x












if __name__ == '__main__':

    import time
    from shotgun_api3_registry import connect

    sg = connect(use_cache=False)

    schema = Schema()

    if False:
        schema.read(sg)
        schema.dump('sandbox/raw.json', raw=True)
    else:
        schema.load_raw('sandbox/raw.json')

    schema.dump('sandbox/reduced.json')
    schema.dump('/tmp/reduced.json')

    t = time.time()
    schema = Schema()
    schema.load('/tmp/reduced.json')
    print 1000 * (time.time() - t)

