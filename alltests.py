from unittest import TestLoader, TextTestRunner

import sys
sys.path.append('Tests')

import test_codefinder
import test_completions
import test_vimhelper
import test_idehelper
import test_matchers
import functional_test

suite = TestLoader().loadTestsFromModule(test_codefinder)
suite.addTest(TestLoader().loadTestsFromModule(test_completions))
suite.addTest(TestLoader().loadTestsFromModule(test_vimhelper))
suite.addTest(TestLoader().loadTestsFromModule(test_idehelper))
suite.addTest(TestLoader().loadTestsFromModule(test_matchers))
suite.addTest(TestLoader().loadTestsFromModule(functional_test))

TextTestRunner(verbosity=2).run(suite)
