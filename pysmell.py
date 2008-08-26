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


def getClassDict(source, codeFinder=None):
    tree = compiler.parse(source)
    if codeFinder is None:
        codeFinder = CodeFinder()
    compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
    return codeFinder.classes

def generateClassTag(classes):
    f = open('PYSMELLTAGS', 'w')
    pprint(classes._classes, f)
    f.close()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        source = open(sys.argv[1], 'r').read()
        generateClassTag(getClassDict(source))
    elif len(sys.argv) == 1:
        codeFinder = CodeFinder()
        classes = None
        for root, dirs, files in os.walk(os.getcwd()):
            for f in files:
                if not f.endswith('.py'):
                    continue
#                print f
                s = open(os.path.join(root, f), 'r').read()
                classes = getClassDict(s, codeFinder)
                if 'UnitTests' in dirs:
                    dirs.remove('UnitTests')
        generateClassTag(classes)

