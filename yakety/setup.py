#! /usr/bin/env python3

from setuptools import setup

setup(name='yakety',
      version='0.1',
      description='An EBNF Parser Generator',
      url='https://github.com/reindeereffect/blog-tools/tree/master/yakety',
      author='Kevin M. Stout',
      packages=['yakety'],
      scripts=['bin/ykt', 'bin/dotify'],
      zip_safe=False)


