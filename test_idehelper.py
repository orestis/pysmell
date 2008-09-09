import unittest
import os
from textwrap import dedent

from idehelper import inferClass

class IDEHelperTest(unittest.TestCase):
    def setUp(self):
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
    
    def testFindPYSMELLDICT(self):
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
        
        
        


if __name__ == '__main__':
    unittest.main()
