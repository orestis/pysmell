# codefinder.py
# Statically analyze python code
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# http://orestis.gr

# Released subject to the BSD License 

import os
import sys
import __builtin__
import compiler

from compiler import ast

class ModuleDict(dict):
    def __init__(self):
        self._modules = {'CLASSES': {}, 'FUNCTIONS': [], 'CONSTANTS': [], 'POINTERS': {}, 'HIERARCHY': []}

    def enterModule(self, module):
        self.currentModule = module
        self['HIERARCHY'].append(module)

    def exitModule(self):
        self.currentModule = None

    def currentClass(self, klass):
        fullClass = "%s.%s" % (self.currentModule, klass)
        return self['CLASSES'][fullClass]

    def enterClass(self, klass, bases, docstring):
        fullClass = "%s.%s" % (self.currentModule, klass)
        self['CLASSES'][fullClass] = {}
        self['CLASSES'][fullClass]['methods'] = []
        self['CLASSES'][fullClass]['properties'] = []
        self['CLASSES'][fullClass]['constructor'] = []
        self['CLASSES'][fullClass]['bases'] = bases
        self['CLASSES'][fullClass]['docstring'] = docstring

    def addMethod(self, klass, method, args, docstring):
        if (method, args, docstring) not in self.currentClass(klass)['methods']:
            self.currentClass(klass)['methods'].append((method, args, docstring))

    def addPointer(self, name, pointer):
        self['POINTERS'][name] = pointer

    def addFunction(self, function, args, docstring):
        fullFunction = "%s.%s" % (self.currentModule, function)
        self['FUNCTIONS'].append((fullFunction, args, docstring))

    def addProperty(self, klass, prop):
        if klass is not None:
            if prop not in self.currentClass(klass)['properties']:
                self.currentClass(klass)['properties'].append(prop)
        else:
            fullProp = "%s.%s" % (self.currentModule, prop)
            self['CONSTANTS'].append(fullProp)

    def setConstructor(self, klass, args):
        fullClass = "%s.%s" % (self.currentModule, klass)
        self['CLASSES'][fullClass]['constructor'] = args

    def update(self, other):
        if other:
            self['CONSTANTS'].extend(other['CONSTANTS'])
            self['FUNCTIONS'].extend(other['FUNCTIONS'])
            self['HIERARCHY'].extend(other['HIERARCHY'])
            self['CLASSES'].update(other['CLASSES'])
            self['POINTERS'].update(other['POINTERS'])

    def keys(self):
        return self._modules.keys()

    def values(self):
        return self._modules.values()

    def items(self):
        return self._modules.items()

    def iteritems(self):
        return self._modules.iteritems()

    def __getitem__(self, item):
        return self._modules[item]

    def __len__(self):
        return len(self.keys())

    def __eq__(self, other):
        return ((isinstance(other, ModuleDict) and other._modules == self._modules) or
               (isinstance(other, dict) and other == self._modules))
              

    def __ne__(self, other):
        return not self == other


def VisitChildren(fun):
    def decorated(self, *args, **kwargs):
        fun(self, *args, **kwargs)
        self.handleChildren(args[0])
    return decorated


class BaseVisitor(object):
    def __init__(self):
        self.scope = []
        self.imports = {}


    def handleChildren(self, node):
        for c in node.getChildNodes():
            self.visit(c)

    @VisitChildren
    def visitFrom(self, node):
        for name in node.names:
            asName = name[1] or name[0]
            self.imports[asName] = "%s.%s" % (node.modname, name[0])

    @VisitChildren
    def visitImport(self, node):
        for name in node.names:
            asName = name[1] or name[0]
            self.imports[asName] = name[0]

    def qualify(self, name, curModule):
        if hasattr(__builtin__, name):
            return name
        if name in self.imports:
            return self.imports[name]
        for imp in self.imports:
            if name.startswith(imp):
                actual = self.imports[imp]
                return "%s%s" % (actual, name[len(imp):])
        if curModule:
            return '%s.%s' % (curModule, name)
        else:
            return name

class CodeFinder(BaseVisitor):
    def __init__(self):
        BaseVisitor.__init__(self)
        self.modules = ModuleDict()
        self.module = '__module__'
        self.__package = '__package__'
        self.path = '__path__'

    
    def __setPackage(self, package):
        if package:
            self.__package = package + '.'
        else:
            self.__package = ''

    package = property(lambda s: s.__package, __setPackage)

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

    def visitModule(self, node):
        if self.module == '__init__':
            self.modules.enterModule('%s' % self.package[:-1]) # remove dot
        else:
            self.modules.enterModule('%s%s' % (self.package, self.module))
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

    def visitFrom(self, node):
        BaseVisitor.visitFrom(self, node)
        for name in node.names:
            asName = name[1] or name[0]
            imported = name[0]
            if self.isRelativeImport(node.modname):
                imported = "%s%s.%s" % (self.package, node.modname, imported)
            else:
                imported = "%s.%s" % (node.modname, imported)
            self.modules.addPointer("%s.%s" % (self.modules.currentModule, asName), imported)

    def visitImport(self, node):
        BaseVisitor.visitImport(self, node)
        for name in node.names:
            asName = name[1] or name[0]
            imported = name[0]
            if self.isRelativeImport(imported):
                imported = "%s%s" % (self.package, imported)
            self.modules.addPointer("%s.%s" % (self.modules.currentModule, asName), imported)

    def isRelativeImport(self, imported):
        pathToImport = os.path.join(self.path, *imported.split('.'))
        return os.path.exists(pathToImport) or os.path.exists(pathToImport + '.py')
        
    def visitClass(self, klass):
        self.enterScope(klass)
        if len(self.scope) == 1:
            bases = [self.qualify(getName(b), self.modules.currentModule) for b in klass.bases]
            self.modules.enterClass(klass.name, bases, klass.doc or '')
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
    return template % (leftJ.join(map(getName, left)),
                        rightJ.join(map(getName, right)))

MATHNODES = {
    ast.Add: '+',
    ast.Sub: '-',
    ast.Mul: '*',
    ast.Power: '**',
    ast.Div: '/',
    ast.Mod: '%',
}

def getNameMath(node):
    return '%s%s%s' % (getName(node.left), MATHNODES[node.__class__], getName(node.right))


def getName(node):
    if node is None: return ''
    if isinstance(node, (basestring, int, long, float)):
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
        try:
            float(node.value)
            return str(node.value)
        except:
            return repr(str(node.value))
    if isinstance(node, ast.LeftShift):
        return getNameTwo('%s<<%s', node.left, node.right)
    if isinstance(node, ast.RightShift):
        return getNameTwo('%s>>%s', node.left, node.right)
    if isinstance(node, (ast.Mul, ast.Add, ast.Sub, ast.Power, ast.Div, ast.Mod)):
        return getNameMath(node)
    if isinstance(node, ast.Bitor):
        return '|'.join(map(getName, node.nodes))
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
        slices = children[2:]
        formSlices = []
        for sl in slices:
            if sl is None:
                formSlices.append('')
            else:
                formSlices.append(getName(sl))
        sliceStr = ':'.join(formSlices)
        return '%s[%s]' % (getName(children[0]), sliceStr)
    if isinstance(node, ast.Not):
        return "not %s" % ''.join(map(getName, ast.flatten(node)))
    if isinstance(node, ast.Or):
        return " or ".join(map(getName, node.nodes))
    if isinstance(node, ast.And):
        return " and ".join(map(getName, node.nodes))
    if isinstance(node, ast.Keyword):
        return "%s=%s" % (node.name, getName(node.expr))
    return repr(node)


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
    compiler.walk(tree, codeFinder)
    return codeFinder.modules


def findRootPackageList(directory, filename):
    "should walk up the tree until there is no __init__.py"
    isPackage = lambda path: os.path.exists(os.path.join(path, '__init__.py'))
    if not isPackage(directory):
        return []
    packages = []
    while directory and isPackage(directory):
        directory, tail = os.path.split(directory)
        if tail:
            packages.append(tail)
    packages.reverse()
    return packages


def findPackage(path):
    packages = findRootPackageList(path, "")
    package = '.'.join(packages)
    return package


def processFile(f, path):
    """f is the the filename, path is the relative path in the project, root is
    the topmost package"""
    codeFinder = CodeFinder()

    package = findPackage(path)
    codeFinder.package = package
    codeFinder.module = f[:-3]
    codeFinder.path = path
    try:
        assert os.path.isabs(path), "path should be absolute"
        modules = getClassDict(os.path.join(path, f), codeFinder)
        return modules
    except Exception, e:
        print '-=#=- '* 10
        print 'EXCEPTION in', os.path.join(path, f)
        print e
        print '-=#=- '* 10
        return None


def analyzeFile(fullPath, tree):
    if tree is None:
        return None
    codeFinder = CodeFinder()
    absPath, filename = os.path.split(fullPath)
    codeFinder.module = filename[:-3]
    codeFinder.path = absPath
    package = findPackage(absPath)
    codeFinder.package = package
    compiler.walk(tree, codeFinder)
    return codeFinder.modules
        

class SelfInferer(BaseVisitor):
    def __init__(self):
        BaseVisitor.__init__(self)
        self.classRanges = []
        self.lastlineno = 1

    def __getattr__(self, _):
        return self.handleChildren

    def handleChildren(self, node):
        self.lastlineno = node.lineno
        BaseVisitor.handleChildren(self, node)


    def visitClass(self, klassNode):
        self.visit(klassNode.code)
        nestedStart, nestedEnd = None, None
        for klass, _, start, end in self.classRanges:
            if start > klassNode.lineno and end < self.lastlineno:
                nestedStart, nestedEnd = start, end
            
        bases = [self.qualify(getName(b), None) for b in klassNode.bases]
        if nestedStart == nestedEnd == None:
            self.classRanges.append((klassNode.name, bases, klassNode.lineno, self.lastlineno))
        else:
            start, end = klassNode.lineno, self.lastlineno
            self.classRanges.append((klassNode.name, bases, start, nestedStart-1))
            self.classRanges.append((klassNode.name, bases, nestedEnd+1, end))
        self.lastlineno = klassNode.lineno


def getSafeTree(source, lineNo):
    source = source.replace('\r\n', '\n')
    try:
        tree = compiler.parse(source)
    except:
        sourceLines = source.splitlines()
        line = sourceLines[lineNo-1]
        unindented = line.lstrip()
        indentation = len(line) - len(unindented)
        whitespace = ' '
        if line.startswith('\t'):
            whitespace = '\t'
        sourceLines[lineNo-1] = '%spass' % (whitespace * indentation)

        replacedSource = '\n'.join(sourceLines)
        try:
            tree = compiler.parse(replacedSource)
        except SyntaxError, e:
            print >> sys.stderr, e.args
            return None

    return tree

class NameVisitor(BaseVisitor):
    def __init__(self):
        BaseVisitor.__init__(self)
        self.names = {}
        self.klasses = []
        self.lastlineno = 1


    def handleChildren(self, node):
        self.lastlineno = node.lineno
        BaseVisitor.handleChildren(self, node)


    @VisitChildren
    def visitAssign(self, node):
        assNode = node.nodes[0]
        name = None
        if isinstance(assNode, ast.AssName):
            name = assNode.name
        elif isinstance(assNode, ast.AssAttr):
            name = assNode.attrname
        self.names[name] = getName(node.expr)

    @VisitChildren
    def visitClass(self, node):
        self.klasses.append(node.name)


def getNames(tree):
    if tree is None:
        return None
    inferer = NameVisitor()
    compiler.walk(tree, inferer)
    names = inferer.names
    names.update(inferer.imports)
    return names, inferer.klasses
    


def getImports(tree):
    if tree is None:
        return None
    inferer = BaseVisitor()
    compiler.walk(tree, inferer)

    return inferer.imports


def getClassAndParents(tree, lineNo):
    if tree is None:
        return None, []

    inferer = SelfInferer()
    compiler.walk(tree, inferer)
    classRanges = inferer.classRanges
    classRanges.sort(sortClassRanges)
    
    for klass, parents, start, end in classRanges:
        if lineNo >= start:
            return klass, parents
    return None, []

def sortClassRanges(a, b):
    return b[2] - a[2]

