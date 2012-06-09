#!/usr/bin/python

import sys
import subprocess
import os
import os.path

pythonpath = sys.executable
homepath = os.path.realpath(os.path.dirname(sys.argv[0]))
ophispath = os.path.join(homepath, "..", "bin", "ophis")

failed = 0

# These are some simple routines for forwarding to Ophis. It relies
# on the standard input/output capabilities; we'll only go around it
# when explicitly testing the input/output file capabilities.


def assemble_raw(asm="", options=[]):
    p = subprocess.Popen([pythonpath, ophispath] + options,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    return p.communicate(asm)


def assemble_string(asm, options=[]):
    return assemble_raw(asm, ["-o", "-", "-"] + options)


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


# And now, the actual test suites. First, the most basic techniques
# are tested - these are the ones the test harness *itself* depends
# on, then we start running through the features.

def test_basic():
    print
    print "==== BASIC OPERATION ===="
    test_string('Basic Ophis operation', '.byte "Hello, world!", 10',
                'Hello, world!\n')
    if failed == 0:
        test_file('Basic instructions', 'testbase.oph', 'testbase.bin')
        test_file('Basic data pragmas', 'testdata.oph', 'testdata.bin')
        test_file('Undocumented instructions', 'test6510.oph', 'test6510.bin',
                  ['-u'])
        test_file('65c02 extensions', 'test65c02.oph', 'test65c02.bin', ['-c'])
        test_file('Wide instructions', 'testwide.oph', 'testwide.bin', ['-c'])
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


def test_outfile():
    global failed
    print "\n==== INPUT AND OUTPUT ===="
    if os.path.exists("ophis.bin"):
        print "TEST SUITE FAILED: unclean test environment (ophis.bin exists)"
        failed += 1
        return
    elif os.path.exists("custom.bin"):
        print "TEST SUITE FAILED: unclean test environment (custom.bin exists)"
        failed += 1
        return

    # Test 1: Defaults
    try:
        assemble_raw('.byte "Hello, world!", 10', ['-'])
        f = open('ophis.bin', 'rb')
        if f.read() != 'Hello, world!\n':
            print "Default output filename: FAILED (bad output)"
            failed += 1
        else:
            print "Default output filename: SUCCESS"
        f.close()
        os.unlink('ophis.bin')
    except:
        print "Default output filename: FAILED (exception)"
        failed += 1

    # Test 2: Command line override
    try:
        assemble_raw('.byte "Hello, world!", 10', ['-', '-o', 'custom.bin'])
        f = open('custom.bin', 'rb')
        if f.read() != 'Hello, world!\n':
            print "Commandline output filename: FAILED (bad output)"
            failed += 1
        else:
            print "Commandline output filename: SUCCESS"
        f.close()
        os.unlink('custom.bin')
    except:
        print "Commandline output filename: FAILED (exception)"
        failed += 1

    # Test 3: Pragma override
    try:
        assemble_raw('.outfile "custom.bin"\n.byte "Hello, world!", 10', ['-'])
        f = open('custom.bin', 'rb')
        if f.read() != 'Hello, world!\n':
            print "Commandline output filename: FAILED (bad output)"
            failed += 1
        else:
            print "Commandline output filename: SUCCESS"
        f.close()
        os.unlink('custom.bin')
    except:
        print "Commandline output filename: FAILED (exception)"
        failed += 1

    # Test 4: Command line override of .outfile
    try:
        assemble_raw('.outfile "custom2.bin"\n'
                     '.byte "Hello, world!", 10', ['-', '-o', 'custom.bin'])
        f = open('custom.bin', 'rb')
        if f.read() != 'Hello, world!\n':
            print "Commandline override of pragma: FAILED (bad output)"
            failed += 1
        else:
            print "Commandline override of pragma: SUCCESS"
        f.close()
        os.unlink('custom.bin')
    except:
        print "Commandline override of pragma: FAILED (exception)"
        failed += 1

    # Test 5: Pragma repetition priority
    try:
        assemble_raw('.outfile "custom.bin"\n'
                     '.outfile "custom2.bin"\n'
                     '.byte "Hello, world!", 10', ['-'])
        f = open('custom.bin', 'rb')
        if f.read() != 'Hello, world!\n':
            print "Pragma repetition: FAILED (bad output)"
            failed += 1
        else:
            print "Pragma repetition: SUCCESS"
        f.close()
        os.unlink('custom.bin')
    except:
        print "Pragma repetition: FAILED (exception)"
        failed += 1

    # Test 6: multiple input files
    try:
        out = assemble_raw('', ['-o', '-', '-u',
                                os.path.join(homepath, "testbase.oph"),
                                os.path.join(homepath, "test6510.oph")])[0]
        f = open(os.path.join(homepath, "testbase.bin"), 'rb')
        s = f.read()
        f.close()
        f = open(os.path.join(homepath, "test6510.bin"), 'rb')
        s += f.read()
        f.close()
        if out != s:
            print "Multiple input files: FAILED (bad output)"
            failed += 1
        else:
            print "Multiple input files: SUCCESS"
    except:
        print "Multiple input files: FAILED (exception)"
        failed += 1


def test_transforms():
    print "\n==== BINARY TRANSFORM PASSES ===="
    print "Simple zero page selection: SUCCESS (covered in basic tests)"
    test_string('Chained collapse', '.org $fa \n lda + \n lda ^ \n * rts \n',
                '\xa5\xfe\xa5\xfc\x60')
    test_string('Reversible collapse', '.org $fb \n bne ^+200 \n lda ^ \n',
                '\xf0\x03\x4c\xc5\x01\xad\x00\x01')


def test_systematic():
    test_outfile()
    test_transforms()


if __name__ == '__main__':
    print "Using Python interpreter:", pythonpath

    test_basic()

    if failed == 0:
        test_systematic()
    else:
        print "\nBasic test cases failed, aborting test."

    if failed > 0:
        print "\nTotal test case failures: %d" % failed
    else:
        print "\nAll test cases succeeded"
