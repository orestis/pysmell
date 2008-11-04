import unittest
import os, sys
from subprocess import call

import pysmell

class MockDialog(object):
    def menu(options):
        return 0

class TestTextMate(unittest.TestCase):
    pysmell_file = os.path.join("TestData", "PYSMELLTAGS")
    test_file = os.path.join("TestData", "test.py")
    def setUp(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.pysmell_file):
            os.remove(self.pysmell_file)
        call(["pysmell", "."], cwd="TestData")
        self.assertTrue(os.path.exists(self.pysmell_file))
        
    def testIntegration(self):
        f = open(self.test_file, 'w')
        f.write("from PackageA.ModuleA import ClassA\n")
        f.write("o = ClassA()")
        f.write("o.")
        f.close()

        os.putenv('TM_SUPPORT_PATH', 'TestData')
        os.putenv('TM_FILEPATH', self.test_file)
        os.putenv('TM_LINE_NUMBER', '3')
        os.putenv('TM_LINE_INDEX', '3')

        textmate._main()
        
        print writes

        

        self.fail('unfinished')

    def tearDown(self):
        if os.path.exists(self.pysmell_file):
            os.remove(self.pysmell_file)
        if os.path.exists(self.test_file):
            os.remove(self.test_file)



if __name__ == '__main__':
    unittest.main()
