# pysmelltags.py
# Statically analyze python code and generate PYSMELLTAGS file
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# pysmell v0.2
# http://orestis.gr

# Released subject to the BSD License 


import sys, os
from codefinder import ModuleDict, processFile
from pprint import pprint

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


def generateClassTag(modules):
    f = open(os.path.join(os.getcwd(), 'PYSMELLTAGS'), 'w')
    pprint(modules, f, width=100)
    f.close()


def process(argList, excluded):
    modules = ModuleDict()
    for item in fileList:
        if os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                if os.path.basename(root) in excluded:
                    continue
                for f in files:
                    if not f.endswith(".py"):
                        continue
                    newmodules = processFile(f, root, item)
                    modules.update(newmodules)
        else: # single file
            newmodules = processFile(item, '', '')
            modules.update(newmodules)
            
    generateClassTag(modules)



if __name__ == '__main__':
    fileList = sys.argv[1:]
    if '-h' in fileList:
        print 'Usage: python pysmelltags.py [PackageA PackageB FileA.py FileB.py] [-x ExcludedDir1 ExcludedDir2]'
        sys.exit(0)
    timing = False
    excluded = []
    if '-t' in fileList:
        timing = True
        fileList.remove('-t')
    if '-x' in fileList:
        excluded = fileList[fileList.index('-x')+1:]
        fileList = fileList[:fileList.index('-x')]
    if not fileList:
        fileList = [os.getcwd()]

    if timing:
        import time
        start = time.clock()
    process(fileList, excluded)
    if timing:
        took = time.clock() - start
        print 'took %f seconds' % took


