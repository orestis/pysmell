#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from ez_setup import use_setuptools
use_setuptools(version="0.6c8")
from distutils import cmd
from setuptools import setup


from setuptools.command.install import install as _install

post_install_message = """\

===================================================================
PySmell has a number of support scripts for Vim, Emacs.
You have to manually copy them from the source distribution to your
.vim/plugins, .emacs.d to be able to use PySmell. 

TextMate users should double-click on the bundle to install it.

Consult the README for more information
===================================================================
"""

class install(_install):
    def run(self):
        _install.run(self)
        print post_install_message

version = __import__('pysmell').__version__


setup(
    cmdclass={'install': install},
    name='pysmell',
    version = version,
    description = 'An autocompletion library for Python',
    author = 'Orestis Markou',
    author_email = 'orestis@orestis.gr',
    packages = ['pysmell'],
    entry_points = {
        'console_scripts': [ 'pysmell = pysmell.tags:main' ]
    },
    include_package_data = True,
    test_suite = "Tests",
    keywords = 'vim emacs textmate autocomplete',
    url = 'http://code.google.com/p/pysmell',
    long_description =
"""\
PySmell is a python IDE completion helper. 

It tries to statically analyze Python source code, without executing it,
and generates information about a project's structure that IDE tools can
use.

PySmell currently supports Vim, Emacs and TextMate. It can be integrated with
any editor that can run Python scripts and has an auto-complete API.
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
