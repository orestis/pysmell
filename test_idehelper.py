import unittest
import os
from textwrap import dedent

from idehelper import inferClass, detectCompletionType, CompletionOptions

class IDEHelperTest(unittest.TestCase):
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
                'POINTERS' : {
                    'Another.Thing': 'Nested.Package.Module.Class',
                    'Star.*': 'Nested.Package.Module.*',
                
                },
        }

    
    def DONTtestFindPYSMELLDICT(self):
        self.fail('write test')

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
        inferred, _ = inferClass(absPath, source, 3, self.nestedDict, None)
        self.assertEquals(inferred, 'Nested.Package.Module.Class')


    def testInferClassRelative(self):
        source = dedent("""\
            class Class(object):
                def sth(self):
                    self.
        
        """)
        pathParts = ["Nested", "Package", "Module.py"]
        relPath = os.path.join(*pathParts)
        inferred, _ = inferClass(relPath, source, 3, self.nestedDict, None)
        self.assertEquals(inferred, 'Nested.Package.Module.Class')


    def testInferClassYouDontKnowAbout(self):
        source = dedent("""\
            class NewClass(object):
                def sth(self):
                    self.
        
        """)
        pathParts = ['Tests', 'PackageB', 'NewModule.py'] # Tests/PackageB contains an __init__.py file
        relPath = os.path.join(*pathParts)
        inferred, parents = inferClass(relPath, source, 3, self.nestedDict, None)
        self.assertEquals(inferred, 'PackageB.NewModule.NewClass')
        self.assertEquals(parents, ['object'])

        cwd = os.getcwd()
        pathParts = [cwd, 'Tests', 'PackageB', 'NewModule.py'] # Tests/PackageB contains an __init__.py file
        absPath = os.path.join(*pathParts)
        inferred, parents = inferClass(absPath, source, 3, self.nestedDict, None)
        self.assertEquals(inferred, 'PackageB.NewModule.NewClass')
        self.assertEquals(parents, ['object'])

    def testInferUnknownClassParents(self):
        source = dedent("""\
            from Nested.Package.Module import Class
            class Other(Class):
                def sth(self):
                    self.
        
        """)
        klass, parents = inferClass(os.path.join('Tests', 'PackageA', 'Module.py'), source,
                            4, self.nestedDict)
        self.assertEquals(klass, 'PackageA.Module.Other')
        self.assertEquals(parents, ['Nested.Package.Module.Class'])

    def testInferClassParentsWithPointers(self):
        source = dedent("""\
            from Another import Thing
            class Bother(Thing):
                def sth(self):
                    self.
        
        """)
        klass, parents = inferClass(os.path.join('Tests', 'PackageA', 'Module.py'), source,
                            4, self.nestedDict)
        self.assertEquals(klass, 'PackageA.Module.Bother')
        self.assertEquals(parents, ['Nested.Package.Module.Class'])
        
        
    def testInferClassParentsWithPointersToStar(self):
        source = dedent("""\
            from Star import Class
            class Bother(Class):
                def sth(self):
                    self.
        
        """)
        klass, parents = inferClass(os.path.join('Tests', 'PackageA', 'Module.py'), source,
                            4, self.nestedDict)
        self.assertEquals(klass, 'PackageA.Module.Bother')
        self.assertEquals(parents, ['Nested.Package.Module.Class'])
        
        

    def testDetectGlobalLookup(self):
        options = detectCompletionType('', '', 'b', 1, 1, 'b', self.pysmelldict)
        expected = CompletionOptions(isAttrLookup=False, klass=None, parents=None, funcName=None, rindex=None)
        self.assertEquals(options, expected)


    def testDetectAttrLookup(self):
        options = detectCompletionType('', '', 'somethign.a', 1, 11, 'a', self.pysmelldict)
        expected = CompletionOptions(isAttrLookup=True, klass=None, parents=None, funcName=None, rindex=None)
        self.assertEquals(options, expected)


    def testDetectCompleteArgumentListMethodClosingParen(self):
        options = detectCompletionType('', '', 'salf.bm()', 1, 8, 'bm(', self.pysmelldict)
        expected = CompletionOptions(isAttrLookup=True, klass=None, parents=None, funcName='bm', rindex=-1)
        self.assertEquals(options, expected)


    def testDetectCompleteArgumentListMethod(self):
        options = detectCompletionType('', '', 'salf.bm(', 1, 8, 'bm(', self.pysmelldict)
        expected = CompletionOptions(isAttrLookup=True, klass=None, parents=None, funcName='bm', rindex=None)
        self.assertEquals(options, expected)


    def testDetectCompleteArgumentListFunctionClosingParen(self):
        options = detectCompletionType('', '', '   b()', 1, 5, 'b(', self.pysmelldict)
        expected = CompletionOptions(isAttrLookup=False, klass=None, parents=None, funcName='b', rindex=-1)
        self.assertEquals(options, expected)

    
    def testDetectCompleteArgumentListFunction(self):
        options = detectCompletionType('', '', '  b(', 1, 4, 'b(', self.pysmelldict)
        expected = CompletionOptions(isAttrLookup=False, klass=None, parents=None, funcName='b', rindex=None)
        self.assertEquals(options, expected)


    def testDetectSimpleClass(self):
        source = dedent("""\
            class aClass(object):
                def sth(self):
                    self.
        
        """)
        options = detectCompletionType('Module.py', source, "%sself." % (' ' * 8), 3, 13, '', self.pysmelldict)
        expected = CompletionOptions(isAttrLookup=True, klass='Module.aClass',
                            parents=['object'], funcName=None, rindex=None)
        self.assertEquals(options, expected)


    def testDetectDeepClass(self):
        source = dedent("""\
            class Class(object):
                def sth(self):
                    self.
        
        """)
        options = detectCompletionType(os.path.join('Nested', 'Package', 'Module.py'), source,
                            "%sself." % (' ' * 8), 3, 13, '', self.nestedDict)
        expected = CompletionOptions(isAttrLookup=True, klass='Nested.Package.Module.Class', parents=['object'], funcName=None, rindex=None)
        self.assertEquals(options, expected)


    def testDetectParentsOfUnknownClass(self):
        source = dedent("""\
            from Nested.Package.Module import Class
            class Other(Class):
                def sth(self):
                    self.
        
        """)
        options = detectCompletionType(os.path.join('Tests', 'PackageA', 'Module.py'), source,
                            "%sself." % (' ' * 8), 4, 13, '', self.nestedDict)
        expected = CompletionOptions(isAttrLookup=True,
                            klass='PackageA.Module.Other', parents=['Nested.Package.Module.Class'],
                            funcName=None, rindex=None)
        self.assertEquals(options, expected)
        

    def testDetectModuleCompletion(self):
        source = dedent("""\
            from Nested.Package.
            
        """)
        options = detectCompletionType(os.path.join('Tests', 'PackageA', 'Module.py'), source,
                            "from Nested.Package.", 1, 20, '', self.nestedDict)
        expected = CompletionOptions(isAttrLookup=False,
                            klass=None, parents=None,
                            funcName=None, rindex=None, module="Nested.Package.")

        self.assertEquals(options, expected)
        




if __name__ == '__main__':
    unittest.main()
