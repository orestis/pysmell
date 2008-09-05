import unittest
from textwrap import dedent
import subprocess
import os

import pysmelltags

class FunctionalTest(unittest.TestCase):
    def setUp(self):
        self.packageA = {
            'PackageA.ModuleA': {
                'FUNCTIONS': [('TopLevelFunction', ['arg1', 'arg2'], "")],
                'CONSTANTS': ['CONSTANT',],
                'CLASSES':
                    {'ClassA': {
                            'bases': ['object'],
                            'docstring': '',
                            'constructor': [],
                            'properties': ['classPropertyA', 'classPropertyB', 'propertyA', 'propertyB', 'propertyC', 'propertyD'],
                            'methods': [('methodA', ['argA', 'argB', '*args', '**kwargs'], '')]
                        },
                     'ChildClassA': {
                            'bases': ['ClassA', 'object'],
                            'docstring': 'a class docstring, imagine that',
                            'constructor': ['conArg'],
                            'properties': ['extraProperty'],
                            'methods': [('extraMethod', [], 'i have a docstring')],
                        }
                    },
            },
            'PackageA.NestedPackage.EvenMore.ModuleC': {
                'FUNCTIONS': [],
                'CONSTANTS': ['NESTED'],
                'CLASSES':{}
            },

            'PackageA': {
                'FUNCTIONS': [('SneakyFunction', [], "")],
                'CONSTANTS': ['SneakyConstant'],
                'CLASSES':{
                    'SneakyClass': {
                            'bases': [],
                            'docstring': '',
                            'constructor': [],
                            'properties': [],
                            'methods': []
                            }
                        }
            }
        }
        
        self.packageB = {
            'PackageB': {
                'FUNCTIONS': [('SneakyFunction', [], "")],
                'CONSTANTS': ['SneakyConstant'],
                'CLASSES':{
                    'SneakyClass': {
                            'bases': [],
                            'docstring': '',
                            'constructor': [],
                            'properties': [],
                            'methods': []
                    }
                }
            }
        }
            
        
    def testMultiPackage(self):
        if os.path.exists('Tests/PYSMELLTAGS'):
            os.remove('Tests/PYSMELLTAGS')
        subprocess.call(["python", "../pysmelltags.py", "PackageA", "PackageB"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PYSMELLTAGS').read())
        expectedDict = {}
        expectedDict.update(self.packageA)
        expectedDict.update(self.packageB)
        self.assertEquals(PYSMELLDICT, expectedDict)

    
    def testPackageA(self):
        if os.path.exists('Tests/PYSMELLTAGS'):
            os.remove('Tests/PYSMELLTAGS')
        subprocess.call(["python", "../pysmelltags.py", "PackageA"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PYSMELLTAGS').read())
        expectedDict = self.packageA
        self.assertEquals(PYSMELLDICT, expectedDict)


    def testPackageB(self):
        if os.path.exists('Tests/PYSMELLTAGS'):
            os.remove('Tests/PYSMELLTAGS')
        subprocess.call(["python", "../pysmelltags.py", "PackageB"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PYSMELLTAGS').read())
        expectedDict = self.packageB
        self.assertEquals(PYSMELLDICT, expectedDict)


    def DONTtestTypeInferencing(self):
        'given a valid code block, try to narrow down the possible classes and return that'
        self.fail()

if __name__ == '__main__':
    unittest.main()
