#!/usr/bin/env python

#      This file is part of the PEP GUI detection pipeline batch running tool
#      Copyright (C) 2021 Yuval Boss yuval@uw.edu
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

from distutils.core import setup
import sys
sys.path.append('src')
from setuptools import find_packages
import os
import unittest

# Parse Version information
version_txt_fp = os.path.normpath('src/pep_tk/VERSION.txt')
with open(version_txt_fp, 'r') as file:
    _v_ = file.read().replace('\n', '')
if len(_v_.split('.')) == 3:
    _v_ = _v_
else:
    print(f'Invalid VERSION.cfg - could not parse {_v_}')


# Parse requirements.txt to list
with open('requirements.txt') as f:
    install_reqs = f.read().splitlines()
install_reqs = list(filter(None, install_reqs))

# Parse README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        path = os.sep.join(path.split(os.sep)[2:])
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return paths


extra_files = package_files('src/pep_tk/conf') + package_files('src/pep_tk/lib') + package_files('src/pep_tk')

# define function for python setup.py test
def test_suit():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite


setup(
        name='pep_tk',
        version=_v_,
        description='Polar Ecosystems Program Toolkit',
        long_description=long_description,
        long_description_content_type="text/markdown",
        author='Yuval Boss',
        author_email='yuval@uw.edu',
        url='https://github.com/readicculus/pep_gui',
        install_requires=install_reqs,
        packages=find_packages('src'),
        package_dir={'pep_tk': 'src/pep_tk'},
        package_data={"pep_tk": extra_files},
        include_package_data=True,
        entry_points={
          'console_scripts': ['pep_gui=pep_tk:launch.main'],
        },
        python_requires='>=3.8',
        test_suite="setup.test_suit",
)
