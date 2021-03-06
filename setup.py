# -*- coding: utf-8 -*-
'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

from setuptools import setup
import re
import os
import sys

root_dir = os.path.realpath(os.path.dirname(__file__))
with open("%s/src/glorpen/config/__init__.py" % root_dir, "rt") as f:
    version = re.search(r'__version__\s*=\s*"([^"]+)"', f.read()).group(1)

with open("%s/README.rst" % root_dir, "rt") as f:
    long_description = f.read()

setup (
  name = "glorpen-config",
  version = version,
  packages = [
    "glorpen.config",
    "glorpen.config.fields",
    "glorpen.config.translators"
  ],
  package_dir = {"": "src"},
  install_requires = [],
  dependency_links = [],
  namespace_packages  = ["glorpen"],
  author = "Arkadiusz Dzięgiel",
  author_email = "arkadiusz.dziegiel@glorpen.pl",
  description = "Loads, validates and normalizes configuration.",
  tests_require = [],
  url = "https://github.com/glorpen/glorpen-config",
  license = "GPLv3+",
  long_description = long_description,
  classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Libraries :: Python Modules",
  ],
  test_suite = "glorpen.config.tests",
  extras_require = {
      'semver': ['semver>=2.0,<3.0'],
      'yaml': ['PyYAML>=5.0,<6.0'],
  }
)
