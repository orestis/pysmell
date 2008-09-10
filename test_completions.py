import unittest
from textwrap import dedent
import os

from idehelper import findCompletions


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
                    
                }
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
                    
                }
        }


    def testCompletions(self):
        options = (False, None, None, None, None)
        compls = findCompletions('b', self.pysmelldict, options)
        expected = [compFunc('b', 'arg1, arg2'), compClass('bClass'), compConst('bconst')]
        self.assertEquals(compls, expected)

    def testCompleteMembers(self):
        options = (True, None, None, None, None)
        compls = findCompletions('a', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass')]
        self.assertEquals(compls, expected)

    def testCompleteArgumentListsPropRightParen(self):
        options = (True, None, None, 'bm', -1)
        compls = findCompletions('bm(', self.pysmelldict, options)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])
        
    def testCompleteArgumentListsProp(self):
        options = (True, None, None, 'bm', None)
        compls = findCompletions('bm(', self.pysmelldict, options)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])
        

    def testCompleteArgumentListsRightParen(self):
        options = (False, None, None, 'b', -1)
        compls = findCompletions('b(', self.pysmelldict, options)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])


    def testCompleteArgumentLists(self):
        options = (False, None, None, 'b', None)
        compls = findCompletions('b(', self.pysmelldict, options)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])


    def testCompleteWithSelfInfer(self):
        options = (True, 'Module.aClass', [], None, None)
        compls = findCompletions('', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass')]
        self.assertEquals(compls, expected)


    def testCompletionsWithPackages(self):
        expected = [dict(word='cprop', kind='m', menu='Nested.Package.Module:Class', dup='1')]
        options = (True, 'Nested.Package.Module.Class', [], None, None)
        compls = findCompletions('', self.nestedDict, options)
        self.assertEquals(compls, expected)


    def testKnowAboutClassHierarchies(self):
        options = (True, 'Module.bClass', [], None, None)
        compls = findCompletions('', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass'),
                    compMeth('cm', 'bClass'), compProp('cprop', 'bClass'),
                    compMeth('dm', 'bClass'), compProp('dprop', 'bClass')]
        self.assertEquals(compls, expected)

        options = (True, 'Module.cClass', ['Module.bClass'], None, None)
        compls = findCompletions('', self.pysmelldict, options)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass'),
                    compMeth('cm', 'bClass'), compProp('cprop', 'bClass'),
                    compMeth('dm', 'bClass'), compProp('dprop', 'bClass')]
        self.assertEquals(compls, expected)





if __name__ == '__main__':
    unittest.main()
