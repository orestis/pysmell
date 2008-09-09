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
        compls = findCompletions(None, '', '', 'b', 1, 1, 'b', self.pysmelldict)
        expected = [compFunc('b', 'arg1, arg2'), compClass('bClass'), compConst('bconst')]
        self.assertEquals(compls, expected)

    def testCompleteMembers(self):
        compls = findCompletions(None, '', '', 'somethign.a', 1, 11, 'a', self.pysmelldict)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass')]
        self.assertEquals(compls, expected)

    def testCompleteArgumentListsPropRightParen(self):
        compls = findCompletions(None, '', '', 'salf.bm()', 1, 8, 'bm(', self.pysmelldict)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])
        
    def testCompleteArgumentListsProp(self):
        compls = findCompletions(None, '', '', 'salf.bm(', 1, 8, 'bm(', self.pysmelldict)
        orig = compMeth('bm', 'aClass')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])
        

    def testCompleteArgumentListsRightParen(self):
        compls = findCompletions(None, '', '', '   b()', 1, 5, 'b(', self.pysmelldict)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr'][:-1]
        self.assertEquals(compls, [orig])


    def testCompleteArgumentLists(self):
        compls = findCompletions(None, '', '', '  b(', 1, 4, 'b(', self.pysmelldict)
        orig = compFunc('b', 'arg1, arg2')
        orig['word'] = orig['abbr']
        self.assertEquals(compls, [orig])


    def testCompleteWithSelfInfer(self):
        source = dedent("""\
            class aClass(object):
                def sth(self):
                    self.
        
        """)
        compls = findCompletions(None, 'Module.py', source, "%sself." % (' ' * 8), 3, 13, '', self.pysmelldict)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'), compMeth('bm', 'aClass'), compProp('bprop', 'aClass')]
        self.assertEquals(compls, expected)

    def testCompletionsWithPackages(self):
        source = dedent("""\
            class Class(object):
                def sth(self):
                    self.
        
        """)
        expected = [dict(word='cprop', kind='m', menu='Nested.Package.Module:Class', dup='1')]
        compls = findCompletions(None,
                            os.path.join('Nested', 'Package', 'Module.py'), source,
                            "%sself." % (' ' * 8), 3, 13, '', self.nestedDict)
        self.assertEquals(compls, expected)

    def testKnowAboutClassHierarchies(self):
        source = dedent("""\
            class bClass(aClass):
                def sth(self):
                    self.
        
        """)
        compls = findCompletions(None, 'Module.py', source, "%sself." % (' ' * 8), 3, 13, '', self.pysmelldict)
        expected = [compMeth('am', 'aClass'), compProp('aprop', 'aClass'),
                    compMeth('bm', 'aClass'), compProp('bprop', 'aClass'),
                    compMeth('cm', 'bClass'), compProp('cprop', 'bClass'),
                    compMeth('dm', 'bClass'), compProp('dprop', 'bClass')]
        self.assertEquals(compls, expected)
        source = dedent("""\
            class cClass(object):
                def sth(self):
                    self.
        
        """)
        self.assertEquals(findCompletions(None, 'Module.py', source, "%sself." % (' ' * 8), 3, 13, '', self.pysmelldict), [])





if __name__ == '__main__':
    unittest.main()
