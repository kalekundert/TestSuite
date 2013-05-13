#!/usr/bin/env python

import sys, inspect, traceback
from string import capwords

import utilities.cursor as cursor
import utilities.muffler as muffler
import utilities.text as text

class Suite:

    class NullHelper:
        """ An single instance of this class is passed to the setup, test, and
        teardown functions.  This allows information to be passed between the
        different components of the test. """
        pass


    def __init__(self, title, stop_on_error=True):
        self.title = title
        self.finished = False
        self.stop_on_error = stop_on_error

        self._tests = []
        self._skips = []
        self._results = []

        self._setup = Function.null()
        self._teardown = Function.null()
        self._helper = Helper.null()

    def __iter__(self):
        assert self.finished
        return iter(self._results)


    def run(self, callback=lambda result: None):
        results = []

        # Complain if there are no tests to run.
        if not self._tests:
            message = text.wrap(
                    "\nThe '%s' suite does not have any " % suite.title,
                    "tests to run. If you are using your own test suite, ",
                    "you can get this error by forgetting to pass it into ",
                    "the run() function.")
            raise ValueError(message)

        # Run the tests.
        for test in self._tests:
            result = test.run(); callback(result)
            self._results.append(result)

            if not result and self.stop_on_error:
                break

        self.finished = True

    def test(self, function):
        test = Test(self, function)
        self._tests.append(test)
        return function

    def skip(self, function):
        skip = Function(function, role='skipped')
        self._skips.append(skip)
        return function

    def setup(self, function):
        self._setup = Function(function, role='setup')
        return function

    def teardown(self, function):
        self._teardown = Function(function, role='teardown')
        return function

    def helper(self, cls):
        self._helper = Helper(cls)
        return cls


    def is_finished(self):
        return self.finished

    def get_title(self):
        return self.title

    def set_title(self, title):
        self.title = title

    def get_num_tests(self):
        return len(self._tests)

    def get_num_skips(self):
        return len(self._skips)

    def get_results(self):
        return self._results

    def get_setup(self):
        return self._setup

    def get_teardown(self):
        return self._teardown

    def get_helper(self):
        return self._helper.instantiate()


class Test:
    
    class Result:

        def __init__(self, test, success, output, traceback):
            self.test = test
            self.title = test.title

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


    def __init__(self, suite, function):
        self.suite = suite
        self.function = Function(function, role='test')
        self.title = capwords(self.function.name.replace('_', ' '))

    def run(self):
        setup = self.suite.get_setup()
        function = self.function
        teardown = self.suite.get_teardown()
        helper = self.suite.get_helper()

        with muffler.Muffler() as output:
            try:
                setup(helper)
                function(helper)
                teardown(helper)
            except:
                return Test.Failure(self, output, traceback.format_exc())
            else:
                return Test.Success(self, output)


class Runner:

    def __init__(self):
        self.format = '(%d/%d)'
        self.status = ''

    def run(self, *suites):
        for suite in suites:
            self.successes = 0
            self.failures = 0
            self.test = 0

            self.first_failure = None

            self.title = suite.get_title() + ' '
            self.num_tests = suite.get_num_tests()
            self.num_skips = suite.get_num_skips()

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


    def write_header(self):
        cursor.write(self.title)
        cursor.save()

    def write_progress(self):
        color = "red" if self.failures else "green"
        status = '(%d/%d)' % (self.test, self.num_tests)

        cursor.restore()
        cursor.clear_eol()

        cursor.write_color(status, color, "bold")

    def write_debug_info(self):
        print

        if self.num_skips:
            message = "Skipped %d %s."
            arguments = self.num_skips, text.plural(self.num_skips, "test")
            print cursor.color(message % arguments, "white")

        if self.failures:
            print

            failure = self.first_failure
            header = "Test failed: %s" % failure.title
            print cursor.color(header, "red", "bold")

            print failure.output
            print failure.traceback



class Function:

    def __init__(self, function, role):
        self.function = function
        self.name = function.__name__
        self.role = role

        arguments = inspect.getargspec(function)[0]
        num_arguments = len(arguments)

        if num_arguments == 0:
            self.use_helper = False
        elif num_arguments == 1:
            self.use_helper = True
        else:
            message = "%s function %s() must accept either 0 or 1 arguments."
            arguments = self.role.title(), self.name
            raise ValueError(message % arguments)

    def __call__(self, helper):
        return self.function(helper) if self.use_helper else self.function()

    @staticmethod
    def null():
        return Function(lambda: None, 'null')


class Helper:

    def __init__(self, cls=None):
        self.cls = cls
        self.name = cls.__name__

    def instantiate(self):
        try:
            return self.cls()
        except:
            message = "Unable to instantiate a %s() helper." % self.name
            raise ValueError(message)

    @staticmethod
    def null():
        class BlankObject (object): pass
        return Helper(BlankObject)



# Global Variables (fold)
# ================
# These global variables provide an easy way to use this testing framework.

default_title = "Running all tests..."

global_suite = Suite(default_title)
global_runner = Runner()

test = global_suite.test
skip = global_suite.skip
setup = global_suite.setup
teardown = global_suite.teardown
helper = global_suite.helper
title = global_suite.set_title

def run(*suites):
    if not suites: suites = [global_suite]
    return global_runner.run(*suites)


if __name__ == "__main__":

    # This is primarily a test of the framework, but it also shows how the 
    # framework can be used to run simple tests.

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
        time.sleep(1); print 'Debugging output for 3.'; #raise ZeroDivisionError

    @skip
    def skip_4(helper):
        time.sleep(1); print 'Debugging output for 4.'; raise AssertionError


    # Once all of the tests have been specified, they can be executed using the
    # run() function.  The title() function can be optionally used to control
    # the title used in the output.

    title("Testing the tests...")
    run()

