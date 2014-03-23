#!/usr/bin/python

import sys
import subprocess
import os
import os.path

if len(sys.argv) > 1:
    pythonpath = sys.argv[1]
else:
    pythonpath = sys.executable
homepath = os.path.realpath(os.path.dirname(sys.argv[0]))
ophispath = os.path.join(homepath, "..", "bin", "ophis")

failed = 0

# These are some simple routines for forwarding to Ophis. It relies
# on the standard input/output capabilities; we'll only go around it
# when explicitly testing the input/output file capabilities.


def assembled(raw):
    return ' '.join(["%02X" % ord(c) for c in raw])


def assemble_raw(asm="", options=[]):
    p = subprocess.Popen([pythonpath, ophispath] + options,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    return p.communicate(asm)


def assemble_string(asm, options=[]):
    return assemble_raw(asm, ["-qo", "-", "-"] + options)


def test_string(test_name, asm, expected, options=[]):
    (out, err) = assemble_string(asm, options)
    if out == expected:
        print "%s: SUCCESS" % test_name
    else:
        global failed
        failed += 1
        print "%s: FAILED" % test_name
        print "Assembled code: ", assembled(out)
        print "Expected code:  ", assembled(expected)
    if err != '':
        print "Error output:\n%s" % err


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
    test_string('Basic Ophis operation', '.byte "Hello, world!"',
                'Hello, world!')
    test_string('Newline/EOF passthrough', '.byte 10,26,13,4,0,"Hi",13,10',
                '\n\x1a\r\x04\x00Hi\r\n')
    # Normally these would go in Expressions but we need them to run the
    # tests for relative instructions.
    test_string('Program counter recognition', '.org $41\nlda #^\n', '\xa9A')
    test_string('Program counter math', '.org $41\nlda #^+3\n', '\xa9D')
    if failed == 0:
        test_file('Basic instructions', 'testbase.oph', 'testbase.bin')
        test_file('Basic data pragmas', 'testdata.oph', 'testdata.bin')
        test_file('Undocumented instructions', 'test6510.oph', 'test6510.bin',
                  ['-u'])
        test_file('65c02 extensions', 'test65c02.oph', 'test65c02.bin', ['-c'])
        test_file('4502 extensions', 'test4502.oph', 'test4502.bin', ['-4'])
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


def test_expressions():
    print "\n==== EXPRESSIONS AND LABELS ===="
    test_string('Basic addition', '.byte 3+2', '\x05')
    test_string('Basic subtraction', '.byte 3-2', '\x01')
    test_string('Basic multiplication', '.byte 3*2', '\x06')
    test_string('Basic division', '.byte 6/2', '\x03')
    test_string('Basic bit-union', '.byte 5|9', '\x0d')
    test_string('Basic bit-intersection', '.byte 5&9', '\x01')
    test_string('Basic bit-toggle', '.byte 5^9', '\x0c')
    test_string('Division truncation', '.byte 5/2', '\x02')
    test_string('Overflow', '.byte $FF*$10', '')
    test_string('Multibyte overflow', '.word $FF*$10', '\xf0\x0f')
    test_string('Masked overflow', '.byte $FF*$10&$FF', '\xf0')
    test_string('Underflow', '.byte 2-3', '')
    test_string('Masked underflow', '.byte 2-3&$FF', '\xff')
    test_string('Arithmetic precedence', '.byte 2+3*4-6/2', '\x0b')
    test_string('Parentheses', '.byte [2+3]*[4-6/2]', '\x05')
    test_string('String escapes',
                '.byte "The man said, \\"The \\\\ is Windowsy.\\""',
                'The man said, "The \\ is Windowsy."')
    test_string('Byte selector precedence',
                '.byte >$d000+32,>[$d000+32],<[$D000-275]',
                '\xf0\xd0\xed')
    test_string('Named labels', '.org $6948\nl: .word l', 'Hi')
    test_string('.alias directive (basic)', '.alias hi $6948\n.word hi', 'Hi')
    test_string('.alias directive (derived)',
                '.alias hi $6948\n.alias ho hi+$600\n.word hi,ho', 'HiHo')
    test_string('.alias directive (circular)',
                '.alias a c+1\n.alias b a+3\n.alias c b-4\n.word a, b, c',
                '')
    test_string('.advance directive (basic)',
                'lda #$05\n.advance $05\n.byte ^',
                '\xa9\x05\x00\x00\x00\x05')
    test_string('.advance directive (filler)',
                'lda #$05\nf: .advance $05,f+3\n.byte ^',
                '\xa9\x05\x05\x05\x05\x05')
    test_string('.advance no-op', 'lda #$05\n.advance $02\n.byte ^',
                '\xa9\x05\x02')
    test_string('.advance failure', 'lda #$05\n.advance $01\n.byte ^', '')
    test_string('.checkpc, space > 0', 'lda #$05\n.checkpc $10', '\xa9\x05')
    test_string('.checkpc, space = 0', 'lda #$05\n.checkpc 2', '\xa9\x05')
    test_string('.checkpc, space < 0', 'lda $05\n.checkpc 1', '')
    test_string('A X Y usable as labels',
                '.alias a 1\n.alias x 2\n.alias y 3\n'
                'lda (a+x+y),y\nlda (x+y,x)',
                '\xb1\x06\xa1\x05')
    test_string('Opcodes usable as labels',
                'ldy #$00\n dey: dey\n bne dey',
                '\xa0\x00\x88\xd0\xfd')


def test_segments():
    print("\n==== ASSEMBLY SEGMENTS ====")
    test_string('Segments (basic)',
                '.org $41\n'
                '.data\n'
                '.org $61\n'
                'd:\n'
                '.text\n'
                'l: .byte l, d', 'Aa')
    test_string('Data cleanliness', '.byte 65\n.data\n.byte 65', '')
    test_string('.space directive',
                '.data\n.org $41\n.space a 2\n.space b 1\n.space c 1\n'
                '.text\n.byte a, b, c\n', 'ACD')
    test_string('Multiple named segments',
                '.data\n.org $41\n.data a\n.org $61\n.data b\n.org $4a\n'
                '.data\n.space q 1\n.data a\n.space r 1\n.data b\n.space s 1\n'
                '.text\n.org $10\n.text a\n.org $20\n'
                '.text\n.byte ^,q,r,s\n'
                '.text a\n.byte ^,q,r,s\n',
                '\x10AaJ\x20AaJ')


def test_scopes():
    print("\n==== LABEL SCOPING ====")
    test_string('Repeated labels, different scopes',
                '.org $41\n'
                '.scope\n'
                '_l: .byte _l\n'
                '.scend\n'
                '.scope\n'
                '_l: .byte _l\n'
                '.scend\n', 'AB')
    test_string('Data hiding outside of scope',
                '.org $41\n'
                '.scope\n'
                '_l: .byte _l\n'
                '.scend\n'
                '    .byte _l\n', '')
    test_string('Repeated labels, nested scopes',
                '.org $41\n'
                '.scope\n'
                '_l: .byte _l\n'
                '.scope\n'
                '_l: .byte _l\n'
                '.scend\n'
                '    .byte _l\n'
                '.scend\n', 'ABA')
    test_string('Anonymous labels (basic)',
                '.org $41\n'
                '* .byte -, +\n'
                '* .byte -, --\n', 'ACCA')
    test_string('Anonymous labels (across scopes)',
                '.org $41\n'
                '* .byte -, +\n'
                '.scope\n'
                '* .byte -, --\n'
                '.scend\n', 'ACCA')


def test_macros():
    print("\n==== MACROS ====")
    test_string('Basic macros',
                '.macro greet\n'
                '  .byte "hi"\n'
                '.macend\n'
                '`greet\n.invoke greet', "hihi")
    test_string('Macros with arguments',
                '.macro greet\n'
                '  .byte "hi",_1\n'
                '.macend\n'
                "`greet 'A\n.invoke greet 'B", "hiAhiB")
    test_string('Macros invoking macros',
                '.macro inner\n'
                '  .byte " there"\n'
                '.macend\n'
                '.macro greet\n'
                '  .byte "hi"\n'
                '  `inner\n'
                '.macend\n'
                "`greet", "hi there")
    test_string('Macros defining macros (illegal)',
                '.macro greet\n'
                '.macro inner\n'
                '  .byte " there"\n'
                '.macend\n'
                '  .byte "hi"\n'
                '  `inner\n'
                '.macend\n'
                "`greet", "")
    test_string('Fail on infinite recursion',
                '.macro inner\n'
                '  .byte " there"\n'
                '  `greet\n'
                '.macend\n'
                '.macro greet\n'
                '  .byte "hi"\n'
                '  `inner\n'
                '.macend\n'
                "`greet", "")


def test_subfiles():
    print("\n==== COMPILATION UNITS ====")
    test_string(".include pragma", '.include "baseinc.oph"', 'BASIC\n')
    test_string(".include repeated",
                '.include "baseinc.oph"\n.include "baseinc.oph"',
                'BASIC\nBASIC\n')
    test_string(".require pragma", '.require "baseinc.oph"', 'BASIC\n')
    test_string(".include before .require",
                '.include "baseinc.oph"\n.require "baseinc.oph"',
                'BASIC\n')
    test_string(".require before .include",
                '.require "baseinc.oph"\n.include "baseinc.oph"',
                'BASIC\nBASIC\n')
    test_string(".require same file twice with different paths",
                '.include "baseinc.oph"\n.include "sub/baseinc.oph"',
                'BASIC\nSUB 1 START\nSUB 1 END\n')
    test_string(".require different files with identical paths",
                '.include "sub/sub/sub.oph"',
                'SUB 2 START\nSUB 1 START\nBASIC\nSUB 1 END\nSUB 2 END\n')
    test_string(".charmap (basic)",
                '.charmap \'A, "abcdefghijklmnopqrstuvwxyz"\n'
                '.charmap \'a, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"\n'
                '.byte "hELLO, wORLD!"', "Hello, World!")
    test_string(".charmap (reset)",
                '.charmap \'A, "abcdefghijklmnopqrstuvwxyz"\n'
                '.charmap \'a, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"\n'
                '.byte "hELLO, wORLD!",10\n'
                '.charmap\n'
                '.byte "hELLO, wORLD!",10\n',
                "Hello, World!\nhELLO, wORLD!\n")
    test_string(".charmap (out of range)",
                '.charmap 250, "ABCDEFGHIJKLM"\n.byte 250,251',
                '')
    test_string(".charmapbin (basic)",
                '.charmapbin "../examples/petscii.map"\n.byte "hELLO, wORLD!"',
                "Hello, World!")
    test_string(".charmapbin (illegal)",
                '.charmapbin "baseinc.bin"\n.byte "hELLO, wORLD!"', '')
    test_string(".incbin (basic)", '.incbin "baseinc.bin"', "BASIC\n")
    test_string(".incbin (hardcoded offset)",
                '.incbin "baseinc.bin",3', "IC\n")
    test_string(".incbin (hardcoded offset and length)",
                '.incbin "baseinc.bin",3,2', "IC")
    test_string(".incbin (softcoded offset and length)",
                '.alias off len+1\n.alias len 2\n'
                '.incbin "baseinc.bin",off,len', "IC")
    test_string(".incbin (length too long)",
                '.byte 65\n.incbin "baseinc.bin",3,4', "")
    test_string(".incbin (negative offset)",
                '.byte 65\n.incbin "baseinc.bin",1-5,4', "")
    test_string(".incbin (offset = size)",
                '.byte 65\n.incbin "baseinc.bin",6', "A")
    test_string(".incbin (offset > size)",
                '.byte 65\n.incbin "baseinc.bin",7', "")
    test_string(".incbin (softcoded length too long)",
                '.alias off len\n.alias len 4\n'
                '.byte 65\n.incbin "baseinc.bin",off,len', "")
    test_string(".incbin (softcoded negative offset)",
                '.alias off 1-5\n'
                '.byte 65\n.incbin "baseinc.bin",off,4', "")
    test_string(".incbin (softcoded offset = size)",
                '.alias off 6\n'
                '.byte 65\n.incbin "baseinc.bin",off', "A")
    test_string(".incbin (softcoded offset > size)",
                '.alias off 7\n'
                '.byte 65\n.incbin "baseinc.bin",off', "")


def test_systematic():
    test_outfile()
    test_transforms()
    test_expressions()
    test_segments()
    test_scopes()
    test_macros()
    test_subfiles()


if __name__ == '__main__':
    print "Using Python interpreter:", pythonpath

    test_basic()
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
    if failed == 0:
        test_systematic()
    else:
        print "\nBasic test cases failed, aborting test."

    if failed > 0:
        print "\nTotal test case failures: %d" % failed
    else:
        print "\nAll test cases succeeded"
