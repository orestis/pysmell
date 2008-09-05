# codefinder.py
# Statically analyze python code
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# pysmell v0.2
# http://orestis.gr

# Released subject to the BSD License 

import os
from compiler import ast

class ModuleDict(dict):
    def __init__(self):
        self._modules = {}

    def enterModule(self, module):
        self.currentModule = module
        self._modules[module] = {'CLASSES': {}, 'FUNCTIONS': [], 'CONSTANTS': []}

    def exitModule(self):
        self.currentModule = None

    def isModuleEmpty(self, module):
        return self._modules[module] == {'CLASSES': {}, 'FUNCTIONS': [], 'CONSTANTS': []}

    def currentClass(self, klass):
        return self._modules[self.currentModule]['CLASSES'][klass]

    def enterClass(self, klass, bases, docstring):
        self._modules[self.currentModule]['CLASSES'][klass] = {}
        self._modules[self.currentModule]['CLASSES'][klass]['methods'] = []
        self._modules[self.currentModule]['CLASSES'][klass]['properties'] = []
        self._modules[self.currentModule]['CLASSES'][klass]['constructor'] = []
        self._modules[self.currentModule]['CLASSES'][klass]['bases'] = bases
        self._modules[self.currentModule]['CLASSES'][klass]['docstring'] = docstring

    def addMethod(self, klass, method, args, docstring):
        if (method, args, docstring) not in self.currentClass(klass)['methods']:
            self.currentClass(klass)['methods'].append((method, args, docstring))

    def addFunction(self, function, args, docstring):
        self._modules[self.currentModule]['FUNCTIONS'].append((function, args, docstring))

    def addProperty(self, klass, prop):
        if klass is not None:
            if prop not in self.currentClass(klass)['properties']:
                self.currentClass(klass)['properties'].append(prop)
        else:
            self._modules[self.currentModule]['CONSTANTS'].append(prop)

    def setConstructor(self, klass, args):
        self._modules[self.currentModule]['CLASSES'][klass]['constructor'] = args

    def update(self, other):
        if other:
            self._modules.update(other._modules)

    def keys(self):
        return [k for k in self._modules.keys() if not self.isModuleEmpty(k)]

    def values(self):
        return [self._modules[k] for k in self.keys()]

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        return ((k, self._modules[k]) for k in self.keys())

    def __getitem__(self, item):
        return self._modules[item]

    def __len__(self):
        return len(self.keys())


def VisitChildren(fun):
    def decorated(self, *args, **kwargs):
        fun(self, *args, **kwargs)
        self.handleChildren(args[0])
    return decorated

class BaseVisitor(object):
    def __init__(self):
        self.scope = []


    OTHER = set(['Add', 'And', 'Assign', 'Assert', 'AssName', 'AssTuple',
                'AugAssign', 'Backquote', 'Break', 'Bitand', 'Bitor', 'Bitxor', 'CallFunc',
                'Compare', 'Const', 'Continue', 'Dict', 'Discard', 'Div', 'Exec',
                'FloorDiv', 'For', 'From', 'Function', 'GenExpr', 'GenExprIf',
                'GenExprInner', 'GenExprFor', 'Getattr', 'Global', 'If', 'Import',
                'Invert', 'Keyword', 'Lambda', 'LeftShift', 'List', 'ListComp',
                'ListCompFor', 'ListCompIf', 'Module', 'Mod', 'Mul', 'Name', 'Not', 'Or',
                'Pass', 'Power', 'Print', 'Printnl', 'Raise', 'Return', 'RightShift',
                'Slice', 'Sliceobj', 'Stmt', 'Sub', 'Subscript', 'Tuple', 'TryExcept',
                'TryFinally', 'UnaryAdd', 'UnarySub', 'While', 'Yield'])

    def __getattr__(self, attr):
        if attr[5:] in self.OTHER:
            return self.handleChildren

    def handleChildren(self, node):
        for c in node.getChildNodes():
            self.visit(c)

class CodeFinder(BaseVisitor):
    def __init__(self):
        BaseVisitor.__init__(self)
        self.modules = ModuleDict()
        self.module = '__module__'
        self.package = '__package__'

    @property
    def inClass(self):
        return (len(self.scope) > 0 and (isinstance(self.scope[-1], ast.Class)
                    or self.inClassFunction))

    @property
    def inClassFunction(self):
        return (len(self.scope) == 2 and 
                isinstance(self.scope[-1], ast.Function) and
                isinstance(self.scope[-2], ast.Class))

    def enterScope(self, node):
        self.scope.append(node)

    def exitScope(self):
        self.scope.pop()

    @property
    def currentClass(self):
        if self.inClassFunction:
            return self.scope[-2].name
        elif self.inClass:
            return self.scope[-1].name
        return None
    def setModule(self, module):
        self.module = module

    def setPackage(self, package):
        self.package = package

    def visitModule(self, node):
        if self.module == '__init__':
            self.modules.enterModule('%s' % self.package)
        else:
            self.modules.enterModule('%s.%s' % (self.package, self.module))
        self.visit(node.node)
        self.modules.exitModule()

    @VisitChildren
    def visitGetattr(self, node):
        if self.inClass:
            if isinstance(node.expr, ast.Name):
                if node.expr.name == 'self':
                    pass
            elif isinstance(node.expr, ast.CallFunc):
                pass

    @VisitChildren
    def visitAssAttr(self, node):
        if self.inClassFunction:
            if isinstance(node.expr, ast.Name):
                if node.expr.name == 'self':
                    self.modules.addProperty(self.currentClass, node.attrname)

    @VisitChildren
    def visitAssName(self, node):
        if self.inClass and len(self.scope) == 1:
            self.modules.addProperty(self.currentClass, node.name)
        elif len(self.scope) == 0:
            self.modules.addProperty(None, node.name)

    def visitClass(self, klass):
        self.enterScope(klass)
        if len(self.scope) == 1:
            self.modules.enterClass(klass.name, [getName(b) for b in
                                        klass.bases], klass.doc or '')
        self.visit(klass.code)
        self.exitScope()

    def visitFunction(self, func):
        self.enterScope(func)
        if self.inClassFunction:
            if func.name != '__init__':
                if func.decorators and 'property' in [getName(n) for n in func.decorators]:
                    self.modules.addProperty(self.currentClass, func.name)
                else:
                    self.modules.addMethod(self.currentClass, func.name,
                                    getFuncArgs(func), func.doc or "")
            else:
                self.modules.setConstructor(self.currentClass, getFuncArgs(func))
        elif len(self.scope) == 1:
            self.modules.addFunction(func.name, getFuncArgs(func,
                                inClass=False), func.doc or "")

        self.visit(func.code)
        self.exitScope()


def getNameTwo(template, left, right, leftJ='', rightJ=''):
    return template % (leftJ.join(map(getName, ast.flatten(left))),
                        rightJ.join(map(getName, ast.flatten(right))))
    

def getName(node):
    if node is None: return ''
    if isinstance(node, (basestring, int, float)):
        return str(node)
    if isinstance(node, (ast.Class, ast.Name, ast.Function)):
        return node.name
    if isinstance(node, ast.Dict):
        pairs = ['%s: %s' % pair for pair in [(getName(first), getName(second))
                        for (first, second) in node.items]]
        return '{%s}' % ', '.join(pairs)
    if isinstance(node, ast.CallFunc):
        notArgs = [n for n in node.getChildNodes() if n not in node.args]
        return getNameTwo('%s(%s)', notArgs, node.args, rightJ=', ')
    if isinstance(node, ast.Const):
        return str(node.value)
    if isinstance(node, ast.LeftShift):
        return getNameTwo('%s<<%s', node.left, node.right)
    if isinstance(node, ast.RightShift):
        return getNameTwo('%s>>%s', node.left, node.right)
    if isinstance(node, ast.Mul):
        return getNameTwo('%s*%s', node.left, node.right)
    if isinstance(node, ast.UnarySub):
        return '-%s' % ''.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.List):
        return '[%s]' % ', '.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.Tuple):
        return '(%s)' % ', '.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.Lambda):
        return 'lambda %s: %s' % (', '.join(map(getName, node.argnames)), getName(node.code))
    if isinstance(node, ast.Getattr):
        return '.'.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.Compare):
        rhs = node.asList()[-1]
        return '%s %r' % (' '.join(map(getName, node.getChildren()[:-1])), rhs.value)
    if isinstance(node, ast.Slice):
        children = node.getChildren()
        return '%s[%s%s]' % (getName(children[0]), ':', children[-1].value)
    raise 'Unknown node: %r %r' % (node, dir(node))


def argToStr(arg):
    if isinstance(arg, tuple):
        if len(arg) == 1:
            return '(%s,)' % argToStr(arg[0])
        return '(%s)' % ', '.join(argToStr(elem) for elem in arg)
    return arg
            

def getFuncArgs(func, inClass=True):
    args = map(argToStr, func.argnames[:])
    if func.kwargs and func.varargs:
        args[-1] = '**' + args[-1]
        args[-2] = '*' + args[-2]
    elif func.kwargs:
        args[-1] = '**' + args[-1]
    elif func.varargs:
        args[-1] = '*' + args[-1]

    if inClass:
        args = args[1:]

    offset = bool(func.varargs) + bool(func.kwargs) + 1
    for default in reversed(func.defaults):
        name = getName(default)
        if isinstance(default, ast.Const):
            name = repr(default.value)
        args[-offset] = args[-offset] + "=" + name
        offset += 1

    return args


def getClassDict(path, codeFinder=None):
    tree = compiler.parseFile(path)
    if codeFinder is None:
        codeFinder = CodeFinder()
    compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
    return codeFinder.modules


def processFile(f, path, root):
    codeFinder = CodeFinder()
    head, tail = os.path.split(path)
    packageHieararchy = [tail]
    while head:
        head, tail = os.path.split(head)
        packageHieararchy.append(tail)
    packageHieararchy.reverse()

    index = packageHieararchy.index(root)
    package = '.'.join(packageHieararchy[index:])

    codeFinder.setPackage(package)
    codeFinder.setModule(f[:-3])
    try:
        modules = getClassDict(os.path.join(path, f), codeFinder)
        return modules
    except:
        print '-=#=- '* 10
        print 'EXCEPTION in', os.path.join(path, f)
        print '-=#=- '* 10
        return None
        

class SelfInferer(BaseVisitor):
    def __init__(self):
        BaseVisitor.__init__(self)
        self.classRanges = []
        self.lastlineno = 1

    def handleChildren(self, node):
        self.lastlineno = node.lineno
        BaseVisitor.handleChildren(self, node)

    def visitClass(self, klassNode):
        self.visit(klassNode.code)
        nestedStart, nestedEnd = None, None
        for klass, start, end in self.classRanges:
            if start > klassNode.lineno and end < self.lastlineno:
                nestedStart, nestedEnd = start, end
                
            
        if nestedStart == nestedEnd == None:
            self.classRanges.append((klassNode.name, klassNode.lineno, self.lastlineno))
        else:
            start, end = klassNode.lineno, self.lastlineno
            self.classRanges.append((klassNode.name, start, nestedStart-1))
            self.classRanges.append((klassNode.name, nestedEnd+1, end))
        self.lastlineno = klassNode.lineno
            




import compiler
from compiler.visitor import ExampleASTVisitor

def infer(source, lineNo):
    sourceLines = source.splitlines()
    try:
        tree = compiler.parse(source)
    except:
        line = sourceLines[lineNo-1]
        unindented = line.lstrip()
        indentation = len(line) - len(unindented)
        sourceLines[lineNo-1] = '%spass' % (' ' * indentation)

        replacedSource = '\n'.join(sourceLines)
        tree = compiler.parse(replacedSource)
            

    inferer = SelfInferer()
    compiler.walk(tree, inferer, walker=ExampleASTVisitor(), verbose=1)
    classRanges = inferer.classRanges
    classRanges.sort(sortClassRanges)
    
    for klass, start, end in classRanges:
        if lineNo >= start:
            return klass
    return None

def sortClassRanges(a, b):
    return b[1] - a[1]

