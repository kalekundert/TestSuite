#!/usr/bin/env python

import time
import testing

# Test functions can be easily specified using decorators.  There are three 
# different decorators available to use: @test, @setup, and @teardown.  The 
# first specifies a function that contains testing code.  The second and third 
# specify functions to call before and after every individual test.

@testing.setup
def setup():
    print "Setting up the test."

@testing.teardown
def teardown():
    print "Tearing down the test."

@testing.test
def test_1():
    time.sleep(1); print 'Debugging output for 1.'

@testing.test
def test_2():
    time.sleep(1); print 'Debugging output for 2.'

@testing.test
def test_3():
    time.sleep(1); print 'Debugging output for 3.'


# Once all of the tests have been specified, they can be executed using the
# run() function.  The title() function can be optionally used to control
# the title displayed to the terminal.

testing.title("Unit test demonstration...")
testing.run()

# vim: nofoldenable
