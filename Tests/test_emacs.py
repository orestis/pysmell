
import os.path
from subprocess import Popen, PIPE
import sys
import unittest

emacs_test = os.path.join(os.path.dirname(sys.argv[0]), "test_emacs.el")


class EmacsTest(unittest.TestCase):
    def testEmacsFunctionally(self):
        self.assertTrue(os.path.isfile(emacs_test), "Could not find emacs functional test")
        proc = Popen(["emacs",  "--batch", "--script", emacs_test], stdout=PIPE, stderr=PIPE)
        result = proc.wait()

        if result != 0:
            msg = proc.stdout.read()
            self.fail(msg)

if __name__ == "__main__":
    unittest.main()
            
            

    
