import unittest
import sys

loader = unittest.TestLoader()
tests = loader.discover('tests')
testRunner = unittest.TextTestRunner(verbosity=2)
result = testRunner.run(tests)

if result.wasSuccessful():
    print("ALL TESTS PASSED")
    sys.exit(0)
else:
    print("TESTS FAILED")
    sys.exit(1)
