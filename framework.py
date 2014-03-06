#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals

import inspect, traceback
from string import capwords
from contextlib import contextmanager

import utilities.cursor as cursor
import utilities.muffler as muffler
import utilities.text as text

class Suite:

    def __init__(self, title, stop_on_error=True):
        self.title = title
        self.finished = False
        self.stop_on_error = stop_on_error

        self._tests = []
        self._skips = []
        self._results = []

        self._setup = _Function.null()
        self._teardown = _Function.null()
        self._helper = _Helper.null()

    def __iter__(self):
        assert self.finished
        return iter(self._results)


    def run(self, callback=lambda result: None):
        results = []

        # Complain if there are no tests to run.
        if not self._tests:
            message = text.wrap(
                    "\nThe '%s' suite does not have any " % self.title,
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
        skip = _Function(function, role='skipped')
        self._skips.append(skip)
        return function

    def setup(self, function):
        self._setup = _Function(function, role='setup')
        return function

    def teardown(self, function):
        self._teardown = _Function(function, role='teardown')
        return function

    def helper(self, cls):
        self._helper = _Helper(cls)
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
        self.function = _Function(function, role='test')
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
        print()

        if self.num_skips:
            message = "Skipped %d %s."
            arguments = self.num_skips, text.plural(self.num_skips, "test")
            print(cursor.color(message % arguments, "white"))

        if self.failures:
            print()

            failure = self.first_failure
            header = "Test failed: %s" % failure.title
            print(cursor.color(header, "red", "bold"))

            print(failure.output)
            print(failure.traceback)



class _Function:

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
        return _Function(lambda: None, 'null')


class _Helper:

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
        return _Helper(BlankObject)



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

@contextmanager
def expect(exception):
    try:
        yield
    except exception:
        pass
    except:
        raise AssertionError(
                "Unknown exception '{}' raised.".format(exception))


