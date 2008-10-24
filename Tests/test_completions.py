import unittest
from textwrap import dedent
import os

from pysmell.idehelper import findCompletions, CompletionOptions, Types


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

class CompletionTest(unittest.TestCase):
    def setUp(self):
        self.pysmelldict = {
                'CONSTANTS' : ['Module.aconstant', 'Module.bconst'],
                'FUNCTIONS' : [('Module.a', [], ''), ('Module.arg', [], ''), ('Module.b', ['arg1', 'arg2'], '')],
                'CLASSES' : {
                    'Module.aClass': {
                        'constructor': [],
                        'bases': ['object', 'ForeignModule.alien'],
                        'properties': ['aprop', 'bprop'],
                        'methods': [('am', [], ''), ('bm', [], ())]
                    },
                    'Module.bClass': {
                        'constructor': [],
                        'bases': ['Module.aClass'],
                        'properties': ['cprop', 'dprop'],
                        'methods': [('cm', [], ''), ('dm', [], ())]
                    }
                },
                'HIERARCHY' : ['Module'],
                'POINTERS': {}
            }
        self.nestedDict = {
                'CONSTANTS' : [],
                'FUNCTIONS' : [],
                'CLASSES' : {
                    'Nested.Package.Module.Class': {
                        'constructor': [],
                        'bases': [],
                        'properties': ['cprop'],
                        'methods': []
                    }
                    
                },
                'HIERARCHY' : ['Nested.Package.Module'],
                'POINTERS' : {'Nested.Package.Module.Something': 'dontcare'},
        }
        self.complicatedDict = {
                'CONSTANTS' : ['A.CONST_A', 'B.CONST_B', 'B._HIDDEN', 'C.CONST_C'],
                'FUNCTIONS' : [],
                'CLASSES' : {},
                'HIERARCHY' : ['A', 'B', 'C'],
                'POINTERS' : {
                    'A.*': 'B.*',
                    'A.THING': 'C.CONST_C',
                },
        }


    def testCompletions(self):
        options = CompletionOptions(Types.TOPLEVEL)
        compls = findCompletions('b', self.pysmelldict, options)
        expected = [compFunc('b', 'arg1, arg2'), compClass('bClass'), compConst('bconst')]
        self.assertEquals(compls, expected)


    def testCompleteMembers(self):
        options = CompletionOptions(Types.INSTANCE, klass=None, parents=[])
        compls = findCompletions('a', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass')]
        self.assertEquals(compls, expected)


    def testCompleteArgumentListsPropRightParen(self):
        options = CompletionOptions(Types.METHOD, klass=None, parents=[], name='bm', rindex=-1)
        compls = findCompletions('bm(', self.pysmelldict, options)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])

        
    def testCompleteArgumentListsProp(self):
        options = CompletionOptions(Types.METHOD, klass=None, parents=[], name='bm', rindex=None)
        compls = findCompletions('bm(', self.pysmelldict, options)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])
        

    def testCompleteArgumentListsRightParen(self):
        options = CompletionOptions(Types.FUNCTION, klass=None, parents=[], name='b', rindex=-1)
        compls = findCompletions('b(', self.pysmelldict, options)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])


    def testCompleteArgumentLists(self):
        options = CompletionOptions(Types.FUNCTION, klass=None, parents=[], name='b', rindex=None)
        compls = findCompletions('b(', self.pysmelldict, options)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])


    def testCompleteWithSelfInfer(self):
        options = CompletionOptions(Types.INSTANCE, klass='Module.aClass', parents=[])
        compls = findCompletions('', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass')]
        self.assertEquals(compls, expected)


    def testCompletionsWithPackages(self):
        options = CompletionOptions(Types.INSTANCE, klass='Nested.Package.Module.Class', parents=[])
        compls = findCompletions('', self.nestedDict, options)
        expected = [dict(word='cprop', kind='m', menu='Nested.Package.Module:Class', dup='1')]
        self.assertEquals(compls, expected)


    def testKnowAboutClassHierarchies(self):
        options = CompletionOptions(Types.INSTANCE, klass='Module.bClass', parents=[]) #possible error - why no parents
        compls = findCompletions('', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass'),
                    compMeth('cm', 'bClass'), compProp('cprop', 'bClass'),
                    compMeth('dm', 'bClass'), compProp('dprop', 'bClass')]
        self.assertEquals(compls, expected)

        options = CompletionOptions(Types.INSTANCE, klass='Module.cClass', parents=['Module.bClass'])
        compls = findCompletions('', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass'),
                    compMeth('cm', 'bClass'), compProp('cprop', 'bClass'),
                    compMeth('dm', 'bClass'), compProp('dprop', 'bClass')]
        self.assertEquals(compls, expected)


    def testModuleCompletion(self):
        options = CompletionOptions(Types.MODULE, module="Ne", showMembers=False)
        expected = [dict(word='Nested', kind='t', dup='1')]
        compls = findCompletions('Ne', self.nestedDict, options)
        self.assertEquals(compls, expected)
        
        options = CompletionOptions(Types.MODULE, module="Nested", showMembers=False)
        expected = [dict(word='Package', kind='t', dup='1')]
        compls = findCompletions('P', self.nestedDict, options)
        self.assertEquals(compls, expected)
        
        options = CompletionOptions(Types.MODULE, module="Nested.Package", showMembers=False)
        expected = [dict(word='Module', kind='t', dup='1')]
        compls = findCompletions('', self.nestedDict, options)
        self.assertEquals(compls, expected)

        options = CompletionOptions(Types.MODULE, module="Mo", showMembers=False)
        expected = [dict(word='Module', kind='t', dup='1')]
        compls = findCompletions('Mo', self.pysmelldict, options)
        self.assertEquals(compls, expected)

        options = CompletionOptions(Types.MODULE, module="Module", showMembers=False)
        expected = []
        compls = findCompletions('', self.pysmelldict, options)
        self.assertEquals(compls, expected)

        options = CompletionOptions(Types.MODULE, module="Nested.Package", showMembers=True)
        expected = [dict(word='Module', kind='t', dup='1')]
        compls = findCompletions('', self.nestedDict, options)
        self.assertEquals(compls, expected)

        options = CompletionOptions(Types.MODULE, module="Nested.Package.Module", showMembers=True)
        expected = [
            dict(word='Class', dup="1", kind="t", menu="Nested.Package.Module", abbr="Class()"),
            dict(word='Something', dup="1", kind="t"),
        ]
        compls = findCompletions('', self.nestedDict, options)
        self.assertEquals(compls, expected)

        options = CompletionOptions(Types.MODULE, module="A", showMembers=True)
        expected = [
            dict(word='CONST_A', kind='d', dup='1', menu='A'),
            dict(word='CONST_B', kind='d', dup='1', menu='B'),
            dict(word='THING', kind='t', dup='1')
        ]
        compls = findCompletions('', self.complicatedDict, options)
        self.assertEquals(compls, expected)




if __name__ == '__main__':
    unittest.main()
