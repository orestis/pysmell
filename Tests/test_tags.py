import unittest
from textwrap import dedent
import subprocess
import os
from pysmell import idehelper
from pysmell.codefinder import ModuleDict
from pysmell import tags

class ProducesFile(object):
    def __init__(self, *files):
        self.files = files
    def __call__(self, func):
        def patched(*args, **kw):
            for f in self.files:
                if os.path.exists(f):
                    os.remove(f)
            try:
                return func(*args, **kw)
            finally:
                for f in self.files:
                    if os.path.exists(f):
                        os.remove(f)
        patched.__name__ = func.__name__
        return patched

class TestCase(unittest.TestCase):
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
                self.assertEquals(value, expectedDict[key], "wrong value for key %s: \n%s != %s" % (key, value, expectedDict[key]))



class FunctionalTest(TestCase):
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
                'PackageA.RelImport': 'PackageA.NestedPackage',
                'PackageA.RelMC': 'PackageA.NestedPackage.EvenMore.ModuleC',
            
            },
            'HIERARCHY': [
                'PackageA',
                'PackageA.ModuleA',
                'PackageA.NestedPackage',
                'PackageA.NestedPackage.EvenMore',
                'PackageA.NestedPackage.EvenMore.ModuleC',
            ]
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
            'POINTERS': {},
            'HIERARCHY': ['PackageB']
        }


    @ProducesFile('TestData/PYSMELLTAGS')
    def testMultiPackage(self):
        subprocess.call(["pysmell", "PackageA", "PackageB"], cwd='TestData')
        self.assertTrue(os.path.exists('TestData/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('TestData/PYSMELLTAGS').read())
        expectedDict = {}
        expectedDict.update(self.packageA)
        expectedDict['CLASSES'].update(self.packageB['CLASSES'])
        expectedDict['CONSTANTS'].extend(self.packageB['CONSTANTS'])
        expectedDict['FUNCTIONS'].extend(self.packageB['FUNCTIONS'])
        expectedDict['HIERARCHY'].extend(self.packageB['HIERARCHY'])
        self.assertDictsEqual(PYSMELLDICT, expectedDict)



    @ProducesFile('TestData/PYSMELLTAGS')
    def testUpdateDict(self):
        subprocess.call(["pysmell", "PackageA"], cwd='TestData')
        self.assertTrue(os.path.exists('TestData/PYSMELLTAGS'))
        subprocess.call(["pysmell", "PackageB", "-i", "PYSMELLTAGS"], cwd='TestData')
        self.assertTrue(os.path.exists('TestData/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('TestData/PYSMELLTAGS').read())
        expectedDict = {}
        expectedDict.update(self.packageA)
        expectedDict['CLASSES'].update(self.packageB['CLASSES'])
        expectedDict['CONSTANTS'].extend(self.packageB['CONSTANTS'])
        expectedDict['FUNCTIONS'].extend(self.packageB['FUNCTIONS'])
        expectedDict['HIERARCHY'].extend(self.packageB['HIERARCHY'])
        self.assertDictsEqual(PYSMELLDICT, expectedDict)



    @ProducesFile('TestData/PYSMELLTAGS')
    def testPackageA(self):
        subprocess.call(["pysmell", "PackageA"], cwd='TestData')
        self.assertTrue(os.path.exists('TestData/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('TestData/PYSMELLTAGS').read())
        expectedDict = self.packageA
        self.assertDictsEqual(PYSMELLDICT, expectedDict)

        foundDict = idehelper.findPYSMELLDICT(os.path.join('TestData', 'PackageA', 'something'))
        self.assertDictsEqual(foundDict, expectedDict)


    @ProducesFile('TestData/PYSMELLTAGS')
    def testPackageB(self):
        subprocess.call(["pysmell", "PackageB"], cwd='TestData')
        self.assertTrue(os.path.exists('TestData/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('TestData/PYSMELLTAGS').read())
        expectedDict = self.packageB
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    @ProducesFile('TestData/PackageA/PYSMELLTAGS')
    def testPackageDot(self):
        subprocess.call(["pysmell", "."], cwd='TestData/PackageA')
        self.assertTrue(os.path.exists('TestData/PackageA/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('TestData/PackageA/PYSMELLTAGS').read())
        expectedDict = self.packageA
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    @ProducesFile('TestData/PYSMELLTAGS')
    def testAllPackages(self):
        subprocess.call(["pysmell", "."], cwd='TestData')
        self.assertTrue(os.path.exists('TestData/PYSMELLTAGS'))
        PYSMELLDICT = eval(open('TestData/PYSMELLTAGS').read())
        expectedDict = {}
        expectedDict.update(self.packageA)
        expectedDict['CLASSES'].update(self.packageB['CLASSES'])
        expectedDict['CONSTANTS'].extend(self.packageB['CONSTANTS'])
        expectedDict['CONSTANTS'].append('standalone.NOPACKAGE')
        expectedDict['FUNCTIONS'].extend(self.packageB['FUNCTIONS'])
        expectedDict['HIERARCHY'].extend(self.packageB['HIERARCHY'])
        expectedDict['HIERARCHY'].append('standalone')
        self.assertDictsEqual(PYSMELLDICT, expectedDict)

    
    @ProducesFile('TestData/PackageA/NestedPackage/EvenMore/PYSMELLTAGS')
    def testSingleFile(self):
        "should recurse up until it doesn't find __init__.py"
        path = 'TestData/PackageA/NestedPackage/EvenMore/'
        subprocess.call(["pysmell", "ModuleC.py"], cwd=path)
        self.assertTrue(os.path.exists('%sPYSMELLTAGS' % path ))
        PYSMELLDICT = eval(open('%sPYSMELLTAGS' % path).read())
        expectedDict = {
            'FUNCTIONS': [],
            'CONSTANTS': ['PackageA.NestedPackage.EvenMore.ModuleC.NESTED'],
            'CLASSES': {},
            'POINTERS': {},
            'HIERARCHY': ['PackageA.NestedPackage.EvenMore.ModuleC'],
                        
        }
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    @ProducesFile("TestData/PYSMELLTAGS")
    def testSingleFilesWithPaths(self):
        path = 'TestData'
        pysmell = os.path.join(path, 'PYSMELLTAGS')
        subprocess.call(["pysmell", os.path.join("PackageA", "NestedPackage", "EvenMore", "ModuleC.py")], cwd=path)
        self.assertTrue(os.path.exists(pysmell))
        PYSMELLDICT = eval(open(pysmell).read())
        expectedDict = {
            'FUNCTIONS': [],
            'CONSTANTS': ['PackageA.NestedPackage.EvenMore.ModuleC.NESTED'],
            'CLASSES': {},
            'POINTERS': {},
            'HIERARCHY': ['PackageA.NestedPackage.EvenMore.ModuleC'],
                        
        }
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    @ProducesFile('TestData/OUTPUTREDIR', 'TestData/OUTPUTREDIR2')
    def testOutputRedirect(self):
        subprocess.call(["pysmell", "PackageA", "-o",
            "OUTPUTREDIR"], cwd='TestData')
        self.assertTrue(os.path.exists('TestData/OUTPUTREDIR'))
        PYSMELLDICT = eval(open('TestData/OUTPUTREDIR').read())
        expectedDict = self.packageA
        self.assertDictsEqual(PYSMELLDICT, expectedDict)

        absPath = os.path.join(os.getcwd(), 'TestData', 'OUTPUTREDIR2')
        subprocess.call(["pysmell", "PackageA", "-o", absPath], cwd='TestData')
        self.assertTrue(os.path.exists(absPath))
        PYSMELLDICT = eval(open(absPath).read())
        expectedDict = self.packageA
        self.assertDictsEqual(PYSMELLDICT, expectedDict)


    def testNoArgs(self):
        proc = subprocess.Popen(["pysmell"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        stderr = proc.stderr.read()
        expected = dedent("""\
        usage: pysmell [-h] [-v] [-x [package [package ...]]] [-o OUTPUT] [-i INPUT]
                       [-t] [-d]
                       package [package ...]
        pysmell: error: too few arguments
        """)
        self.assertEquals(stderr.replace('\r\n', '\n'), expected)


    def DONTtestDunderAll(self):
        self.fail("when doing 'from place import *', do not bring in everything"
        "in the pointers but look for __all__ in the module and add only"
        "these.")


    def testOptionalOutput(self):
        modules = tags.process(['TestData/PackageA'], [], verbose=True)
        self.assertTrue(isinstance(modules, ModuleDict), 'did not return modules')
        self.assertDictsEqual(modules, self.packageA)


if __name__ == '__main__':
    unittest.main()
