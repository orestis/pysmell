from unittest import TestLoader, TextTestRunner

import test_codefinder
import test_idehelper

suite = TestLoader().loadTestsFromModule(test_codefinder)
suite.addTest(TestLoader().loadTestsFromModule(test_codefinder))

TextTestRunner(verbosity=2).run(suite)
