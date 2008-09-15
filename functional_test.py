import unittest
from textwrap import dedent
import subprocess
import os

import pysmelltags

class FunctionalTest(unittest.TestCase):
    def setUp(self):
        self.packageA = {
            'CONSTANTS': [
                'PackageA.SneakyConstant',
                'PackageA.ModuleA.CONSTANT',
                'PackageA.NestedPackage.EvenMore.ModuleC.NESTED',
            ],
            'FUNCTIONS': [
                ('PackageA.SneakyFunction', [], ""),
                ('PackageA.ModuleA.TopLevelFunction', ['arg1', 'arg2'], ""),
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
                    'bases': ['PackageA.ModuleA.ClassA', 'object'],
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
            },
            'POINTERS': {
                'PackageA.NESTED': 'PackageA.NestedPackage.EvenMore.ModuleC.NESTED',
                'PackageA.MC': 'PackageA.NestedPackage.EvenMore.ModuleC',
            
            },
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
            },
            'POINTERS': {}
        }

    def assertDictsEqual(self, actualDict, expectedDict):
        self.assertEquals(len(actualDict.keys()), len(expectedDict.keys()),
            "dicts don't have equal number of keys: %r != %r" % (actualDict.keys(), expectedDict.keys()))
        self.assertEquals(set(actualDict.keys()), set(expectedDict.keys()), "dicts don't have equal keys")
        for key, value in actualDict.items():
            if isinstance(value, dict):
                self.assertTrue(isinstance(expectedDict[key], dict), "incompatible types found for key %s" % key)
                self.assertDictsEqual(value, expectedDict[key])
            elif isinstance(value, list):
                self.assertTrue(isinstance(expectedDict[key], list), "incompatible types found for key %s" % key)
                self.assertEquals(sorted(value), sorted(expectedDict[key]), 'wrong sorted(list) for key %s:\n%r != %r' % (key, value, expectedDict[key]))
            else:
                self.assertEquals(value, expectedDict[key], "wrong value for key %s" % key)


    def testMultiPackage(self):
        if os.path.exists('Tests/PYSMELLTAGS'):
            os.remove('Tests/PYSMELLTAGS')
        subprocess.call(["python", "../pysmelltags.py", "PackageA", "PackageB"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PYSMELLTAGS').read())
        expectedDict = {}
        expectedDict.update(self.packageA)
        expectedDict['CLASSES'].update(self.packageB['CLASSES'])
        expectedDict['CONSTANTS'].extend(self.packageB['CONSTANTS'])
        expectedDict['FUNCTIONS'].extend(self.packageB['FUNCTIONS'])
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    def testPackageA(self):
        if os.path.exists('Tests/PYSMELLTAGS'):
            os.remove('Tests/PYSMELLTAGS')
        subprocess.call(["python", "../pysmelltags.py", "PackageA"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PYSMELLTAGS').read())
        expectedDict = self.packageA
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    def testPackageB(self):
        if os.path.exists('Tests/PYSMELLTAGS'):
            os.remove('Tests/PYSMELLTAGS')
        subprocess.call(["python", "../pysmelltags.py", "PackageB"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PYSMELLTAGS').read())
        expectedDict = self.packageB
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    def testPackageDot(self):
        if os.path.exists('Tests/PackageA/PYSMELLTAGS'):
            os.remove('Tests/PackageA/PYSMELLTAGS')
        subprocess.call(["python", "../../pysmelltags.py", "."], cwd='Tests/PackageA')
        self.assertTrue(os.path.exists('Tests/PackageA/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('Tests/PackageA/PYSMELLTAGS').read())
        expectedDict = self.packageA
        self.assertDictsEqual(PYSMELLDICT, expectedDict)

        self.fail("when the current dir is not a package, search for packages")

    
    def testSingleFile(self):
        "should recurse up until it doesn't find __init__.py"
        path = 'Tests/PackageA/NestedPackage/EvenMore/'
        if os.path.exists('%sPYSMELLTAGS' % path):
            os.remove('%sPYSMELLTAGS' % path)
        subprocess.call(["python", "../../../../pysmelltags.py", "ModuleC.py"], cwd=path)
        self.assertTrue(os.path.exists('%sPYSMELLTAGS' % path ))
        PYSMELLDICT = eval(open('%sPYSMELLTAGS' % path).read())
        expectedDict = {
            'FUNCTIONS': [],
            'CONSTANTS': ['PackageA.NestedPackage.EvenMore.ModuleC.NESTED'],
            'CLASSES': {},
            'POINTERS': {},
                        
        }
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    def testOutputRedirect(self):
        if os.path.exists('Tests/OUTPUTREDIR'):
            os.remove('Tests/OUTPUTREDIR')
        subprocess.call(["python", "../pysmelltags.py", "PackageA", "-o",
            "OUTPUTREDIR"], cwd='Tests')
        self.assertTrue(os.path.exists('Tests/OUTPUTREDIR'))
        PYSMELLDICT = eval(open('Tests/OUTPUTREDIR').read())
        expectedDict = self.packageA
        self.assertDictsEqual(PYSMELLDICT, expectedDict)

        absPath = os.path.join(os.getcwd(), 'Tests', 'OUTPUTREDIR2')
        if os.path.exists(absPath):
            os.remove(absPath)
        subprocess.call(["python", "../pysmelltags.py", "PackageA", "-o", absPath], cwd='Tests')
        self.assertTrue(os.path.exists(absPath))
        PYSMELLDICT = eval(open(absPath).read())
        expectedDict = self.packageA
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    def testNoArgs(self):
        proc = subprocess.Popen(["python", "pysmelltags.py"], stdout=subprocess.PIPE)
        proc.wait()
        stdout = proc.stdout.read()
        expected = dedent("""\
        PySmell v0.5

        usage: python pysmelltags.py package [package, ...] [-x excluded, ...] [options]

        Generate a PYSMELLTAGS file with information about the Python code contained
        in the specified packages (recursively). This file is then used to
        provide autocompletion for various IDEs and editors that support it.

        Options:

            -x args   Will not analyze files in directories that match the argument.
                      Useful for excluding tests or version control directories.

            -o FILE   Will redirect the output to FILE instead of PYSMELLTAGS

            -t        Will print timing information.

        """).splitlines()
        self.assertEquals(stdout.splitlines(), expected)


    def testCompleteModuleMembers(self):
        self.fail("""
        from django.db import models

        models.

        should return all top-level members of django.db.models
        """)


if __name__ == '__main__':
    unittest.main()
