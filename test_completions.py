import unittest
from textwrap import dedent
import os

from idehelper import findCompletions, CompletionOptions


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
        }


    def testCompletions(self):
        options = CompletionOptions(isAttrLookup=False, klass=None, parents=None, funcName=None, rindex=None)
        compls = findCompletions('b', self.pysmelldict, options)
        expected = [compFunc('b', 'arg1, arg2'), compClass('bClass'), compConst('bconst')]
        self.assertEquals(compls, expected)

    def testCompleteMembers(self):
        options = CompletionOptions(isAttrLookup=True, klass=None, parents=None, funcName=None, rindex=None)
        compls = findCompletions('a', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass')]
        self.assertEquals(compls, expected)

    def testCompleteArgumentListsPropRightParen(self):
        options = CompletionOptions(isAttrLookup=True, klass=None, parents=None, funcName='bm', rindex=-1)
        compls = findCompletions('bm(', self.pysmelldict, options)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])
        
    def testCompleteArgumentListsProp(self):
        options = CompletionOptions(isAttrLookup=True, klass=None, parents=None, funcName='bm', rindex=None)
        compls = findCompletions('bm(', self.pysmelldict, options)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])
        

    def testCompleteArgumentListsRightParen(self):
        options = CompletionOptions(isAttrLookup=False, klass=None, parents=None, funcName='b', rindex=-1)
        compls = findCompletions('b(', self.pysmelldict, options)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])


    def testCompleteArgumentLists(self):
        options = CompletionOptions(isAttrLookup=False, klass=None, parents=None, funcName='b', rindex=None)
        compls = findCompletions('b(', self.pysmelldict, options)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])


    def testCompleteWithSelfInfer(self):
        options = CompletionOptions(isAttrLookup=True, klass='Module.aClass', parents=[], funcName=None, rindex=None)
        compls = findCompletions('', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass')]
        self.assertEquals(compls, expected)


    def testCompletionsWithPackages(self):
        expected = [dict(word='cprop', kind='m', menu='Nested.Package.Module:Class', dup='1')]
        options = CompletionOptions(isAttrLookup=True, klass='Nested.Package.Module.Class', parents=[], funcName=None, rindex=None)
        compls = findCompletions('', self.nestedDict, options)
        self.assertEquals(compls, expected)


    def testKnowAboutClassHierarchies(self):
        options = CompletionOptions(isAttrLookup=True, klass='Module.bClass', parents=[], funcName=None, rindex=None)
        compls = findCompletions('', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass'),
                    compMeth('cm', 'bClass'), compProp('cprop', 'bClass'),
                    compMeth('dm', 'bClass'), compProp('dprop', 'bClass')]
        self.assertEquals(compls, expected)

        options = CompletionOptions(isAttrLookup=True, klass='Module.cClass', parents=['Module.bClass'], funcName=None, rindex=None)
        compls = findCompletions('', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass'),
                    compMeth('cm', 'bClass'), compProp('cprop', 'bClass'),
                    compMeth('dm', 'bClass'), compProp('dprop', 'bClass')]
        self.assertEquals(compls, expected)


    def testModuleCompletion(self):
        options = CompletionOptions(module="Nested")
        expected = [dict(word='Package', kind='t', dup='1')]
        compls = findCompletions('P', self.nestedDict, options)
        self.assertEquals(compls, expected)
        
        options = CompletionOptions(module="Nested.Package")
        expected = [dict(word='Module', kind='t', dup='1')]
        compls = findCompletions('', self.nestedDict, options)
        self.assertEquals(compls, expected)

        options = CompletionOptions(module="Module")
        expected = []
        compls = findCompletions('', self.pysmelldict, options)
        self.assertEquals(compls, expected)



if __name__ == '__main__':
    unittest.main()
