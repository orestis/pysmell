import unittest
from textwrap import dedent
import compiler
from compiler.visitor import ExampleASTVisitor

from pprint import pformat
from codefinder import CodeFinder, infer, ModuleDict
from vimhelper import findWord, findBase
from idehelper import findCompletions


class ModuleDictTest(unittest.TestCase):
    def testUpdate(self):
        total = ModuleDict()
        total.enterModule('mod1')
        total.enterClass('cls1', [], 'doc1')
        total.enterModule('mod2')
        total.enterClass('cls2', [], 'doc2')

        self.assertEquals(pformat(total), pformat(total._modules))

        md1 = ModuleDict()
        md1.enterModule('mod1')
        md1.enterClass('cls1', [], 'doc1')

        md2 = ModuleDict()
        md2.enterModule('mod2')
        md2.enterClass('cls2', [], 'doc2')

        md3 = ModuleDict()
        md3.update(md1)
        self.assertEquals(pformat(md3), pformat(md1))
        md3.update(md2)
        self.assertEquals(pformat(md3), pformat(total))
        md3.update(None)
        self.assertEquals(pformat(md3), pformat(total))

class CodeFinderTest(unittest.TestCase):
    def getModule(self, source):
        tree = compiler.parse(dedent(source))
        codeFinder = CodeFinder()
        codeFinder.setModule('TestModule')
        codeFinder.setPackage('TestPackage')
        compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
        try:
            return eval(pformat(codeFinder.modules))['TestPackage.TestModule']
        except:
            print 'EXCEPTION WHEN EVALING:'
            print pformat(codeFinder.modules)
            print '=-' * 20
            raise

    def testEmpty(self):
        tree = compiler.parse("")
        codeFinder = CodeFinder()
        codeFinder.setModule('TestModule')
        codeFinder.setPackage('TestPackage')
        compiler.walk(tree, codeFinder, walker=ExampleASTVisitor(), verbose=1)
        self.assertTrue(codeFinder.modules.isModuleEmpty('TestPackage.TestModule'), 'should be empty')
        self.assertEquals(pformat(codeFinder.modules), "{}")


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
        actual = eval(pformat(codeFinder.modules))
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
    def eval(*_):
        pass

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
        compls = findCompletions(None, '', 'b', 1, 1, 'b', self.pysmelldict)
        expected = [compFunc('b', 'arg1, arg2'), compClass('bClass'), compConst('bconst')]
        self.assertEquals(compls, expected)

    def testCompleteMembers(self):
        compls = findCompletions(None, '', 'somethign.a', 1, 11, 'a', self.pysmelldict)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass')]
        self.assertEquals(compls, expected)

    def testCompleteArgumentListsPropRightParen(self):
        compls = findCompletions(None, '', 'salf.bm()', 1, 8, 'bm(', self.pysmelldict)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])
        
    def testCompleteArgumentListsProp(self):
        compls = findCompletions(None, '', 'salf.bm(', 1, 8, 'bm(', self.pysmelldict)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])
        
    def testCompleteArgumentListsRightParen(self):
        compls = findCompletions(None, '', '   b()', 1, 5, 'b(', self.pysmelldict)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])

    def testCompleteArgumentLists(self):
        compls = findCompletions(None, '', '  b(', 1, 4, 'b(', self.pysmelldict)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])

    def testInferSelfSimple(self):
        source = dedent("""\
            import something
            class AClass(object):
                def amethod(self, other):
                    other.do_something()
                    self.

                def another(self):
                    pass
        """)
        klass = infer(source, 5)
        self.assertEquals(klass, 'AClass')

    def testInferSelfMultipleClasses(self):
        
        source = dedent("""\
            import something
            class AClass(object):
                def amethod(self, other):
                    other.do_something()
                    class Sneak(object):
                        def sth(self):
                            class EvenSneakier(object):
                                pass
                            pass
                    pass

                def another(self):
                    pass



            class BClass(object):
                def newmethod(self, something):
                    wibble = [i for i in self.a]
                    pass

                def newerMethod(self, somethingelse):
                    if Bugger:
                        self.ass
        """)
        
        self.assertEquals(infer(source, 1), None, 'no class yet!')
        for line in range(2, 5):
            klass = infer(source, line)
            self.assertEquals(klass, 'AClass', 'wrong class %s in line %d' % (klass, line))

        for line in range(5, 7):
            klass = infer(source, line)
            self.assertEquals(klass, 'Sneak', 'wrong class %s in line %d' % (klass, line))

        for line in range(7, 9):
            klass = infer(source, line)
            self.assertEquals(klass, 'EvenSneakier', 'wrong class %s in line %d' % (klass, line))

        line = 9
        klass = infer(source, line)
        self.assertEquals(klass, 'Sneak', 'wrong class %s in line %d' % (klass, line))

        for line in range(10, 17):
            klass = infer(source, line)
            self.assertEquals(klass, 'AClass', 'wrong class %s in line %d' % (klass, line))

        for line in range(17, 51):
            klass = infer(source, line)
            self.assertEquals(klass, 'BClass', 'wrong class %s in line %d' % (klass, line))


    def testCompleteWithSelfInder(self):
        source = dedent("""\
            class aClass(object):
                def sth(self):
                    self.
        
        """)
        compls = findCompletions(None, source, "%sself." % (' ' * 8), 3, 13, '', self.pysmelldict)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'), compMeth('bm', 'aClass'), compProp('bprop', 'aClass')]
        self.assertEquals(compls, expected)


    def testCamelGroups(self):
        from idehelper import camelGroups
        def assertCamelGroups(word, groups):
            self.assertEquals(list(camelGroups(word)), groups.split())
        assertCamelGroups('alaMaKota', 'ala Ma Kota')
        assertCamelGroups('AlaMaKota', 'Ala Ma Kota')
        assertCamelGroups('isHTML', 'is H T M L')
        assertCamelGroups('ala_ma_kota', 'ala _ma _kota')

    def testMatchers(self):
        from idehelper import (matchCaseSensitively, matchCaseInsetively,
                matchCamelCased, matchSmartass, matchFuzzyCS, matchFuzzyCI)
        def assertMatches(base, word):
            msg = "should complete %r for %r with %s" % (base, word, testedFunction.__name__)
            uncurried = testedFunction(base)
            self.assertTrue(uncurried(word), msg +  "for the first time")
            self.assertTrue(uncurried(word), msg + "for the second time")
        def assertDoesntMatch(base, word):
            msg = "shouldn't complete %r for %r with %s" % (base, word, testedFunction.__name__)
            uncurried = testedFunction(base)
            self.assertFalse(uncurried(word), msg +  "for the first time")
            self.assertFalse(uncurried(word), msg + "for the second time")
        def assertStandardMatches():
            assertMatches('Ala', 'Ala')
            assertMatches('Ala', 'AlaMaKota')
            assertMatches('ala_ma_kota', 'ala_ma_kota')
            assertMatches('', 'AlaMaKota')
            assertDoesntMatch('piernik', 'wiatrak')
        def assertCamelMatches():
            assertMatches('AMK', 'AlaMaKota')
            assertMatches('aM', 'alaMaKota')
            assertMatches('aMK', 'alaMaKota')
            assertMatches('aMaKo', 'alaMaKota')
            assertMatches('alMaK', 'alaMaKota')
            assertMatches('a_ma_ko', 'ala_ma_kota')
            assertDoesntMatch('aleMbiK', 'alaMaKota')
            assertDoesntMatch('alaMaKotaIPsaIRybki', 'alaMaKota')

        testedFunction = matchCaseSensitively
        assertStandardMatches()
        assertDoesntMatch('ala', 'Alamakota')
        assertDoesntMatch('ala', 'Ala')

        testedFunction = matchCaseInsetively
        assertStandardMatches()
        assertMatches('ala', 'Alamakota')
        assertMatches('ala', 'Ala')
        
        testedFunction = matchCamelCased
        assertStandardMatches()
        assertCamelMatches()
        assertMatches('aMK', 'alaMaKota')
        assertDoesntMatch('almako', 'ala_ma_kota')
        assertDoesntMatch('almako', 'alaMaKota')
        assertDoesntMatch('alkoma', 'alaMaKota')

        testedFunction = matchSmartass
        assertStandardMatches()
        assertCamelMatches()
        assertMatches('amk', 'alaMaKota')
        assertMatches('AMK', 'alaMaKota')
        assertMatches('almako', 'ala_ma_kota')
        assertMatches('almako', 'alaMaKota')
        assertDoesntMatch('alkoma', 'alaMaKota')

        testedFunction = matchFuzzyCS
        assertStandardMatches()
        assertCamelMatches()
        assertMatches('aMK', 'alaMaKota')
        assertMatches('aaMKa', 'alaMaKota')
        assertDoesntMatch('almako', 'alaMaKota')
        assertDoesntMatch('amk', 'alaMaKota')
        assertDoesntMatch('alkoma', 'alaMaKota')

        testedFunction = matchFuzzyCI
        assertStandardMatches()
        assertCamelMatches()
        assertMatches('aMK', 'alaMaKota')
        assertMatches('aaMKa', 'alaMaKota')
        assertMatches('almako', 'alaMaKota')
        assertMatches('amk', 'alaMaKota')
        assertDoesntMatch('alkoma', 'alaMaKota')


if __name__ == '__main__':
    unittest.main()
