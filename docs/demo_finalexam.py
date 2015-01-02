#!/usr/bin/env python

import time
import finalexam

# Test functions can be easily specified using decorators.  There are three 
# different decorators available to use: @test, @setup, and @teardown.  The 
# first specifies a function that contains testing code.  The second and third 
# specify functions to call before and after every individual test.

# Note that although these test functions all contain print statements, no 
# output will be written unless one of the tests fails.  You can see this for 
# yourself by raising an exception from within any of the tests.

@finalexam.setup
def setup():
    print "Setting up the test."

@finalexam.teardown
def teardown():
    print "Tearing down the test."

@finalexam.test
def test_1():
    print 'Debugging output for 1.'
    time.sleep(1)

@finalexam.test
def test_2():
    print 'Debugging output for 2.'
    time.sleep(1)

# It is also easy to indicate that a particular piece of code is expected to 
# raise an exception, using expect().  In this example, an assertion would be 
# triggered if the with block finished without throwing a ZeroDivisionError.

@finalexam.test
def test_3():
    with finalexam.expect(ZeroDivisionError):
        undefined = 1 / 0
    time.sleep(1)

# Once all of the tests have been specified, they can be executed using the
# run() function.  The title() function can be optionally used to control
# the title displayed to the terminal.

finalexam.title("Unit test demonstration...")
finalexam.run()

# vim: nofoldenable
