import unittest
from pysmell.dynamic import get_dynamic_tags

from test_tags import TestCase

class DynamicTagsTest(TestCase):

    def testBastion(self):
        funcDoc = """Create a bastion for an object, using an optional filter.\n\nSee the Bastion module's documentation for background.\n\nArguments:\n\nobject - the original object\nfilter - a predicate that decides whether a function name is OK;\n         by default all names are OK that don't start with '_'\nname - the name of the object; default repr(object)\nbastionclass - class used to create the bastion; default BastionClass"""
        moduledict = {
            'CLASSES': {
                'Bastion.BastionClass': {
                    'constructor': ['get', 'name'],
                    'bases': [],
                    'docstring': """\
Helper class used by the Bastion() function.

You could subclass this and pass the subclass as the bastionclass
argument to the Bastion() function, as long as the constructor has
the same signature (a get() function and a name for the object).""",
                    'properties': [],
                    'methods': [],
                },
            },
            'FUNCTIONS': [('Bastion.Bastion', ['object', 'filter=<lambda>', 'name=None', 'bastionclass=BastionClass'], funcDoc),
                ('Bastion._test', [], 'Test the Bastion() function.')],
            'CONSTANTS': [],
            'POINTERS': {'Bastion.MethodType': '__builtin__.MethodType'},
            'HIERARCHY': ['Bastion']
            
        }
        tags = get_dynamic_tags('Bastion')
        self.assertDictsEqual(tags, moduledict)

    def testOs(self):
        d = get_dynamic_tags('os')
        print d._modules
        self.fail()

if __name__ == '__main__':
    unittest.main()
