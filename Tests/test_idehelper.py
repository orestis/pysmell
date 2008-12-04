import copy
import os
import unittest
from textwrap import dedent

from pysmell.idehelper import (inferClass, detectCompletionType,
    CompletionOptions, findPYSMELLDICT, Types, findBase, getSafeTree)

NESTEDDICT = {
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
        'POINTERS' : {
            'Another.Thing': 'Nested.Package.Module.Class',
            'Star.*': 'Nested.Package.Module.*',
        
        },
        'HIERARCHY' : ['Nested.Package.Module'],
}


class IDEHelperTest(unittest.TestCase):
    def testFindPYSMELLDICT(self):
        # include everything that starts with PYSMELLTAGS
        if os.path.exists('PYSMELLTAGS'):
            os.remove('PYSMELLTAGS')
        import pysmell.idehelper
        oldTryReadPSD = pysmell.idehelper.tryReadPYSMELLDICT
        oldListDir = pysmell.idehelper.listdir
        TRPArgs = []
        def mockTRP(direct, fname, dictToUpdate):
            TRPArgs.append((direct, fname))
            dictToUpdate.update({'PYSMELLTAGS.django': {'django': True}}.get(fname, {}))

        listdirs = []
        def mockListDir(dirname):
            listdirs.append(dirname)
            return {'random': ['something'],
                    os.path.join('random', 'dirA'): ['PYSMELLTAGS.django'],
                }.get(dirname, [])

        pysmell.idehelper.tryReadPYSMELLDICT = mockTRP
        pysmell.idehelper.listdir = mockListDir
        try:
            self.assertEquals(findPYSMELLDICT(os.path.join('a', 'random', 'path', 'andfile')), None, 'should not find PYSMELLTAGS')
            self.assertEquals(listdirs,
                [os.path.join('a', 'random', 'path'),
                 os.path.join('a', 'random'),
                 'a'], # two '' because of root again
                'did not list dirs correctly: %s' % listdirs)
            self.assertEquals(TRPArgs, [], 'did not read tags correctly')

            listdirs = []
            TRPArgs = []

            tags = findPYSMELLDICT(os.path.join('random', 'dirA', 'file'))
            self.assertEquals(tags, None, 'should not find pysmelltags')
            self.assertEquals(listdirs,
                [os.path.join('random', 'dirA'), 'random'],
                'did not list dirs correctly: %s' % listdirs)
            self.assertEquals(TRPArgs,
                [(os.path.join('random', 'dirA'), 'PYSMELLTAGS.django')],
                'did not read tags correctly: %s' % TRPArgs)

        finally:
            pysmell.idehelper.tryReadPYSMELLDICT = oldTryReadPSD
            pysmell.idehelper.listdir = oldListDir


    def testInferClassAbsolute(self):
        source = dedent("""\
            class Class(object):
                def sth(self):
                    self.
        
        """)
        pathParts = ["DevFolder", "BlahBlah", "Nested", "Package", "Module.py"]
        if os.name == 'posix':
            pathParts.insert(0, "/")
        else:
            pathParts.insert(0, "C:")
        absPath = os.path.join(*pathParts)
        inferred, _ = inferClass(absPath, getSafeTree(source, 3), 3, NESTEDDICT, None)
        self.assertEquals(inferred, 'Nested.Package.Module.Class')


    def testInferClassRelative(self):
        source = dedent("""\
            class Class(object):
                def sth(self):
                    self.
        
        """)
        pathParts = ["Nested", "Package", "Module.py"]
        relPath = os.path.join(*pathParts)
        inferred, _ = inferClass(relPath, getSafeTree(source, 3), 3, NESTEDDICT, None)
        self.assertEquals(inferred, 'Nested.Package.Module.Class')


    def testInferClassYouDontKnowAbout(self):
        source = dedent("""\
            class NewClass(object):
                def sth(self):
                    self.
        
        """)
        pathParts = ['TestData', 'PackageB', 'NewModule.py'] # TestData/PackageB contains an __init__.py file
        relPath = os.path.join(*pathParts)
        inferred, parents = inferClass(relPath, getSafeTree(source, 3), 3, NESTEDDICT, None)
        self.assertEquals(inferred, 'PackageB.NewModule.NewClass')
        self.assertEquals(parents, ['object'])

        cwd = os.getcwd()
        pathParts = [cwd, 'TestData', 'PackageB', 'NewModule.py'] # TestData/PackageB contains an __init__.py file
        absPath = os.path.join(*pathParts)
        inferred, parents = inferClass(absPath, getSafeTree(source, 3), 3, NESTEDDICT, None)
        self.assertEquals(inferred, 'PackageB.NewModule.NewClass')
        self.assertEquals(parents, ['object'])


    def testInferUnknownClassParents(self):
        source = dedent("""\
            from Nested.Package.Module import Class
            class Other(Class):
                def sth(self):
                    self.
        
        """)
        klass, parents = inferClass(os.path.join('TestData', 'PackageA', 'Module.py'),
            getSafeTree(source, 4), 4, NESTEDDICT)
        self.assertEquals(klass, 'PackageA.Module.Other')
        self.assertEquals(parents, ['Nested.Package.Module.Class'])


    def testInferClassParentsWithPointers(self):
        source = dedent("""\
            from Another import Thing
            class Bother(Thing):
                def sth(self):
                    self.
        
        """)
        klass, parents = inferClass(os.path.join('TestData', 'PackageA', 'Module.py'),
            getSafeTree(source, 4), 4, NESTEDDICT)
        self.assertEquals(klass, 'PackageA.Module.Bother')
        self.assertEquals(parents, ['Nested.Package.Module.Class'])
        
        
    def testInferClassParentsWithPointersToStar(self):
        source = dedent("""\
            from Star import Class
            class Bother(Class):
                def sth(self):
                    self.
        
        """)
        klass, parents = inferClass(os.path.join('TestData', 'PackageA', 'Module.py'),
            getSafeTree(source, 4), 4, NESTEDDICT)
        self.assertEquals(klass, 'PackageA.Module.Bother')
        self.assertEquals(parents, ['Nested.Package.Module.Class'])


class DetectOptionsTest(unittest.TestCase):
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
                    },
                },
                'POINTERS' : {},
                'HIERARCHY' : ['Module'],
            }
    

    def testDetectGlobalLookup(self):
        options = detectCompletionType('path', 'b', 1, 1, 'b', self.pysmelldict)
        expected = CompletionOptions(Types.TOPLEVEL)
        self.assertEquals(options, expected)


    def testDetectAttrLookup(self):
        line = 'somethign.a'
        options = detectCompletionType('path', line, 1, len(line), 'a', self.pysmelldict)
        expected = CompletionOptions(Types.INSTANCE, klass=None, parents=[])
        self.assertEquals(options, expected)


    def testDetectCompleteArgumentListMethodClosingParen(self):
        line = 'salf.bm()'
        options = detectCompletionType('path', line, 1, len(line) - 1, 'bm(', self.pysmelldict)
        expected = CompletionOptions(Types.METHOD, klass=None, parents=[], name='bm', rindex=-1)
        self.assertEquals(options, expected)


    def testDetectCompleteArgumentListMethod(self):
        line = 'salf.bm('
        options = detectCompletionType('path', line, 1, len(line), 'bm(', self.pysmelldict)
        expected = CompletionOptions(Types.METHOD, klass=None, parents=[], name='bm', rindex = None)
        self.assertEquals(options, expected)


    def testDetectCompleteArgumentListFunctionClosingParen(self):
        source = dedent("""\
            def a():
              b()
        """)
        line = '  b()'
        options = detectCompletionType('path', source, 2, len(line) - 1, 'b(', self.pysmelldict)
        expected = CompletionOptions(Types.FUNCTION, name='b', rindex=-1)# module?
        self.assertEquals(options, expected)

    
    def testDetectCompleteArgumentListFunction(self):
        source = dedent("""\
            def a():
              b(
        """)
        line = '  b('
        options = detectCompletionType('path', source, 2, len(line), 'b(', self.pysmelldict)
        expected = CompletionOptions(Types.FUNCTION, name='b', rindex=None)
        self.assertEquals(options, expected)


    def testDetectSimpleClass(self):
        source = dedent("""\
            class aClass(object):
                def sth(self):
                    self.
        
        """)
        line = "%sself." % (' ' * 8)
        options = detectCompletionType('Module.py', source, 3, len(line), '', self.pysmelldict)
        expected = CompletionOptions(Types.INSTANCE, klass='Module.aClass', parents=['object'])
        self.assertEquals(options, expected)



    def testInferShouldUpdatePYSMELLDICT(self):
        source = dedent("""\
            from Nested.Package.Module import Class
            class FreshClass(Class):
                something = 1
                def sth(self):
                    self.
        
        """)
        line = "%sself." % (' ' * 8)
        copiedDict = copy.deepcopy(self.pysmelldict)
        assert copiedDict == self.pysmelldict
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'),
            source, 5, len(line), '', copiedDict)
        expected = CompletionOptions(Types.INSTANCE, klass='PackageA.Module.FreshClass', parents=['Nested.Package.Module.Class'])
        self.assertEquals(options, expected) #sanity
        klass = copiedDict['CLASSES']['PackageA.Module.FreshClass']
        self.assertEquals(klass['bases'], ['Nested.Package.Module.Class'])
        self.assertEquals(klass['properties'], ['something'])
        self.assertEquals(klass['methods'], [('sth', [], "")])



    def testDetectDeepClass(self):
        source = dedent("""\
            class Class(object):
                def sth(self):
                    self.
        
        """)
        line = "%sself." % (' ' * 8)
        options = detectCompletionType(os.path.join('Nested', 'Package', 'Module.py'), source,
                            3, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.INSTANCE, klass='Nested.Package.Module.Class', parents=['object'])
        self.assertEquals(options, expected)


    def testDetectParentsOfUnknownClass(self):
        source = dedent("""\
            from Nested.Package.Module import Class
            class Other(Class):
                def sth(self):
                    self.
        
        """)
        line = "%sself." % (' ' * 8)
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                            4, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.INSTANCE, klass='PackageA.Module.Other', parents=['Nested.Package.Module.Class'])
        self.assertEquals(options, expected)
        

    def testDetectModuleCompletionInitial(self):
        source = dedent("""\
            from Nested.Package.Mo
            
        """)
        line = "from Nested.Package.Mo"
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                        1, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module='Nested.Package', showMembers=False)
        self.assertEquals(options, expected)
        
        source = dedent("""\
            from Module.
            
        """)
        line = "from Module."
        options = detectCompletionType('Module.py', source, 1, len(line), '', self.pysmelldict)
        expected = CompletionOptions(Types.MODULE, module='Module', showMembers=False)
        self.assertEquals(options, expected)
        
        source = dedent("""\
            from Mo
            
        """)
        line = "from Mo"
        options = detectCompletionType('Module.py', source, 1, len(line), '', self.pysmelldict)
        expected = CompletionOptions(Types.MODULE, module='Mo', showMembers=False)
        self.assertEquals(options, expected)
        

    def testDetectModuleCompletionTwo(self):
        source = dedent("""\
            from Nested.Package import 
            
        """)
        line = "from Nested.Package import "
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            1, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Nested.Package", showMembers=True)
        self.assertEquals(options, expected)

        source = dedent("""\
            from Nested import 
            
        """)
        line = "from Nested import "
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            1, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Nested", showMembers=True)
        self.assertEquals(options, expected)

        source = dedent("""\
            from Nested import Pack
            
        """)
        line = "from Nested import Pack"
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            1, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Nested", showMembers=True)
        self.assertEquals(options, expected)


    def testModuleCompletionThree(self):
        source = dedent("""\
            import Nested.Package.
            
        """)
        line = "import Nested.Package."
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            1, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Nested.Package", showMembers=False)
        self.assertEquals(options, expected)

        source = dedent("""\
            import Ne
            
        """)
        line = "import Ne"
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            1, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Ne", showMembers=False)
        self.assertEquals(options, expected)


    def testDetectModuleAttrLookup(self):
        source = dedent("""\
            from Nested.Package import Module as mod

            mod.
        """)
        line = "mod."
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            3, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Nested.Package.Module", showMembers=True)
        self.assertEquals(options, expected)


    def testDetectModuleAttrLookupWithBase(self):
        source = dedent("""\
            from Nested.Package import Module as mod

            func(mod.some, arg)
        """)
        line = "func(mod.some"
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            3, len(line), 'some', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Nested.Package.Module", showMembers=True)
        self.assertEquals(options, expected)


    def testDetectModuleAttrLookupWithBase2(self):
        print '--------'
        source = dedent("""\
            from Nested.Package import Module as mod

            class Some(object):
                def init(self):
                    self.func(mod.EVT_, self.something)
        """)
        line = "%sself.func(mod.EVT_" % (" " * 8)
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            5, len(line), 'EVT_', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Nested.Package.Module", showMembers=True)
        self.assertEquals(options, expected)


    def testDetectModuleAttrLookup2(self):
        source = dedent("""\
            from Nested.Package import Module

            Module.
        """)
        line = "Module."
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            3, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Nested.Package.Module", showMembers=True)
        self.assertEquals(options, expected)


    def testDetectModuleAttrLookup3(self):
        source = dedent("""\
            from Nested import Package

            funct(Package.Module., arg)
        """)
        line = "funct(Package.Module."
        options = detectCompletionType(os.path.join('TestData', 'PackageA', 'Module.py'), source,
                                            3, len(line), '', NESTEDDICT, update=False)
        expected = CompletionOptions(Types.MODULE, module="Nested.Package.Module", showMembers=True)
        self.assertEquals(options, expected)




    def testDetectClassCreation(self):
        source = dedent("""\
            from Module import aClass

            thing = aClass()
            thing.
        """)
        line = "thing."
        options = detectCompletionType('apath', source,
                                            4, len(line), '', self.pysmelldict)
        expected = CompletionOptions(Types.INSTANCE, klass='Module.aClass', parents=['object', 'ForeignModule.alien'])
        self.assertEquals(options, expected)


    def testDetectClassCreationLocal(self):
        source = dedent("""\
            class aClass(object):
                pass

            thing = aClass()
            thing.
        """)
        line = "thing."
        options = detectCompletionType(os.path.abspath('Module.py'), source,
                                            5, len(line), '', self.pysmelldict)
        expected = CompletionOptions(Types.INSTANCE, klass='Module.aClass', parents=['object'])
        self.assertEquals(options, expected)




class FindBaseTest(unittest.TestCase):

    def testThem(self):
        index = findBase('bbbb', 2)
        self.assertEquals(index, 0)
        index = findBase('a.bbbb(', 7)
        self.assertEquals(index, 2)
        index = findBase('bbbb(', 5)
        self.assertEquals(index, 0)
        index = findBase('    bbbb', 6)
        self.assertEquals(index, 4)
        index = findBase('hehe.bbbb', 7)
        self.assertEquals(index, 5)
        index = findBase('    hehe.bbbb', 11)
        self.assertEquals(index, 9)

if __name__ == '__main__':
    unittest.main()
