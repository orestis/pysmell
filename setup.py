#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from setuptools import setup

setup(name='pysmell',
        version ='0.6',
        description = 'An autocompletion library for Python',
        author = 'Orestis Markou',
        author_email = 'orestis@orestis.gr',
        packages = ['pysmell'],
        entry_points = {
            'console_scripts': [ 'pysmell = pysmell:main' ]
            },
        data_files = [
            ('vim', ['pysmell.vim'])
            ]
        )
