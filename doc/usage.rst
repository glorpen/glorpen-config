=============
Example usage
=============

Using fields
============

Your first step should be defining configuration schema:

.. code-block:: python

   import logging
   import glorpen.config.fields.simple as f
   from glorpen.config.fields.log import LogLevel
   
   project_path = "/tmp/project"
   
   spec = f.Dict({
     "project_path": f.Path(default=project_path),
     "project_cache_path": f.Path(default="{{ project_path }}/cache"),
     "logging": fl.LogLevel(default=logging.INFO),
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

Custom field class should extend :class:`glorpen.config.fields.base.Field` or :class:`glorpen.config.fields.base.FieldWithDefault`.

:meth:`glorpen.config.fields.base.Field.make_resolvable` method should register normalizer functions which later will be called in registration order.
Each value returned by normalizer is passed to next one. After chain end value is returned as config value.

Returned :class:`glorpen.config.fields.base.ResolvableObject` instance is resolved before passing it to next normalizer.

If value passed to normalizator is invalid it should raise :class:`glorpen.config.exceptions.ValidationError`.
Sometimes value can be lazy loaded - it is represented as :class:`glorpen.config.fields.base.ResolvableObject`.
You can get real value by using :meth:`glorpen.config.fields.base.resolve`.

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
