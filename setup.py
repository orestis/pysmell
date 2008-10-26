#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from setuptools import setup

setup(
    name='pysmell',
    version ='0.6',
    description = 'An autocompletion library for Python',
    author = 'Orestis Markou',
    author_email = 'orestis@orestis.gr',
    packages = ['pysmell'],
    entry_points = {
        'console_scripts': [ 'pysmell = pysmell.pysmell:main' ]
    },
    data_files = [
        ('vim', ['pysmell.vim'])
    ],
    license = 'BSD',
    keywords = 'vim autocomplete',
    url = 'http://orestis.gr/tags/pysmell',
    description = 'PySmell is a python IDE completion helper. ',
    long_description =
"""\
PySmell is a python IDE completion helper. 

It tries to statically analyze Python source code, without executing it,
and generates information about a project's structure that IDE tools can
use.

The first target is Vim, because that's what I'm using and because its
completion mechanism is very straightforward, but it's not limited to it.
""",
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
        'Topic :: Utilities',
        'Topic :: Text Editors',
    ]
        

)
