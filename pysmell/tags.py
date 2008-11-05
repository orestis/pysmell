#!/usr/bin/env python
# pysmell.py
# Statically analyze python code and generate PYSMELLTAGS file
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# http://orestis.gr

# Released subject to the BSD License 

import os
import sys
from textwrap import dedent
from pprint import pprint

from pysmell.codefinder import ModuleDict, processFile
from pysmell.idehelper import findRootPackageList

from pysmell import argparse
 
version = __import__('pysmell').__version__

source = """
class Aclass(object):
    def do_stuff(self):
        a = 1
        print a
        self.bar = 42

    def do_other_stuff(self):
        self.bar().do_stuff()
        self.baz.do_stuff()

def test(aname):
    aname.do_stuff()
    aname.do_other_stuff()
"""


def generateClassTag(modules, output):
    p = os.path.abspath(output)
    f = open(p, 'w')
    pprint(modules, f, width=100)
    f.close()


def process(argList, excluded, output, inputDict=None, verbose=False):
    modules = ModuleDict()
    if inputDict:
        modules.update(inputDict)
    for rootPackage in argList:
        if os.path.isdir(rootPackage):
            for path, dirs, files in os.walk(rootPackage):
                for exc in excluded:
                    if exc in dirs:
                        if verbose:
                            print 'removing', exc, 'in', path
                        dirs.remove(exc)
                for f in files:
                    if not f.endswith(".py"):
                        continue
                    #path here is relative, make it absolute
                    absPath = os.path.abspath(path)
                    if verbose:
                        print 'processing', absPath, f
                    newmodules = processFile(f, absPath)
                    modules.update(newmodules)
        else: # single file
            filename = rootPackage
            absPath, filename = os.path.split(filename)
            if not absPath:
                absPath = os.path.abspath(".")
            else:
                absPath = os.path.abspath(absPath)
                
            #path here is absolute
            if verbose:
                print 'processing', absPath, filename
            newmodules = processFile(filename, absPath)
            modules.update(newmodules)
            
    generateClassTag(modules, output)


def main():
    description = dedent("""\
        Generate a PYSMELLTAGS file with information about the
        Python code contained in the specified packages (recursively). This file is
        then used to provide autocompletion for various IDEs and editors that
        support it. """)
    parser = argparse.ArgumentParser(description=description, version=version, prog='pysmell')
    parser.add_argument('fileList', metavar='package', type=str, nargs='+',
        help='The packages to be analysed.')
    parser.add_argument('-x', '--exclude', metavar='package', nargs='*', type=str, default=[],
        help=dedent("""Will not analyze files in directories that match the
        argument. Useful for excluding tests or version control directories."""))
    parser.add_argument('-o', '--output', default='PYSMELLTAGS',
        help="File to write the tags to")
    parser.add_argument('-i', '--input',
        help="Preexisting tags file to update")
    parser.add_argument('-t', '--timing', action='store_true',
        help="Will print timing information")
    parser.add_argument('-d', '--debug', action='store_true',
        help="Verbose mode; useful for debugging")
    args = parser.parse_args()
    fileList = args.fileList
    excluded = args.exclude
    timing = args.timing
    output = args.output
    verbose = args.debug
    inputFile = args.input
    if inputFile:
        try:
            inputDict = eval(file(inputFile).read())
        except:
            print >> sys.stderr, "Could not process %s - is it a PYSMELLTAGS file?" % inputFile
            sys.exit(3)
    else:
        inputDict = None


    #if not fileList:
    #    fileList = [os.getcwd()]

    if timing:
        import time
        start = time.clock()
    if verbose:
        print 'processing', fileList
        print 'ignoring', excluded
    process(fileList, excluded, output, inputDict=inputDict, verbose=verbose)
    if timing:
        took = time.clock() - start
        print 'took %f seconds' % took


if __name__ == '__main__':
    main()
