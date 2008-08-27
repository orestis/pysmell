from compiler import ast

class ClassDict(object):
    def __init__(self):
        self._classes = {}

    def addClass(self, klass):
        self._classes[klass] = {}
        self._classes[klass]['methods'] = []
        self._classes[klass]['properties'] = []
        self._classes[klass]['constructor'] = []

    def addMethod(self, klass, method, args, docstring):
        if (method, args, docstring) not in self._classes[klass]['methods']:
            self._classes[klass]['methods'].append((method, args, docstring))

    def addProperty(self, klass, prop):
        if prop not in self._classes[klass]['properties']:
            self._classes[klass]['properties'].append(prop)

    def setConstructor(self, klass, args):
        self._classes[klass]['constructor'] = args

    def __repr__(self):
        return repr(self._classes)


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

    OTHER = set(['Add', 'And', 'Assign', 'Assert', 'AssName', 'AssTuple', 'AugAssign',
                'Break', 'Bitand', 'Bitor', 'Bitxor', 'CallFunc', 'Compare', 'Const', 'Continue', 'Dict',
                'Discard', 'Div', 'If', 'FloorDiv', 'For', 'From', 'GenExpr', 'GenExprIf', 'GenExprInner',
                'GenExprFor', 'Global', 'Import', 'Keyword', 'Lambda', 'List', 'ListComp',
                'ListCompFor', 'ListCompIf', 'Module', 'Mod', 'Mul', 'Name', 'Not', 'Or',
                'Pass', 'Power', 'Printnl', 'Raise', 'Return', 'Slice', 'Stmt', 'Sub', 'Subscript',
                'Tuple', 'TryExcept', 'TryFinally', 'UnarySub', 'While', 'Yield'])

    def __getattr__(self, attr):
        if attr[5:] in self.OTHER:
            return self.handleChildren

    def handleChildren(self, node):
        for c in node.getChildNodes():
            self.visit(c)


    @VisitChildren
    def visitGetattr(self, node):
        if self.inClass:
            if isinstance(node.expr, ast.Name):
                if node.expr.name == 'self':
                    pass
#                    print 'in class, self Accessing', node.attrname, 'of', self.currentClass
            elif isinstance(node.expr, ast.CallFunc):
                pass
#                print 'in class, trying to access %s attr of %s' % (node.attrname, node.expr)
            else:
                pass
#                print 'in class, Accessing', node.attrname, 'of', node.expr
#        else:
#            self.accesses.setdefault(node.expr.name, set([])).add(node.attrname)

    @VisitChildren
    def visitAssAttr(self, node):
        if self.inClass:
            if isinstance(node.expr, ast.Name):
                if node.expr.name == 'self':
                    self.classes.addProperty(self.currentClass, node.attrname)
                    return
#        print 'assigning', node.expr, node.attrname


    def visitClass(self, klass):
        self.enterScope(klass)
        self.classes.addClass(klass.name)
        self.visit(klass.code)
        self.exitScope()

    def visitFunction(self, func):
        for check in self.checkers.get('Function', []):
            check(self, func)

        self.accesses = {}
        if self.inClass:
            if func.name != '__init__':
                if func.decorators and 'property' in [getName(n) for n in func.decorators]:
                    self.classes.addProperty(self.currentClass, func.name)
                else:
                    self.classes.addMethod(self.currentClass, func.name, func.argnames[1:], func.doc or "")
            else:
                self.classes.setConstructor(self.currentClass, func.argnames[1:])

        self.visit(func.code)

        for name, attrs in self.accesses.items():
            for klass, classattrs in self.classes.items():
                if attrs.issubset(classattrs):
                    print name, 'looks like', klass



def getName(node):
    if isinstance(node, (ast.Class, ast.Name, ast.Function)):
        return node.name
    if isinstance(node, (ast.CallFunc),):
        return node.node.name
    raise 'Unknown node', type(node)

            

