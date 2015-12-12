# -*- coding: utf-8 -*-
'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

from setuptools import setup, find_packages
import re
import os

root_dir = os.path.realpath(os.path.dirname(__file__))
with open("%s/src/config/__init__.py" % root_dir, "rt") as f:
    version = re.search(r'__version__\s*=\s*"([^"]+)"', f.read()).group(1)

with open("%s/README.rst" % root_dir, "rt") as f:
    long_description = f.read()

setup (
  name = 'glorpenlibs_config',
  version = version,
  packages = ["glorpen.config"],
  package_dir = {'glorpen': 'src'},
  install_requires=["yaml"],
  dependency_links = [],
  namespace_packages  = ["glorpen"],
  author = 'Arkadiusz Dzięgiel',
  author_email = 'arkadiusz.dziegiel@glorpen.pl',
  description = 'Loads, validates, normalizes configuration in yaml.',
  url = '',
  license = '',
  long_description= long_description,
  #python3+
)
