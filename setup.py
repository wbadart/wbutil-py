#!/usr/bin/env python

'''
setup.py

wbutil-py package metadata.

Will Badart <wbadart@live.com>
created: JAN 2018
'''

from setuptools import setup, find_packages


setup(name='wbutil',
      version='2.0.2a0',
      packages=find_packages(),
      url='https://github.com/wbadart/wbutil-py',

      author='Will Badart',
      author_email='wbadart@live.com',
      description='Python utility library',
      license='MIT',
      keywords='utility util helper library',
      homepage='https://github.com/wbadart/wbutil-py',
      project_urls={
          'Bug Tracker': 'https://github.com/wbadart/wbutil-py/issues',
          'Documentation': 'https://github.com/wbadart/wbutil-py/wiki',
          'Source Code': 'https://github.com/wbadart/wbutil-py',
      },

      zip_safe=False)
