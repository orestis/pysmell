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
    tree = compiler.parse(source.replace('\r\n', '\n'))
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
                    print f
                    codeFinder.setFilename(f)
                    try:
                        s = open(os.path.join(root, f), 'r').read()
                        if s:
                            classes = getClassDict(s, codeFinder)
                    except:
                        print 'EXCEPTION'
                        print '-=#=- '* 10
                        print s
                        print '-=#=- '* 10
                        raise
    generateClassTag(classes)

if __name__ == '__main__':
    fileList = sys.argv[1:]
    if not fileList:
        fileList = [os.getcwd()]
    excluded = []
    print fileList
    if '-x' in fileList:
        excluded = fileList[fileList.index('-x'):]
        fileList = fileList[:fileList.index('-x') + 1]
    process(fileList, excluded)


