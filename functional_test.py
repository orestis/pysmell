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
            'PackageA': {
                'FUNCTIONS': [('SneakyFunction'), [], ""],
                'CONSTANTS': ['SneakyConstant'],
                'CLASSES':{
                    'SneakyClass': {
                            'bases': [],
                            'docstring': '',
                            'constructor': '',
                            'properties': [],
                            'methods': []
                            }
                        }
                    }
                }
        self.packageB = {
            'PackageB': {
                'FUNCTIONS': [('SneakyFunction'), [], ""],
                'CONSTANTS': ['SneakyConstant'],
                'CLASSES':{
                    'SneakyClass': {
                            'bases': [],
                            'docstring': '',
                            'constructor': '',
                            'properties': [],
                            'methods': []
                            }
                        }
                    }
                }
            
        
    def DONTtestTagGeneration(self):
        input_source = dedent("""\
        "This is MyClass' docstring"

        class MyClass(object):
            def __init__(self, first, last):
                self.firstname = first
                self.lastname = last

            @property
            def fullname(self):
                return self.firstname + " " + self.lastname

            def jump(self, howhigh):
                print 'Jumping %d up' % howhigh

            def duck(self):
                'hi im a docstring'
                print 'its a trap'

        """)
        output = pysmell.getClassDict(input_source)
        expected = {'MyClass': {
                'constructor': ['first', 'last'],
                'properties': ['firstname', 'lastname', 'fullname'],
                'methods': [('jump', ['howhigh'], ''), ('duck', [], 'hi im a docstring')],
            },
        }
        self.assertEquals(output._modules['CLASSES'], expected)
        self.fail('check *args **kwargs')

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

    
    def testPackage(self):
        if os.path.exists('Tests/PYSMELLTAGS'):
            os.remove('Tests/PYSMELLTAGS')
        subprocess.call(["python", "../pysmelltags.py", "PackageA"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PYSMELLTAGS').read())
        expectedDict = self.packageA
        self.assertEquals(PYSMELLDICT, expectedDict)

    
    def testPackageHandling(self):
        self.fail('django does a lot of top-level package in __init__.py')
        self.fail('pysmell should handle packages as well (I think that just p.p.module will do)')

    def DONTtestTypeInferencing(self):
        'given a valid code block, try to narrow down the possible classes and return that'
        self.fail()

if __name__ == '__main__':
    unittest.main()
