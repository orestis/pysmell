
import os.path
from subprocess import Popen, PIPE
import sys
import unittest

emacs_test = os.path.join("Tests", "test_emacs.el")


class EmacsTest(unittest.TestCase):
    def testEmacsFunctionally(self):
        if sys.platform == 'win32':
            return
        try:
            pysmell_file = os.path.join("TestData", "PYSMELLTAGS")
            if (os.path.isfile(pysmell_file)):
                os.remove(pysmell_file)
            self.assertTrue(os.path.isfile(emacs_test), "Could not find emacs functional test")
            user = os.environ.get('USER', os.environ.get('username'))
            proc = Popen(["emacs",  "--batch", "--load", emacs_test, '--funcall', 'run-all-tests', '-u', user], stdout=PIPE, stderr=PIPE)
            result = proc.wait()

            if result != 0:
                msg = proc.stdout.read()
                self.fail(msg)
        finally:
            if (os.path.isfile(pysmell_file)):
                os.remove(pysmell_file)

if __name__ == "__main__":
    unittest.main()
            
            

    
