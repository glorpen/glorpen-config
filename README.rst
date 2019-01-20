==============
Glorpen Config
==============

.. image:: https://travis-ci.org/glorpen/glorpen-config.svg?branch=master
    :target: https://travis-ci.org/glorpen/glorpen-config
.. image:: https://readthedocs.org/projects/glorpen-config/badge/?version=latest
    :target: https://glorpen-config.readthedocs.io/en/latest/

Config framework for Your projects - with validation, interpolation and value normalization!

Full documentation: https://glorpen-config.readthedocs.io/

Official repositories
=====================

GitHub: https://github.com/glorpen/glorpen-config

BitBucket: https://bitbucket.org/glorpen/glorpen-config

Features
========

You can:

- create custom fields for custom data
- define configuration schema inside Python app
- convert configuration values to Python objects
- validate configuration
- use interpolation to fill config values
- set default values

Loading data
------------

``glorpen.config.Config`` uses ``glorpen.config.loaders`` to allow loading data from different sources.

Loaders should accept:

- path, ``filepath`` constructor argument
- file-like object, ``fileobj`` constructor argument

Additionally you can just pass ``dict`` data to config with ``glorpen.config.Config.load_data`` or ``glorpen.config.Config.finalize``.

Interpolation
-------------

You can reuse values from config with ``{{ path.to.value }}`` notation, eg:

.. code-block:: yaml

   project:
      path: "/tmp"
      cache_path: "{{ project.path }}/cache"

String interpolation currently can be used only with ``glorpen.config.fields.simple.String`` fields.

Normalization and validation
----------------------------

Each field type has own normalization rules, eg. for ``glorpen.config.fields.log.LogLevel``:

.. code-block:: yaml

   logging: DEBUG

``config.get("logging")`` would yield value ``10`` as is ``logging.DEBUG``. 

Additionally it will raise ``glorpen.config.exceptions.ValidationError`` if invalid level name is given.

Default values
--------------

Each field can have default value. If no value is given in config but default one is set, it will be used instead.

Default values adhere to same interpolation and normalization rules - each default value is denormalized and then passed to normalizers.
That way complex object can still profit from config interpolation. There should not be any real impact on performance as it is done only once.

Example usage
=============

Your first step should be defining configuration schema:

.. code-block:: python

   import logging
   import glorpen.config.fields.simple as f
   from glorpen.config.fields.log import LogLevel
   
   project_path = "/tmp/project"
   
   spec = f.Dict({
     "project_path": f.Path(default=project_path),
     "project_cache_path": f.Path(default="{{ project_path }}/cache"),
     "logging": LogLevel(default=logging.INFO),
     "database": f.String(),
     "sources": f.Dict({
         "some_param": f.String(),
         "some_path": f.Path(),
     }),
     "maybe_string": f.Variant([
         f.String(),
         f.Number()
     ])
   })

Example yaml config:

.. code-block:: yaml

   logging: "DEBUG"
   database: "mysql://...."
   sources:
     some_param: "some param"
     some_path: "/tmp"
   maybe_string: 12

Then you can create ``glorpen.config.Config`` instance:

.. code-block:: python

   from glorpen.config import Config
   import glorpen.config.loaders as loaders
   
   loader = loaders.YamlLoader(filepath=config_path)
   cfg = Config(loader=loader, spec=spec).finalize()
   
   cfg.get("sources.some_param") #=> 'some param'
   cfg.get("project_path") #=> '/tmp/project'
   cfg.get("project_cache_path") #=> '/tmp/project/cache'
   cfg.get("logging") #=> 10
   cfg.get("maybe_string") #=> 12

Creating custom fields
======================

Custom field class should extend ``glorpen.config.fields.base.Field`` or ``glorpen.config.fields.base.FieldWithDefault``.

``glorpen.config.fields.base.Field.make_resolvable`` method should register normalizer functions which later will be called in registration order.
Each value returned by normalizer is passed to next one. After chain end value is returned as config value.

Returned ``glorpen.config.fields.base.ResolvableObject`` instance is resolved before passing it to next normalizer.

If value passed to normalizator is invalid it should raise ``glorpen.config.exceptions.ValidationError``.
Sometimes value can be lazy loaded - it is represented as ``glorpen.config.fields.base.ResolvableObject``.
You can get real value by using ``glorpen.config.fields.base.resolve(value, config)``.

.. code-block:: python

   class MyValue(object):
      def __init__(self, value):
         super(MyValue, self).__init__()
         self.value = value
   
   class MyField(Field):
       
       def to_my_value(self, value, config):
           return MyValue(value)
       
       def is_value_supported(self, value):
           return True
       
       def make_resolvable(self, r):
           r.on_resolve(self.to_my_value)

The last thing is to use prepared custom field in configuration spec.
