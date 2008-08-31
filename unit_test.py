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
        codeFinder.setFilename('TestModule.py')
        compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
        try:
            return eval(repr(codeFinder.classes))['TestModule']
        except:
            print 'EXCEPTION WHEN EVALING:'
            print repr(codeFinder.classes)
            print '=-' * 20
            raise

    def testEmptyModule(self):
        out = self.getModule("")
        expected = {}
        self.assertClasses(out, expected)

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
    return dict(word=name, abbr='%s()' % name, kind='m', menu='Module:%s' % klass)
def compFunc(name):
    return dict(word=name, abbr='%s()' % name, kind='f', menu='Module')
def compConst(name):
    return dict(word=name, kind='d', menu='Module')
def compProp(name, klass):
    return dict(word=name, kind='m', menu='Module:%s' % klass)
def compClass(name):
    return dict(word=name, abbr='%s()' % name,  kind='t', menu='Module')
class MockVim(object):
    class _current(object):
        class _window(object):
            cursor = (-1, -1)
        buffer = []
        window = _window()
    current = _current()
class CompletionTest(unittest.TestCase):
    def setUp(self):
        self.pysmelldict = {'Module': {
                'CONSTANTS' : ['aconstant', 'bconst'],
                'FUNCTIONS' : [('a', [], ''), ('arg', [], ''), ('b', [], '')],
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

    def testFindBase(self):
        self.vim.current.buffer = ['aaaa', 'hehe.bbbb', 'cccc']
        self.vim.current.window.cursor =(2, 6)
        index = findBase(self.vim)
        word = findWord(self.vim)
        self.assertEquals(index, 4)
        self.assertEquals(word, 'hehe.bb')

    def testCompletions(self):
        compls = findCompletions('b', 'b', self.pysmelldict)
        expected = [compFunc('b'), compClass('bClass'), compConst('bconst')]
        self.assertEquals(compls, expected)

    def testCompleteMembers(self):
        compls = findCompletions('somethign.a', 'a', self.pysmelldict)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass')]
        self.assertEquals(compls, expected)

    def testCompleteArgumentLists(self):
        self.fail('test how argument lists are filled in')
        

if __name__ == '__main__':
    unittest.main()
