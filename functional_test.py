import unittest
from textwrap import dedent

import pysmell

class FunctionalTest(unittest.TestCase):
    def testTagGeneration(self):
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
        self.assertEquals(output._classes, expected)
        self.fail('check *args **kwargs')
    
    def testSimpleAutoComplete(self):
        'should accept initialy a starting string and return everything that matches'
        self.fail()


    def testTypeInferencing(self):
        'given a valid code block, try to narrow down the possible classes and return that'
        self.fail()

if __name__ == '__main__':
    unittest.main()
