from unittest import TestLoader, TextTestRunner

import test_codefinder
import test_completions
import test_vimhelper
import test_idehelper
import test_matchers

suite = TestLoader().loadTestsFromModule(test_codefinder)
suite.addTest(TestLoader().loadTestsFromModule(test_completions))
suite.addTest(TestLoader().loadTestsFromModule(test_vimhelper))
suite.addTest(TestLoader().loadTestsFromModule(test_idehelper))
suite.addTest(TestLoader().loadTestsFromModule(test_matchers))

TextTestRunner(verbosity=2).run(suite)
