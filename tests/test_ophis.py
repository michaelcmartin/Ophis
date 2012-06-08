#!/usr/bin/python

import sys
import subprocess
import os.path

pythonpath = sys.executable
homepath = os.path.realpath(os.path.dirname(sys.argv[0]))
ophispath = os.path.join(homepath, "..", "bin", "ophis")

failed = 0


def assemble_string(asm, options=[]):
    p = subprocess.Popen([pythonpath, ophispath, "-o", "-", "-"] + options,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    return p.communicate(asm)


def test_string(test_name, asm, expected, options=[]):
    (out, err) = assemble_string(asm, options)
    if out == expected:
        print "%s: SUCCESS" % test_name
    else:
        global failed
        failed += 1
        print "%s: FAILED\nError output:\n%s" % (test_name, err)


def test_file(test_name, fname, ename, options=[]):
    f = open(os.path.join(homepath, fname), 'rt')
    asm = f.read()
    f.close()
    if ename is not None:
        f = open(os.path.join(homepath, ename), 'rb')
        expected = f.read()
        f.close()
    else:  # a test where we expect failure
        expected = ''
    test_string(test_name, asm, expected, options)


if __name__ == '__main__':
    print "Using Python interpreter:", pythonpath
    test_string('Basic Ophis operation', '.byte "Hello, world!", 10',
                'Hello, world!\n')
    if failed == 0:
        test_file('Basic instructions', 'testbase.oph', 'testbase.bin')
        test_file('Basic data pragmas', 'testdata.oph', 'testdata.bin')
        test_file('Undocumented instructions', 'test6510.oph', 'test6510.bin',
                  ['-u'])
        test_file('65c02 extensions', 'test65c02.oph', 'test65c02.bin', ['-c'])
        test_file('Branch restrictions (6502)', 'longbranch.oph', None,
                  ['--no-branch-extend'])
        test_file('Branch restrictions (65c02)', 'branch_c02.oph', None,
                  ['-c', '--no-branch-extend'])
        test_file('Branch extension, error-free (6502)', 'longbranch.oph',
                  'longbranch.bin')
        test_file('Branch extension, correct code (6502)',
                  'longbranch_ref.oph', 'longbranch.bin')
        test_file('Branch extension, error-free (65c02)', 'branch_c02.oph',
                  'branch_c02.bin', ['-c'])
        test_file('Branch extension, correct code (65c02)',
                  'branch_c02_ref.oph', 'branch_c02.bin', ['-c'])

    if failed > 0:
        print "Total test case failures: %d" % failed
    else:
        print "All test cases succeeded"
