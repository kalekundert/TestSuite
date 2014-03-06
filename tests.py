#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals

# Note that this script uses the code being tested to perform the tests.  This 
# self-referential nature might make this code a hard to understand for someone 
# who isn't already familiar with the testing framework.  Look in the demo 
# script to see a better real-world demonstration of the testing framework.

import testing
import utilities.text as text
import utilities.muffler as muffler

# Helper Functions

def print_status():
    print("Successful test executed.")

def print_status_with_helper(helper):
    print(helper.state)
    print("Successful test executed.")

def raise_exception():
    print("Unsuccessful test executed.")
    raise ZeroDivisionError

def raise_exception_with_helper(helper):
    print(helper.state)
    print("Unsuccessful test executed.")

def setup_globally():
    print("Setting up globally.")

def setup_with_helper(helper):
    print("Setting up a helper object.")
    helper.state = "Using a helper object."

def teardown_globally():
    print("Tearing down globally.")

def teardown_with_helper(helper):
    print("Tearing down a helper object.")
    del helper.state

def illegal_test_function(first, second):
    print("Not a valid test function.")


class CustomHelper:
    def __init__(self):
        self.state = "Using a custom helper object."

class IllegalCustomHelper:
    def __init__(self, argument):
        pass


def run_suite(suite):
    runner = testing.Runner()

    with muffler.Muffler() as transcript:
        runner.run(suite)

    transcript = str(transcript).strip()
    transcript = text.indent(transcript, '> ')

    print(transcript)
    return transcript


# Test Functions

@testing.test
def suite_api_test():
    suite = testing.Suite("Testing the API...")

    assert not suite.is_finished()

    suite.test(print_status)
    suite.test(raise_exception)
    suite.test(print_status)
    suite.skip(print_status)

    transcript = run_suite(suite)

    print(suite.get_results())

    assert suite.is_finished()
    assert suite.get_title() == "Testing the API..."
    assert suite.get_num_tests() == 3
    assert suite.get_num_skips() == 1
    assert suite.get_results()[0]
    assert not suite.get_results()[1]

    for result in suite:
        pass

@testing.test
def expected_error_test():
    with testing.expect(ZeroDivisionError):
        raise ZeroDivisionError

    with testing.expect(OverflowError):
        raise OverflowError

    with testing.expect(AssertionError):
        with testing.expect(ValueError):
            pass

    with testing.expect(AssertionError):
        with testing.expect(AttributeError):
            raise KeyError

@testing.test
def successful_test():
    suite = testing.Suite("Testing for success...")

    suite.setup(setup_globally)
    suite.test(print_status)
    suite.test(print_status)
    suite.test(print_status)
    suite.teardown(teardown_globally)

    transcript = run_suite(suite)

    assert "Testing for success..." in transcript
    assert '3/3' in transcript
    assert "Setting up globally." not in transcript
    assert "Successful test executed." not in transcript
    assert "Tearing down globally." not in transcript
    assert "Skipped" not in transcript

@testing.test
def successful_test_with_helper():
    suite = testing.Suite("Testing for success with helper...")

    suite.setup(setup_with_helper)
    suite.test(print_status_with_helper)
    suite.test(print_status_with_helper)
    suite.test(print_status_with_helper)
    suite.teardown(teardown_with_helper)

    transcript = run_suite(suite)

    assert "Testing for success with helper..." in transcript
    assert '3/3' in transcript
    assert "Setting up a helper object." not in transcript
    assert "Using a helper object." not in transcript
    assert "Successful test executed." not in transcript
    assert "Tearing down a helper object." not in transcript
    assert "Skipped" not in transcript

@testing.test
def failed_test():
    suite = testing.Suite("Testing for failure...")

    suite.setup(setup_globally)
    suite.test(print_status)
    suite.test(raise_exception)
    suite.test(print_status)
    suite.teardown(teardown_globally)

    transcript = run_suite(suite)

    assert "Testing for failure..." in transcript
    assert '2/3' in transcript
    assert "Setting up globally." in transcript
    assert "Unsuccessful test executed." in transcript
    assert 'ZeroDivisionError' in transcript
    assert "Tearing down globally." not in transcript
    assert "Skipped" not in transcript

@testing.test
def failed_test_with_helper():
    suite = testing.Suite("Testing for failure with helper...")

    suite.setup(setup_with_helper)
    suite.test(print_status_with_helper)
    suite.test(raise_exception_with_helper)
    suite.test(print_status_with_helper)
    suite.teardown(teardown_with_helper)

    transcript = run_suite(suite)

    assert "Testing for failure with helper..." in transcript
    assert '3/3' in transcript
    assert "Setting up a helper object." not in transcript
    assert "Using a helper object." not in transcript
    assert "Successful test executed." not in transcript
    assert "Tearing down a helper object." not in transcript
    assert "Skipped" not in transcript

@testing.skip
def custom_helper_test():
    suite = testing.Suite("Testing for success with custom helper...")

    suite.helper(CustomHelper)
    suite.test(print_status_with_helper)
    suite.test(print_status_with_helper)
    suite.test(print_status_with_helper)

    transcript = run_suite(suite)

    assert "Testing for success with helper..." in transcript
    assert '3/3' in transcript
    assert "Setting up a helper object." not in transcript
    assert "Using a custom helper object." not in transcript
    assert "Successful test executed." not in transcript
    assert "Tearing down a helper object." not in transcript
    assert "Skipped" not in transcript

@testing.test
def broken_user_input_test():
    suite = testing.Suite("Testing broken user input...")
    runner = testing.Runner()

    # Make sure an exception is thrown if no tests are added to the suite.
    with testing.expect(ValueError):
        runner.run(suite)

    # Make sure only functions with one or two arguments can be used as tests.
    with testing.expect(ValueError):
        suite.test(illegal_test_function)

    # Make sure an exception is thrown if a helper can't be instantiated.
    with testing.expect(ValueError):
        suite.helper(IllegalCustomHelper)
        suite.test(print_status)
        runner.run(suite)


testing.title("Testing the tests...")
testing.run()

