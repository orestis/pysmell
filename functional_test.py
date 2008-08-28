import unittest
from textwrap import dedent
import subprocess
import os

import pysmell

class FunctionalTest(unittest.TestCase):
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

    def testPackage(self):
        if os.path.exists('Tests/PYSMELLTAGS'):
            os.remove('Tests/PYSMELLTAGS')
        subprocess.call(["python", "../pysmell.py", "PackageA"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PYSMELLTAGS').read())
        expectedDict = {
            'ModuleA': {
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
                    }
                
            }
                        
        }
        self.assertEquals(PYSMELLDICT, expectedDict)

    
    def DONTtestSimpleAutoComplete(self):
        'should accept initialy a starting string and return everything that matches'
        self.fail()


    def DONTtestTypeInferencing(self):
        'given a valid code block, try to narrow down the possible classes and return that'
        self.fail()

if __name__ == '__main__':
    unittest.main()
