import unittest
from textwrap import dedent
import compiler
from compiler.visitor import ExampleASTVisitor

from codefinder import CodeFinder
from vimhelper import findCompletions, findWord, findBase

class CodeFinderTest(unittest.TestCase):
    def getModule(self, source):
        tree = compiler.parse(dedent(source))
        codeFinder = CodeFinder()
        codeFinder.setModule('TestModule')
        codeFinder.setPackage('TestPackage')
        compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
        try:
            return eval(repr(codeFinder.modules))['TestPackage.TestModule']
        except:
            print 'EXCEPTION WHEN EVALING:'
            print repr(codeFinder.modules)
            print '=-' * 20
            raise

    def testEmpty(self):
        tree = compiler.parse("")
        codeFinder = CodeFinder()
        codeFinder.setModule('TestModule')
        codeFinder.setPackage('TestPackage')
        compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
        self.assertTrue(codeFinder.modules.isModuleEmpty('TestPackage.TestModule'), 'should be empty')
        self.assertEquals(repr(codeFinder.modules), "")


    def testOnlyPackage(self):
        source = """
        class A(object):
            pass
        """
        tree = compiler.parse(dedent(source))
        codeFinder = CodeFinder()
        codeFinder.setPackage('TestPackage')
        codeFinder.setModule('__init__')
        compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
        expected = {'TestPackage': {'CLASSES': {'A': dict(docstring='', bases=['object'], constructor=[], methods=[], properties=[])},
            'FUNCTIONS': [], 'CONSTANTS': []}
        }
        actual = eval(repr(codeFinder.modules))
        self.assertEquals(actual, expected)

    def assertClasses(self, moduleDict, expected):
        self.assertEquals(moduleDict['CLASSES'], expected)

    def testSimpleClass(self):
        out = self.getModule("""
        class A(object):
            pass
        """)
        expected = {'A': dict(bases=['object'], properties=[], methods=[], constructor=[], docstring='')}
        self.assertClasses(out, expected)

    def testAdvancedDefaultArguments(self):
        out = self.getModule("""
        def function(a=1, b=2, c=None, d=4, e='string', f=Name, g={}):
            pass
        """)
        expected = ('function', ['a=1', 'b=2', 'c=None', 'd=4', "e='string'", 'f=Name', 'g={}'], '')
        self.assertEquals(out['FUNCTIONS'], [expected])

    def testOldStyleDecoratorProperties(self):
        out = self.getModule("""
        class A:
            def __a(self):
                pass
            a = property(__a)
        """)
        expected = {'A': dict(bases=[], properties=['a'], methods=[('__a', [], '')], constructor=[], docstring='')}
        self.assertClasses(out, expected)


    def assertNamesIsHandled(self, name):
        out = self.getModule("""
        def f(a=%s):
            pass
        """ % name)
        self.assertEquals(out['FUNCTIONS'], [('f', ['a=%s' % name], '')])

    def testNames(self):
        self.assertNamesIsHandled('A.B.C(1)')
        self.assertNamesIsHandled('A.B.C()')
        self.assertNamesIsHandled('A.B.C')
        self.assertNamesIsHandled('{a: b, c: d}')
        self.assertNamesIsHandled('(a, b, c)')
        self.assertNamesIsHandled('[a, b, c]')
        self.assertNamesIsHandled('lambda a: (c, b)')
        self.assertNamesIsHandled("lambda name: name[:1] != '_'")
        self.assertNamesIsHandled("-180")
        self.assertNamesIsHandled("10*180")
        self.assertNamesIsHandled("10>>180")
        self.assertNamesIsHandled("10<<180")
        

    def testClassProperties(self):
        out = self.getModule("""
        class A(object):
            classprop = 1
            def __init__(self):
                self.plainprop = 2
                self.plainprop = 3
            @property
            def methodProp(self):
                pass
        """)
        expectedProps = ['classprop', 'plainprop', 'methodProp']
        self.assertEquals(out['CLASSES']['A']['properties'], expectedProps)

    def testClassMethods(self):
        out = self.getModule("""
        class A(object):
            def method(self):
                'random docstring'
                pass
            def methodArgs(self, arg1, arg2):
                pass
            def methodTuple(self, (x, y)):
                pass
            def methodDefaultArgs(self, arg1, arg2=None):
                pass
            def methodStar(self, arg1, *args):
                pass
            def methodKW(self, arg1, **kwargs):
                pass
            def methodAll(self, arg1, *args, **kwargs):
                pass
            def methodReallyAll(self, arg1, arg2='a string', *args, **kwargs):
                pass
        """)
        expectedMethods = [('method', [], 'random docstring'),
                           ('methodArgs', ['arg1', 'arg2'], ''),
                           ('methodTuple', ['(x, y)'], ''),
                           ('methodDefaultArgs', ['arg1', 'arg2=None'], ''),
                           ('methodStar', ['arg1', '*args'], ''),
                           ('methodKW', ['arg1', '**kwargs'], ''),
                           ('methodAll', ['arg1', '*args', '**kwargs'], ''),
                           ('methodReallyAll', ['arg1', "arg2='a string'", '*args', '**kwargs'], ''),
                           ]
        self.assertEquals(out['CLASSES']['A']['methods'], expectedMethods)

    def testTopLevelFunctions(self):
        out = self.getModule("""
        def TopFunction1(arg1, arg2=True, **spinach):
            'random docstring'
        def TopFunction2(arg1, arg2=False):
            'random docstring2'
        """)
        expectedFunctions = [('TopFunction1', ['arg1', 'arg2=True', '**spinach'], 'random docstring'),
                             ('TopFunction2', ['arg1', 'arg2=False'], 'random docstring2')]
        self.assertEquals(out['FUNCTIONS'], expectedFunctions)

    def testNestedStuff(self):
        out = self.getModule("""
        class A(object):
            def level1(self):
                class Level2(object):
                    pass
                def level2():
                    pass
                pass
            class InnerClass(object):
                def innerMethod(self):
                    pass
        """)
        self.assertEquals(len(out['CLASSES'].keys()), 1, 'should not count inner classes')
        self.assertEquals(out['CLASSES']['A']['methods'], [('level1', [], '')])
        self.assertEquals(out['FUNCTIONS'], [])

    def testModuleConstants(self):
        out = self.getModule("""
        CONSTANT = 1
        """)
        self.assertEquals(out['CONSTANTS'], ['CONSTANT'])

    def testArgToStr(self):
        from codefinder import argToStr
        self.assertEquals(argToStr('stuff'), 'stuff')
        self.assertEquals(argToStr(('ala', 'ma', 'kota')), '(ala, ma, kota)')
        self.assertEquals(argToStr((('x1', 'y1'), ('x2', 'y2'))), '((x1, y1), (x2, y2))')
        self.assertEquals(argToStr(('ala',)), '(ala,)')

def compMeth(name, klass):
    return dict(word=name, abbr='%s()' % name, kind='m', menu='Module:%s' % klass, dup='1')
def compFunc(name, args=''):
    return dict(word=name, abbr='%s(%s)' % (name, args), kind='f', menu='Module', dup='1')
def compConst(name):
    return dict(word=name, kind='d', menu='Module', dup='1')
def compProp(name, klass):
    return dict(word=name, kind='m', menu='Module:%s' % klass, dup='1')
def compClass(name):
    return dict(word=name, abbr='%s()' % name,  kind='t', menu='Module', dup='1')

class MockVim(object):
    class _current(object):
        class _window(object):
            cursor = (-1, -1)
        buffer = []
        window = _window()
    current = _current()
    command = lambda _, __:None

class CompletionTest(unittest.TestCase):
    def setUp(self):
        self.pysmelldict = {'Module': {
                'CONSTANTS' : ['aconstant', 'bconst'],
                'FUNCTIONS' : [('a', [], ''), ('arg', [], ''), ('b', ['arg1', 'arg2'], '')],
                'CLASSES' : {
                    'aClass': {
                        'constructor': [],
                        'bases': ['object'],
                        'properties': ['aprop', 'bprop'],
                        'methods': [('am', [], ''), ('bm', [], ())]
                    },
                    'bClass': {
                        'constructor': [],
                        'bases': ['AClass'],
                        'properties': ['cprop', 'dprop'],
                        'methods': [('cm', [], ''), ('dm', [], ())]
                    }
                }
            }}
        import vimhelper
        vimhelper.vim = self.vim = MockVim()

    def testFindBaseName(self):
        self.vim.current.buffer = ['aaaa', 'bbbb', 'cccc']
        self.vim.current.window.cursor =(2, 2)
        index = findBase(self.vim)
        word = findWord(self.vim, 2, 'bbbb')
        self.assertEquals(index, 0)
        self.assertEquals(word, 'bb')

    def testFindBaseMethodCall(self):
        self.vim.current.buffer = ['aaaa', 'a.bbbb(', 'cccc']
        self.vim.current.window.cursor =(2, 7)
        index = findBase(self.vim)
        word = findWord(self.vim, 7, 'a.bbbb(')
        self.assertEquals(index, 2)
        self.assertEquals(word, 'a.bbbb(')

    def testFindBaseFuncCall(self):
        self.vim.current.buffer = ['aaaa', 'bbbb(', 'cccc']
        self.vim.current.window.cursor =(2, 5)
        index = findBase(self.vim)
        word = findWord(self.vim, 5, 'bbbb(')
        self.assertEquals(index, 0)
        self.assertEquals(word, 'bbbb(')

    def testFindBaseNameIndent(self):
        self.vim.current.buffer = ['aaaa', '    bbbb', 'cccc']
        self.vim.current.window.cursor =(2, 6)
        index = findBase(self.vim)
        word = findWord(self.vim, 6, '    bbbb')
        self.assertEquals(index, 4)
        self.assertEquals(word, 'bb')

    def testFindBaseProp(self):
        self.vim.current.buffer = ['aaaa', 'hehe.bbbb', 'cccc']
        self.vim.current.window.cursor =(2, 7)
        index = findBase(self.vim)
        word = findWord(self.vim, 7, 'hehe.bbbb')
        self.assertEquals(index, 5)
        self.assertEquals(word, 'hehe.bb')

    def testFindBasePropIndent(self):
        self.vim.current.buffer = ['aaaa', '    hehe.bbbb', 'cccc']
        self.vim.current.window.cursor =(2, 11)
        index = findBase(self.vim)
        word = findWord(self.vim, 11, '    hehe.bbbb')
        self.assertEquals(index, 9)
        self.assertEquals(word, 'hehe.bb')

    def testCompletions(self):
        compls = findCompletions(self.vim, 'b', 1, 'b', self.pysmelldict)
        expected = [compFunc('b', 'arg1, arg2'), compClass('bClass'), compConst('bconst')]
        self.assertEquals(compls, expected)

    def testCompleteMembers(self):
        compls = findCompletions(self.vim, 'somethign.a', 11, 'a', self.pysmelldict)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass')]
        self.assertEquals(compls, expected)

    def testCompleteArgumentListsPropRightParen(self):
        compls = findCompletions(self.vim, 'self.bm()', 8, 'bm(', self.pysmelldict)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])
        
    def testCompleteArgumentListsProp(self):
        compls = findCompletions(self.vim, 'self.bm(', 8, 'bm(', self.pysmelldict)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])
        
    def testCompleteArgumentListsRightParen(self):
        compls = findCompletions(self.vim, '   b()', 5, 'b(', self.pysmelldict)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])

    def testCompleteArgumentLists(self):
        compls = findCompletions(self.vim, '  b(', 4, 'b(', self.pysmelldict)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])
        

if __name__ == '__main__':
    unittest.main()
