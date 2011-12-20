#!/usr/bin/env python

import sys, inspect, traceback
from string import capwords

import utilities.cursor as cursor
import utilities.muffler as muffler
import utilities.string as string

class Suite:

    # Constructor and Iterator {{{1
    def __init__(self, title, stop_on_error=False):
        self.tests = []
        self.results = []

        self.title = title
        self.finished = False

        self.setup_action = lambda helper: None
        self.teardown_action = lambda helper: None

        self.stop_on_error = stop_on_error

    def __iter__(self):
        assert self.finished
        return iter(self.results)

    # Attributes {{{1
    def is_finished(self):
        return self.finished

    def get_tests(self):
        return len(self.tests)

    def get_title(self):
        return self.title

    def set_title(self, title):
        self.title = title

    def get_results(self):
        return self.results

    def get_setup(self):
        return self.setup_action

    def get_teardown(self):
        return self.teardown_action

    # }}}1

    # Run Method {{{1
    def run(self, callback=lambda result: None):
        results = []

        for test in self.tests:
            result = test.run()
            callback(result)
            self.results.append(result)

            #if not result and self.stop_on_error:
                #break

        self.finished = True

    # Decorator Methods {{{1
    def setup(self, function):
        self.setup_action = self.check_arguments(function)
        return function

    def test(self, function):
        test = Test(self, function)
        function = self.check_arguments(function)

        self.tests.append(test)
        return function

    def teardown(self, function):
        self.teardown_action = self.check_arguments(function)
        return function

    def check_arguments(self, function):
        name = function.__name__
        signature = inspect.getargspec(function)
        message = "Test function %s() must accept exactly 1 argument."

        if len(signature.args) != 1:
            raise TypeError(message % name)

        return function

    # }}}1

class Test:

    # Helper Class {{{1

    # An single instance of this class is passed to the setup, test, and
    # teardown functions.  This allows information to be passed between the
    # different components of the test.
    
    class Helper:
        pass

    # Result Classes {{{1
    class Result:

        def __init__(self, test, success, output, traceback):
            self.test = test
            self.name = test.name

            self.success = success
            self.output = output
            self.traceback = traceback

        def __nonzero__(self):
            return self.success

    class Success(Result):
        def __init__(self, test, output):
            Test.Result.__init__(self, test, True, output, "")

    class Failure(Result):
        def __init__(self, test, output, exception):
            Test.Result.__init__(self, test, False, output, exception)

    # }}}1

    # Constructor {{{1
    def __init__(self, suite, function):
        self.function = function
        self.helper = Test.Helper()

        self.setup = suite.get_setup()
        self.teardown = suite.get_teardown()

        # This gross line tries to guess a reasonable name for the test by
        # starting with the name of the given function, converting any
        # underscores into spaces, and capitalizing each word.
        
        self.name = capwords(function.__name__.replace('_', ' '))


    # Run Method {{{1
    def run(self):
        with muffler.Muffler() as output:
            try:
                self.setup(self.helper)
                self.function(self.helper)
                self.teardown(self.helper)

            except Exception:
                return Test.Failure(self, output, traceback.format_exc())

            else:
                return Test.Success(self, output)

    # }}}1

class Runner:

    # Constructor {{{1
    def __init__(self):
        self.format = '(%d/%d)'
        self.status = ''

    # }}}1

    # Testing Methods {{{1
    def run(self, suite):

        # Get ready.
        self.successes = 0
        self.failures = 0
        self.test = 0

        self.first_failure = None

        self.tests = suite.get_tests()
        self.title = suite.get_title() + ' '

        self.write_header()
        self.write_progress()

        # Run the tests.
        suite.run(self.update)

        # Show the results.
        self.write_progress()
        self.write_debug_info()

    def update(self, result):

        # Analyze the result.
        if result: self.successes += 1
        if not result: self.failures += 1

        if not result and self.first_failure is None:
            self.first_failure = result

        self.test += 1
        
        # Display the result.
        self.write_progress()

    # Drawing Methods {{{1

    def write_header(self):
        cursor.write(self.title)
        cursor.save()

    def write_progress(self):
        color = "red" if self.failures else "green"
        status = '(%d/%d)' % (self.test, self.tests)

        cursor.restore()
        cursor.write_color(status, color, "bold")

    def write_debug_info(self):

        failure = self.first_failure

        if failure is None:
            print; return

        else:
            print; print

            header = "'%s' Debugging Information:" % failure.name
            print cursor.color(header, "red", "bold")

            print failure.output
            print failure.traceback


    # }}}1

# These global variables provide an easy way to use this testing framework.
default_title = "Running all tests..."

global_suite = Suite(default_title)
global_runner = Runner()

test = global_suite.test
setup = global_suite.setup
teardown = global_suite.teardown
title = global_suite.set_title

# Global Runner Function {{{1
def run(suite=global_suite):

    if not suite.get_tests():

        message = string.wrap(
                "The given test suite does not have any tests to run.  ",
                "If you are using your own test suites, you can get this ",
                "error by forgetting to pass them into the run() function.")

        raise ValueError(message)

    return global_runner.run(suite)

# }}}1

if __name__ == "__main__":

    # This is primarily a test of the framework, but it also shows how to use
    # it to run simple tests.

    import time

    # Test functions can be easily specified using decorators.  There are three
    # different decorators available to use: @test, @setup, and @teardown.
    # The first specifies a function that contains testing code.  The second
    # and third specify functions to call before and after every individual
    # test.

    @setup
    def test_setup(helper):
        print "Setting up the test."

    @teardown
    def test_teardown(helper):
        print "Tearing down the test."

    @test
    def test_1(helper):
        time.sleep(1); print 'Debugging output for 1.'

    @test
    def test_2(helper):
        time.sleep(1); print 'Debugging output for 2.'; raise AssertionError

    @test
    def test_3(helper):
        time.sleep(1); print 'Debugging output for 3.'; raise ZeroDivisionError

    # Once all of the tests have been specified, they can be executed using the
    # run() function.  The title() function can be optionally used to control
    # the title used in the output.

    title("Testing the tests...")
    run()

