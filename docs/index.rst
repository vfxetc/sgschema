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
(from a theoretical pipeline pipeline):

- ``$Publish`` resolves to the ``PublishEvent`` entity type;
- ``$sgpublish:type`` is aliased to the ``PublishEvent.sg_type`` field;
- ``#sgsession:core`` is tagged to the ``Task`` fields ``content``, and ``step``;
- ``$shotgun:name`` is aliased to what Shotgun will return as the ``name`` field
  of all entities;
- ``version`` resolves to the ``PublishEvent.sg_version`` field.

This project is tightly integrated into SGSession, and used in all operations.


Caching
-------

In general, schemas should be preprocessed and cached, then reloaded for each
use. To read the schema, reduce it, and cache it::

    schema = Schema()
    schema.read(shotgun_object)
    schema.dump('/path/to/cache.json')

The cached schema can then be loaded manually::

    schema = Schema()
    schema.load('/path/to/cache.json')

The :meth:`Schema.from_cache` method uses setuptools' entrypoints to find
cached schemas from the runtime environment::

    schema = sgschema.Schema.from_cache(shotgun.base_url)

That class method calls any functions registered as a ``sgschema_cache``
setuptools entrypoint. Those functions are called with the passed URL.
Whatever non-None value is returned first is loaded into the schema. The process
is effectively::

    schema = Schema()
    for func in funcs_from_entrypoints:
        raw_schema = func(base_url)
        if raw_schema:
            schema.load(raw_schema)
            break






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

