# pysmelltags.py
# Statically analyze python code and generate PYSMELLTAGS file
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# pysmell v0.1
# http://orestis.gr

# Released subject to the BSD License 


import sys, os
import compiler
from codefinder import CodeFinder
from compiler.visitor import ExampleASTVisitor
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

def check_method_arguments(self, func):
    if self.inClass:
        if func.argnames:
            if func.argnames[0] != 'self':
                print ('self! in class %s, function %s, line %d' %
                    (self.currentClass, func.name, func.lineno))
        else:
            print ('no args!')


def getClassDict(path, codeFinder=None):
    tree = compiler.parseFile(path)
    if codeFinder is None:
        codeFinder = CodeFinder()
    compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
    return codeFinder.classes


def generateClassTag(classes):
    f = open(os.path.join(os.getcwd(), 'PYSMELLTAGS'), 'w')
    pprint(classes._modules, f, width=100)
    f.close()


def process(argList, excluded):
    codeFinder = CodeFinder()
    classes = None
    for item in fileList:
        if os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                if os.path.basename(root) in excluded:
                    continue
                for f in files:
                    if not f.endswith(".py"):
                        continue
                    newClasses = processFile(f, codeFinder, root)
                    if newClasses:
                        classes = newClasses
        else: # single file
            newClasses = processFile(item, codeFinder, '')
            if newClasses:
                classes = newClasses
            
            
    generateClassTag(classes)

def processFile(f, codeFinder, root):
    print os.path.join(root, f),
    if f == '__init__.py':
        codeFinder.setFilename(os.path.split(root)[-1])
    else:
        codeFinder.setFilename(f)
    try:
        classes = getClassDict(os.path.join(root, f), codeFinder)
        print len(classes._modules.keys())
        return classes
    except:
        print '-=#=- '* 10
        print 'EXCEPTION in', os.path.join(root, f)
        print '-=#=- '* 10
        return None
        

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


