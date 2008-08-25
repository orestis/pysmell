import sys
import compiler
from codefinder import CodeFinder
from compiler.visitor import ExampleASTVisitor

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

def method_arguments(self, func):
    if self.inClass:
        if func.argnames:
            if func.argnames[0] != 'self':
                print ('self! in class %s, function %s, line %d' %
                    (self.currentClass, func.name, func.lineno))
        else:
            print ('no args!')


def getClassDict(source):
    tree = compiler.parse(source)
    codeFinder = CodeFinder()
    compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
    return codeFinder.classes


if __name__ == '__main__':
    if len(sys.argv) > 1:
        source = open(sys.argv[1], 'r').read()
    tree = compiler.parse(source)
    codeFinder = CodeFinder()
    codeFinder.addChecker('Function', method_arguments)
    compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)

