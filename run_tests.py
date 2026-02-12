import unittest
import sys
import os

# Ensure project root is in path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    try:
        suite.addTests(loader.loadTestsFromName('tests.test_xml_reader'))
        suite.addTests(loader.loadTestsFromName('tests.test_audit'))
        suite.addTests(loader.loadTestsFromName('tests.test_modular_scraper'))
        suite.addTests(loader.loadTestsFromName('tests.test_scraper')) # Added this
    except Exception as e:
        with open('test_results_manual.txt', 'w') as f:
            f.write(f"Error loading tests: {e}")
        return

    with open('test_results_manual.txt', 'w') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        result = runner.run(suite)
        
if __name__ == '__main__':
    run_tests()
