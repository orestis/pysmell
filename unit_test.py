import unittest
from textwrap import dedent
import compiler
from compiler.visitor import ExampleASTVisitor

from codefinder import CodeFinder

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


if __name__ == '__main__':
    unittest.main()
