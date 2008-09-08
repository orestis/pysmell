import unittest
from textwrap import dedent
import subprocess
import os

import pysmelltags

class FunctionalTest(unittest.TestCase):
    def setUp(self):
        self.packageA = {
            'CONSTANTS': [
                'PackageA.ModuleA.CONSTANT',
                'PackageA.NestedPackage.EvenMore.ModuleC.NESTED',
                'PackageA.SneakyConstant',
            ],
            'FUNCTIONS': [
                ('PackageA.ModuleA.TopLevelFunction', ['arg1', 'arg2'], ""),
                ('PackageA.SneakyFunction', [], ""),
            ],
            'CLASSES': {
                'PackageA.ModuleA.ClassA': {
                    'bases': ['object'],
                    'docstring': '',
                    'constructor': [],
                    'properties': ['classPropertyA', 'classPropertyB', 'propertyA', 'propertyB', 'propertyC', 'propertyD'],
                    'methods': [('methodA', ['argA', 'argB', '*args', '**kwargs'], '')]
                },
                'PackageA.ModuleA.ChildClassA': {
                    'bases': ['ClassA', 'object'],
                    'docstring': 'a class docstring, imagine that',
                    'constructor': ['conArg'],
                    'properties': ['extraProperty'],
                    'methods': [('extraMethod', [], 'i have a docstring')],
                },
                'PackageA.SneakyClass': {
                    'bases': [],
                    'docstring': '',
                    'constructor': [],
                    'properties': [],
                    'methods': []
                },
            }
        }
        
        self.packageB = {
            'CONSTANTS': ['PackageB.SneakyConstant'],
            'FUNCTIONS': [('PackageB.SneakyFunction', [], "")],
            'CLASSES':{
                'PackageB.SneakyClass': {
                    'bases': [],
                    'docstring': '',
                    'constructor': [],
                    'properties': [],
                    'methods': []
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


    def testPackageDot(self):
        if os.path.exists('Tests/PackageA/PYSMELLTAGS'):
            os.remove('Tests/PackageA/PYSMELLTAGS')
        subprocess.call(["python", "../../pysmelltags.py", "."], cwd='Tests/PackageA')
        self.assertTrue(os.path.exists('Tests/PackageA/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PackageA/PYSMELLTAGS').read())
        expectedDict = self.packageA
        self.assertEquals(PYSMELLDICT, expectedDict)

    
    def DONTtestSingleFile(self):
        self.fail()


    def testOutputRedirect(self):
        if os.path.exists('Tests/OUTPUTREDIR'):
            os.remove('Tests/OUTPUTREDIR')
        subprocess.call(["python", "../pysmelltags.py", "PackageA", "-o",
            "OUTPUTREDIR"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/OUTPUTREDIR'))
        PYSMELLDICT = eval(open('Tests/OUTPUTREDIR').read())
        expectedDict = self.packageA
        self.assertEquals(PYSMELLDICT, expectedDict)

        absPath = os.path.join(os.getcwd(), 'Tests', 'OUTPUTREDIR2')
        if os.path.exists(absPath):
            os.remove(absPath)
        subprocess.call(["python", "../pysmelltags.py", "PackageA", "-o", absPath], cwd='Tests')
        self.assertTrue(os.path.exists(absPath))
        PYSMELLDICT = eval(open(absPath).read())
        expectedDict = self.packageA
        self.assertEquals(PYSMELLDICT, expectedDict)


    def testNoArgs(self):
        proc = subprocess.Popen(["python", "pysmelltags.py"], stdout=subprocess.PIPE)
        proc.wait()
        stdout = proc.stdout.read()
        expected = dedent("""\
        PySmell v0.2

        usage: python pysmelltags.py package [package, ...] [-x excluded, ...] [options]

        Generate a PYSMELLTAGS file with information about the Python code contained
        in the specified packages (recursively). This file is then used to
        provide autocompletion for various IDEs and editors that support it.

        Options:

            -x args   Will not analyze files in directories that match the argument.
                      Useful for excluding tests or version control directories.

            -o FILE   Will redirect the output to FILE instead of PYSMELLTAGS

            -t        Will print timing information.

        """)
        self.assertEquals(stdout, expected)


    def testTypeInferencing(self):
        'given a valid code block, try to narrow down the possible classes and return that'
        self.fail()

if __name__ == '__main__':
    unittest.main()
