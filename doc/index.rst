==============
Glorpen Config
==============

.. image:: https://travis-ci.org/glorpen/glorpen-config.svg?branch=master
    :target: https://travis-ci.org/glorpen/glorpen-config
.. image:: https://readthedocs.org/projects/glorpen-config/badge/?version=latest
    :target: https://glorpen-config.readthedocs.io/en/latest/

Config framework for Your projects - with validation, interpolation and value normalization!

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

:class:`glorpen.config.Config` uses :mod:`glorpen.config.loaders` to allow loading data from different sources.

Loaders should accept:

- path, ``filepath`` constructor argument
- file-like object, ``fileobj`` constructor argument

Additionally you can just pass ``dict`` data to config with :meth:`glorpen.config.Config.load_data` or :meth:`glorpen.config.Config.finalize`.

Interpolation
-------------

You can reuse values from config with ``{{ path.to.value }}`` notation, eg:

.. code-block:: yaml

   project:
      path: "/tmp"
      cache_path: "{{ project.path }}/cache"

String interpolation currently can be used only with :class:`glorpen.config.fields.String` fields.

Normalization and validation
----------------------------

Each field type has own normalization rules, eg. for :class:`glorpen.config.fields.LogLevel`:

.. code-block:: yaml

   logging: DEBUG

``config.get("logging")`` would yield value ``10`` as is ``logging.DEBUG``. 

Additionally it will raise :class:`glorpen.config.exceptions.ValidationError` if invalid level name is given.

Default values
--------------

Each field can have default value. If no value is given in config but default one is set, it will be used instead.

Default values adhere to same interpolation and normalization rules - each default value is denormalized and then passed to normalizers.
That way complex object can still profit from config interpolation. There should not be any real impact on performance as it is done only once.


Contents
========

.. toctree::
   :maxdepth: 2
   
   usage.rst
   code.rst
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
