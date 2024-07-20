"""Error logging

    Keeps track of the number of errors inflicted so far, and
    where in the assembly the errors are occurring."""

# Copyright 2002-2024 Michael C. Martin and additional contributors.
# You may use, modify, and distribute this file under the MIT
# license: See README for details.

import sys

count = 0
currentpoint = "<Top Level>"


def log(err):
    """Reports an error at the current program point, and increases
the global error count."""
    global count
    count = count + 1
    print(currentpoint + ": " + err, file=sys.stderr)


def report():
    "Print out the number of errors."
    if count == 0:
        print("No errors", file=sys.stderr)
    elif count == 1:
        print("1 error", file=sys.stderr)
    else:
        print(str(count) + " errors", file=sys.stderr)
