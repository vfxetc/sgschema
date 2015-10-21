.. _index:

SGSchema
========

This project aims to assist interaction with Shotgun via its API by applying
knowledge of the server's schema.

The initial use case is to assist tool developers in being able to operate on
Shotgun instances with slightly different schemas. Differences can accrue due
to human mistakes while creating fields, or due to the initial schemas being
different across the history of Shotgun.

You may provide aliases and tags for entity types and fields, as well as
automatically detect and use the common ``"sg_"`` prefix on fields. Example uses
(from a theoretical pipeline):

- ``$Publish`` resolves to the ``PublishEvent`` entity type;
- ``$sgpublish:type`` is aliased to the ``PublishEvent.sg_type`` field;
- ``#sgsession:core`` is tagged to the ``Task`` fields ``content``, and ``step``;
- ``$shotgun:name`` is aliased to what Shotgun will return as the ``name`` field
  of all entities;
- ``version`` resolves to the ``PublishEvent.sg_version`` field.

This project is tightly integrated into SGSession, and used in all operations.


Dynamic Loading and Caching
---------------------------

Packages can define their own schemas at runtime via ``pkg_resources``
entry points. The :meth:`.Schema.load_entry_points` calls registered
functions (to ``sgcache_loaders`` by default) in order to construct a schema.

A good pattern for creating a schema object is::

    schema = Schema()
    schema.read(shotgun_api3_instance)
    schema.load_entry_points(base_url)

This is extremely time consuming to run at startup, so it is recommended to
pre-process and cache the schema. First load the schema as above, then dump
it to a file::

    schema.dump(os.path.join(cache_dir, '%s.json' % base_url))

Then, register an entry point to the ``sgschema_cache`` group, which loads it::

    def load_cache(schema, base_url):
        schema.load(os.path.join(cache_dir, '%s.json' % base_url))




Contents
--------

.. toctree::
   :maxdepth: 2

   setup
   python_api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

