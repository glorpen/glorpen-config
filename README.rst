==============
Glorpen Config
==============

.. image:: https://travis-ci.org/glorpen/glorpen-config.svg?branch=master
  :target: https://travis-ci.org/glorpen/glorpen-config
.. image:: https://readthedocs.org/projects/glorpen-config/badge/?version=latest
  :target: https://glorpen-config.readthedocs.io/en/latest/
.. image:: https://codecov.io/gh/glorpen/glorpen-config/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/glorpen/glorpen-config

Config framework for Your projects - with validation, interpolation and value normalization. It can even generate default config with help texts!

Full documentation: https://glorpen-config.readthedocs.io/

Official repositories
=====================

GitHub: https://github.com/glorpen/glorpen-config

BitBucket: https://bitbucket.org/glorpen/glorpen-config

GitLab: https://gitlab.com/glorpen/glorpen-config

Features
========

You can:

- define configuration schema inside Python app
- convert configuration values to Python objects
- validate user provided data
- use interpolation to fill config values
- generate example configuration with help text

How to load data
----------------

You can use ``Reader`` to read values from arbitrary source and then pass it to ``glorpen.config.Config``:

.. code-block:: python

    from glorpen.config.translators.yaml import YamlReader
    from glorpen.config import Config

    config = Config(String())
    config.get(YamlReader("example.yaml").read())

or with use of ``glorpen.config.Translator``:

.. code-block:: python

    from glorpen.config.translators.yaml import YamlReader
    from glorpen.config import Config, Translator

    translator = Translator(Config(String()))
    translator.read(YamlReader("example.yaml"))


``glorpen.config.Config.get`` accepts anything that is supported by underlying config schema so you can pass ``dict`` or custom objects.

Interpolation
-------------

You can reuse values from config with dotted notation, eg: ``{{ path.to.value }}``.

.. code-block:: yaml

   project:
      path: "/tmp"
      cache_path: "{{ project.path }}/cache"

See field documentation to find where interpolation is supported.

Normalization and validation
----------------------------

Each field type has own normalization rules, eg. for ``glorpen.config.fields.log.LogLevel``:

.. code-block:: yaml

   logging: DEBUG

``config.get(data)`` would yield value ``10`` as in ``logging.DEBUG``. 

Additionally it will raise exception if invalid value is provided.

Optional and default values
---------------------------

Each field can have default value. If no value is given in config but default one is set, it will be used instead.

Default values should be already Python values, eg. int, str, objects.

Example usage
=============

Your first step should be defining configuration schema:

.. code-block:: python

   import logging
   import glorpen.config.fields.simple as fs
   import glorpen.config.fields.base as fb
   from glorpen.config.fields.log import LogLevel
   
   project_path = "/tmp/project"
   
   spec = fs.Dict({
     "project_path": fb.Optional(fs.Path(), default=project_path),
     "project_cache_path": fb.Optional(fs.Path(), default=project_path + "/cache"),
     "logging": LogLevel(default=logging.INFO),
     "database": fs.String(),
     "sources": fs.Dict({
         "some_param": fs.String(),
         "some_path": fs.Path(),
     }),
     "maybe_string": fs.Variant([
         fs.String(),
         fs.Number()
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

   from glorpen.config import Config, Translator
   from glorpen.config.translators.yaml import YamlReader
   
   cfg = Translator(Config(spec)).read(YamlReader(config_path))
   
   cfg["sources"]["some_param"] #=> 'some param'
   cfg["project_path"] #=> '/tmp/project'
   cfg["project_cache_path"] #=> '/tmp/project/cache'
   cfg["logging"] #=> 10
   cfg["maybe_string"] #=> 12

Creating custom fields
======================

TODO
