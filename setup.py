#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

from pep_tk import __version__

# read requirements.txt to list
with open('requirements.txt') as f:
    install_reqs = f.read().splitlines()
install_reqs = list(filter(None, install_reqs))

setup(name='PEP-TK',
      version=__version__,
      description='Polar Ecosystems Program Toolkit',
      author='Yuval Boss',
      author_email='yuval@uw.edu',
      url='https://github.com/readicculus/pep_gui',
      install_requires=install_reqs,
      packages=find_packages(),
     )