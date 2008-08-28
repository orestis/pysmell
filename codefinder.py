from compiler import ast

class ClassDict(object):
    def __init__(self):
        self._modules = {}

    def enterModule(self, module):
        self.currentModule = module
        self._modules[module] = {'CLASSES': {}, 'FUNCTIONS': [], 'CONSTANTS': []}

    def exitModule(self):
        self.currentModule = None

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

    def __repr__(self):
        return repr(self._modules)


def VisitChildren(fun):
    def decorated(self, *args, **kwargs):
        fun(self, *args, **kwargs)
        self.handleChildren(args[0])
    return decorated

class CodeFinder(object):
    def __init__(self):
        self.scope = []
        self.checkers = {}
        self.classes = ClassDict()
        self.accesses = {}
        self.module = '__main__'

    def setFilename(self, filename):
        self.module = filename[:-3]

    def addChecker(self, nodeType, func):
        self.checkers.setdefault(nodeType, []).append(func)

    @property
    def inClass(self):
        return len(self.scope) > 0 and (isinstance(self.scope[-1], ast.Class) or self.inClassFunction)

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

    OTHER = set(['Add', 'And', 'Assign', 'Assert', 'AssTuple', 'AugAssign',
                'Break', 'Bitand', 'Bitor', 'Bitxor', 'CallFunc', 'Compare', 'Const', 'Continue', 'Dict',
                'Discard', 'Div', 'Exec', 'If', 'FloorDiv', 'For', 'From', 'GenExpr', 'GenExprIf', 'GenExprInner',
                'GenExprFor', 'Global', 'Import', 'Keyword', 'Lambda', 'List', 'ListComp',
                'ListCompFor', 'ListCompIf', 'Mod', 'Mul', 'Name', 'Not', 'Or',
                'Pass', 'Power', 'Printnl', 'Raise', 'Return', 'Slice', 'Sliceobj', 'Stmt', 'Sub', 'Subscript',
                'Tuple', 'TryExcept', 'TryFinally', 'UnaryAdd', 'UnarySub', 'While', 'Yield'])

    def __getattr__(self, attr):
        if attr[5:] in self.OTHER:
            return self.handleChildren

    def handleChildren(self, node):
        for c in node.getChildNodes():
            self.visit(c)

    def visitModule(self, node):
        self.classes.enterModule(self.module)
        self.visit(node.node)
        self.classes.exitModule()

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
                    self.classes.addProperty(self.currentClass, node.attrname)

    @VisitChildren
    def visitAssName(self, node):
        if self.inClass and len(self.scope) == 1:
            self.classes.addProperty(self.currentClass, node.name)
        elif len(self.scope) == 0:
            self.classes.addProperty(None, node.name)

    def visitClass(self, klass):
        self.enterScope(klass)
        if len(self.scope) == 1:
            self.classes.enterClass(klass.name, [getName(b) for b in klass.bases], klass.doc or '')
        self.visit(klass.code)
        self.exitScope()

    def visitFunction(self, func):
        for check in self.checkers.get('Function', []):
            check(self, func)

        self.accesses = {}
        self.enterScope(func)
        if self.inClassFunction:
            if func.name != '__init__':
                if func.decorators and 'property' in [getName(n) for n in func.decorators]:
                    self.classes.addProperty(self.currentClass, func.name)
                else:
                    self.classes.addMethod(self.currentClass, func.name, getFuncArgs(func), func.doc or "")
            else:
                self.classes.setConstructor(self.currentClass, getFuncArgs(func))
        elif len(self.scope) == 1:
            self.classes.addFunction(func.name, getFuncArgs(func, inClass=False), func.doc or "")

        self.visit(func.code)
        self.exitScope()

        for name, attrs in self.accesses.items():
            for klass, classattrs in self.classes.items():
                if attrs.issubset(classattrs):
                    print name, 'looks like', klass



def getName(node):
    if isinstance(node, (ast.Class, ast.Name, ast.Function)):
        return node.name
    #if isinstance(node, (ast.CallFunc),):
        #return node.node.name
    if isinstance(node, (ast.Const),):
        return str(node.value)
    if isinstance(node, (ast.Getattr, ast.Tuple, ast.CallFunc, ast.Lambda),):
        return '.'.join(map(getName, node.getChildNodes()))
    raise 'Unknown node: %r %r' % (node, dir(node))

            

def getFuncArgs(func, inClass=True):
    args = func.argnames[:]
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
    for default in func.defaults:
        name = getName(default)
        if name not in ('None', 'True', 'False'):
            name = repr(name)
        args[-offset] = args[-offset] + "=" + name

    return args

