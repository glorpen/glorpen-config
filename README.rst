==============
glorpen.config
==============

.. image:: https://travis-ci.org/glorpen/glorpen-config.svg?branch=master

Yaml config for Your projects - with validation, interpolation and value normalization!

Official repositories
=====================

For forking and other funnies.

BitBucket: https://bitbucket.org/glorpen/glorpen-config

GitHub: https://github.com/glorpen/glorpen-config

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

`glorpen.config.Config` class allows loading data from three sources:

- path, `filepath` constructor argument
- file-like object, `fileobj` constructor argument
- dict object passed to `glorpen.config.Config.load_data` or `glorpen.config.Config.finalize`.

Interpolation
-------------

You can reuse values from config with `{{ path.to.value }}` notation, eg:

.. code-block:: yaml

   project:
      path: "/tmp"
      cache_path: "{{ project.path }}/cache"

If normalized value object `MyClass('/tmp','{{project.path}}')` is `denormalized` to `/tmp:{{project.path}}`,
after resolving configuration it will read `MyClass('/tmp','/tmp')`.

Normalization and validation
----------------------------

Each field type has own normalization rules, eg. for `fields.LogLevel`:

.. code-block:: yaml

   logging: DEBUG

`config.get("logging")` would yield value `10` as is `logging.DEBUG`. 

Additionally it will raise `exceptions.ValidationError` if invalid level name is given.

Default values
--------------

Each field can have default value. If no value is given in config but default one is set, it will be used instead.

Default values adhere to same interpolation and normalization rules - each default value is denormalized and then passed to normalizers.
That way complex object can still profit from config interpolation. There should not be any real impact on performance as it is done only once.

Example usage
=============

Your first step should be defining configuration schema:

.. code-block:: python

   from glorpen.config import Config
   from glorpen.config.fields import Dict, String, Path, LogLevel
   
   project_path = "/tmp/project"
   
   spec = Dict(
      project_path = Path(default=project_path),
      project_cache_path = Path(default="{{ project_path }}/cache"),
      logging = Dict(
          level = LogLevel(default=logging.INFO)
      ),
      database = String(),
      sources = Dict(
          some_param = String(),
          some_path = Path(),
      )
   )

Example yaml config:

.. code-block:: yaml

   logging: "DEBUG"
   database: "mysql://...."
   sources:
      some_param: "some param"
      some_path: "/tmp"

Then you can create `Config` instance:

.. code-block:: python

   cfg = Config(filepath=config_path, spec=spec).finalize()

   cfg.get("sources.some_param") #=> "some param"
   cfg.get("project_path") #=> "/tmp/project"
   cfg.get("project_cache_path") #=> "/tmp/project/cache"
   cfg.get("logging") #=> 10

Creating custom fields
======================

Custom field class should extend `glorpen.config.fields.Field`.

`Field.make_resolvable` method should register normalizer functions which later will be called in registration order.
Each value returned by normalizer is passed to next one. After chain end value is returned as config value.

`denormalize` method should convert field's normalized object back to string.

If value passed to normalizator is invalid it should raise `exceptions.ValidationError`.

.. code-block:: python

   class MyValue(object):
      def __init__(self, value):
         super(MyValue, self).__init__()
         self.value = value
   
   class MyField(Field):
       
       def to_my_value(self, value, config):
           return MyValue(value)
       
       def denormalize(self, value):
           return value.value
       
       def make_resolvable(self, r):
           r.on_resolve(self.to_my_value)

The last thing is to use prepared custom field in configuration spec.
