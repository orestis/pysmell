
import os.path
import time
from subprocess import Popen, PIPE, call
import sys
import unittest
from pysmell.vimhelper import findWord

vim_test = os.path.join("Tests", "test_vim.vim")


class MockVim(object):
    class _current(object):
        class _window(object):
            cursor = (-1, -1)
        buffer = []
        window = _window()
    current = _current()
    command = lambda _, __:Non
    def eval(*_):
        pass

class VimHelperTest(unittest.TestCase):

    def setUp(self):
        import pysmell.vimhelper
        pysmell.vimhelper.vim = self.vim = MockVim()

    def testFindBaseName(self):
        self.vim.current.buffer = ['aaaa', 'bbbb', 'cccc']
        self.vim.current.window.cursor =(2, 2)
        word = findWord(self.vim, 2, 'bbbb')
        self.assertEquals(word, 'bb')

    def testFindBaseMethodCall(self):
        self.vim.current.buffer = ['aaaa', 'a.bbbb(', 'cccc']
        self.vim.current.window.cursor =(2, 7)
        word = findWord(self.vim, 7, 'a.bbbb(')
        self.assertEquals(word, 'a.bbbb(')

    def testFindBaseFuncCall(self):
        self.vim.current.buffer = ['aaaa', 'bbbb(', 'cccc']
        self.vim.current.window.cursor =(2, 5)
        word = findWord(self.vim, 5, 'bbbb(')
        self.assertEquals(word, 'bbbb(')

    def testFindBaseNameIndent(self):
        self.vim.current.buffer = ['aaaa', '    bbbb', 'cccc']
        self.vim.current.window.cursor =(2, 6)
        word = findWord(self.vim, 6, '    bbbb')
        self.assertEquals(word, 'bb')

    def testFindBaseProp(self):
        self.vim.current.buffer = ['aaaa', 'hehe.bbbb', 'cccc']
        self.vim.current.window.cursor =(2, 7)
        word = findWord(self.vim, 7, 'hehe.bbbb')
        self.assertEquals(word, 'hehe.bb')

    def testFindBasePropIndent(self):
        self.vim.current.buffer = ['aaaa', '    hehe.bbbb', 'cccc']
        self.vim.current.window.cursor =(2, 11)
        word = findWord(self.vim, 11, '    hehe.bbbb')
        self.assertEquals(word, 'hehe.bb')

class VimTest(unittest.TestCase):
    def testVimFunctionally(self):
        if sys.platform == 'win32':
            return
        try:
            pysmell_file = os.path.join("TestData", "PYSMELLTAGS")
            if os.path.exists(pysmell_file):
                os.remove(pysmell_file)
            call(["pysmell", "."], cwd="TestData")
            self.assertTrue(os.path.exists(pysmell_file))
            test_file = os.path.join("TestData", "test.py")
            if os.path.exists(test_file):
                os.remove(test_file)

            self.assertTrue(os.path.isfile(vim_test), "Could not find vim functional test")
            proc = Popen(["vim", "-u", "NONE", "-s", vim_test], stdout=PIPE, stderr=PIPE)
            WAITFOR = 4
            while WAITFOR >= 0:
                result = proc.poll()
                if result is not None:
                    break
                time.sleep(1)
                WAITFOR -= 1
            else:
                try:
                    import win32api
                    win32api.TerminateProcess(int(proc._handle), -1)
                except:
                    import signal
                    os.kill(proc.pid, signal.SIGTERM)
                self.fail("TIMED OUT WAITING FOR VIM.Stdout was:\n" + proc.stdout.read())
            test_output = open(test_file, 'r').read()
            if result != 0:
                msg = proc.stdout.read()
                msg += open('vimtest.out', 'r').read()
                self.fail(msg)
            self.assertTrue("o.classPropertyA" in test_output, "did not complete correctly. Test output is:\n %s" % test_output)

        finally:
            if (os.path.isfile(pysmell_file)):
                os.remove(pysmell_file)
            if os.path.exists('vimtest.out'):
                os.remove('vimtest.out')
            if os.path.exists(test_file):
                os.remove(test_file)

if __name__ == "__main__":
    unittest.main()
            
            

    
