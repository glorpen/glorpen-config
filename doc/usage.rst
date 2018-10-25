=============
Example usage
=============

Using fields
============

Your first step should be defining configuration schema:

.. code-block:: python

   from glorpen.config import Config
   from glorpen.config.fields import Dict, String, Path, LogLevel
   
   project_path = "/tmp/project"
   
   spec = Dict({
      "project_path": Path(default=project_path),
      "project_cache_path": Path(default="{{ project_path }}/cache"),
      "logging": Dict({
          "level": LogLevel(default=logging.INFO)
      }),
      "database": String(),
      "sources": Dict(
          "some_param": String(),
          "some_path": Path(),
      ),
      "maybe_string": Variant([
          String(),
          Number()
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

Then you can create :class:`glorpen.config.Config` instance:

.. code-block:: python

   cfg = Config(filepath=config_path, spec=spec).finalize()

   cfg.get("sources.some_param") #=> "some param"
   cfg.get("project_path") #=> "/tmp/project"
   cfg.get("project_cache_path") #=> "/tmp/project/cache"
   cfg.get("logging") #=> 10
   cfg.get("maybe_string") #=> 12

Creating custom fields
======================

Custom field class should extend :class:`glorpen.config.fields.Field` or :class:`glorpen.config.fields.FieldWithDefault`.

:meth:`glorpen.config.fields.Field.make_resolvable` method should register normalizer functions which later will be called in registration order.
Each value returned by normalizer is passed to next one. After chain end value is returned as config value.

Returned :class:`glorpen.config.fields.ResolvableObject` instance is resolved before passing it to next normalizer.

If value passed to normalizator is invalid it should raise :class:`glorpen.config.exceptions.ValidationError`.
Sometimes value can be lazy loaded - it is represented as :class:`glorpen.config.fields.ResolvableObject`.
You can get real value by using :meth:`glorpen.config.fields.resolve`.

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
