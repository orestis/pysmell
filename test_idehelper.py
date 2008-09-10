import unittest
import os
from textwrap import dedent

from idehelper import inferClass, detectCompletionType

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
        inferred = inferClass(absPath, source, 3, self.nestedDict, None)
        self.assertEquals(inferred, 'Nested.Package.Module.Class')


    def testInferClassRelative(self):
        source = dedent("""\
            class Class(object):
                def sth(self):
                    self.
        
        """)
        pathParts = ["Nested", "Package", "Module.py"]
        relPath = os.path.join(*pathParts)
        inferred = inferClass(relPath, source, 3, self.nestedDict, None)
        self.assertEquals(inferred, 'Nested.Package.Module.Class')


    def testInferClassYouDontKnowAbout(self):
        source = dedent("""\
            class NewClass(object):
                def sth(self):
                    self.
        
        """)
        pathParts = ['Tests', 'PackageB', 'NewModule.py'] # Tests/PackageB contains an __init__.py file
        relPath = os.path.join(*pathParts)
        inferred = inferClass(relPath, source, 3, self.nestedDict, None)
        self.assertEquals(inferred, 'PackageB.NewModule.NewClass')

        cwd = os.getcwd()
        pathParts = [cwd, 'Tests', 'PackageB', 'NewModule.py'] # Tests/PackageB contains an __init__.py file
        absPath = os.path.join(*pathParts)
        inferred = inferClass(absPath, source, 3, self.nestedDict, None)
        self.assertEquals(inferred, 'PackageB.NewModule.NewClass')

    def testDetectGlobalLookup(self):
        options = detectCompletionType('', '', 'b', 1, 1, 'b', self.pysmelldict)
        expected = (False, None, None, None)
        self.assertEquals(options, expected)


    def testDetectAttrLookup(self):
        options = detectCompletionType('', '', 'somethign.a', 1, 11, 'a', self.pysmelldict)
        expected = (True, None, None, None)
        self.assertEquals(options, expected)


    def testDetectCompleteArgumentListMethodClosingParen(self):
        options = detectCompletionType('', '', 'salf.bm()', 1, 8, 'bm(', self.pysmelldict)
        expected = (True, None, 'bm', -1)
        self.assertEquals(options, expected)


    def testDetectCompleteArgumentListMethod(self):
        options = detectCompletionType('', '', 'salf.bm(', 1, 8, 'bm(', self.pysmelldict)
        expected = (True, None, 'bm', None)
        self.assertEquals(options, expected)


    def testDetectCompleteArgumentListFunctionClosingParen(self):
        options = detectCompletionType('', '', '   b()', 1, 5, 'b(', self.pysmelldict)
        expected = (False, None, 'b', -1)
        self.assertEquals(options, expected)

    
    def testDetectCompleteArgumentListFunction(self):
        options = detectCompletionType('', '', '  b(', 1, 4, 'b(', self.pysmelldict)
        expected = (False, None, 'b', None)
        self.assertEquals(options, expected)


    def testDetectSimpleClass(self):
        source = dedent("""\
            class aClass(object):
                def sth(self):
                    self.
        
        """)
        options = detectCompletionType('Module.py', source, "%sself." % (' ' * 8), 3, 13, '', self.pysmelldict)
        expected = (True, 'Module.aClass', None, None)
        self.assertEquals(options, expected)


    def testDetectDeepClass(self):
        source = dedent("""\
            class Class(object):
                def sth(self):
                    self.
        
        """)
        options = detectCompletionType(os.path.join('Nested', 'Package', 'Module.py'), source,
                            "%sself." % (' ' * 8), 3, 13, '', self.nestedDict)
        expected = (True, 'Nested.Package.Module.Class', None, None)
        self.assertEquals(options, expected)




if __name__ == '__main__':
    unittest.main()
