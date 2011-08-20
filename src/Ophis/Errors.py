"""Error logging

	Keeps track of the number of errors inflicted so far, and
	where in the assembly the errors are occurring."""

# Copyright 2002 Michael C. Martin.
# You may use, modify, and distribute this file under the BSD
# license: See LICENSE.txt for details.

count = 0
currentpoint = "<Top Level>"

def log(err):
	"""Reports an error at the current program point, and increases
the global error count."""
	global count
	count = count+1
	print currentpoint+": "+err

def report():
	"Print out the number of errors."
	if count == 0: print "No errors"
	elif count == 1: print "1 error"
	else: print str(count)+" errors"