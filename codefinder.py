import sys
import compiler
from compiler import ast

def VisitChildren(fun):
    def decorated(self, *args, **kwargs):
        fun(self, *args, **kwargs)
        self.handleChildren(args[0])
    return decorated

class CodeFinder(object):
    def __init__(self):
        self.scope = []
        self.checkers = {}

    def addChecker(self, nodeType, func):
        self.checkers.setdefault(nodeType, []).append(func)

    @property
    def inClass(self):
        return bool(self.scope) and isinstance(self.scope[0], ast.Class)

    def enterScope(self, node):
        self.scope.insert(0, node)

    def exitScope(self):
        self.scope.pop()

    @property
    def currentClass(self):
        return self.inClass and self.scope[0].name or None

    OTHER = set(['Assign', 'AssName', 'Stmt', 'CallFunc', 'Const', 'Module',
                 'Discard', 'Printnl'])

    def __getattr__(self, attr):
        if attr[5:] in self.OTHER:
            return self.handleChildren

    def handleChildren(self, node):
        for c in node.getChildNodes():
            self.visit(c)

    @VisitChildren
    def visitName(self, node):
        print node.name

    @VisitChildren
    def visitGetattr(self, node):
        print node.expr,
        print node.attrname

    def visitClass(self, klass):
        self.enterScope(klass)
        print klass.name
        self.visit(klass.code)
        self.exitScope()

    @VisitChildren
    def visitFunction(self, func):
        for check in self.checkers.get('Function', []):
            check(self, func)

source = """
class Aclass(object):
    def do_stuff(salf):
        a = 1
        print a

    def do_other_stuff():
        self.bar().do_stuff()

def test(aname):
    aname.do_stuff()
    aname.do_other_stuff()
"""

def self_argument(self, func):
    if self.inClass:
        if func.argnames:
            if func.argnames[0] != 'self':
                print ('self! in class %s, function %s, line %d' %
                    (self.currentClass, func.name, func.lineno))
        else:
            print ('no args!')

if __name__ == '__main__':
    from compiler.visitor import ExampleASTVisitor
    if len(sys.argv) > 1:
        source = open(sys.argv[1], 'r').read()
    tree = compiler.parse(source)
    codeFinder = CodeFinder()
    codeFinder.addChecker('Function', self_argument)
    compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
