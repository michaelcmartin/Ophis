"""Command line options data."""

import argparse

# Copyright 2002-2025 Michael C. Martin and additional contributors.
# You may use, modify, and distribute this file under the MIT
# license: See README for details.

enable_branch_extend = True
enable_undoc_ops = False
enable_65c02_exts = False
enable_4502_exts = False

warn_on_branch_extend = True

print_summary = True
print_loaded_files = False
print_pass = False
print_ir = False
print_labels = False

infiles = None
outfile = None
listfile = None
mapfile = None


def parse_args(args):
    "Populate the module's globals based on the command-line options given."
    global enable_collapse, enable_branch_extend
    global enable_undoc_ops, enable_65c02_exts, enable_4502_exts
    global warn_on_branch_extend
    global print_summary, print_loaded_files
    global print_pass, print_ir, print_labels
    global infiles, outfile, listfile, mapfile

    program_description = "Ophis 6502 series cross-assembler"

    parser = argparse.ArgumentParser(description=program_description)

    parser.add_argument(
        "srcfile", nargs="+", help="Input filenames (concatenated at assemble time)"
    )
    parser.add_argument("-o", "--outfile", help="Output filename (default: ophis.bin)")
    parser.add_argument("-l", "--listfile", help="Create program listing")
    parser.add_argument("-m", "--mapfile", help="Create label-address map")
    parser.add_argument(
        "--version", action="version", version=f"{program_description}, version 2.3-dev"
    )

    ingrp = parser.add_argument_group("Input options")
    ingrp.add_argument(
        "-u",
        "--undoc",
        action="store_true",
        default=False,
        help="Enable 6502 undocumented opcodes",
    )
    ingrp.add_argument(
        "-c",
        "--65c02",
        action="store_true",
        default=False,
        dest="c02",
        help="Enable 65c02 extended instruction set",
    )
    ingrp.add_argument(
        "-4",
        "--4502",
        action="store_true",
        default=False,
        dest="csg4502",
        help="Enable 4502 extended instruction set",
    )

    outgrp = parser.add_argument_group("Console output options")
    outgrp.add_argument(
        "-v", "--verbose", action="store_const", const=2, help="Verbose mode", default=1
    )
    outgrp.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        help="Quiet mode",
        dest="verbose",
        const=0,
    )
    outgrp.add_argument(
        "-d", "--debug", action="count", dest="verbose", help=argparse.SUPPRESS
    )
    outgrp.add_argument(
        "--no-warn",
        action="store_false",
        dest="warn",
        default=True,
        help="Do not print warnings",
    )

    bingrp = parser.add_argument_group("Compilation options")
    bingrp.add_argument(
        "--no-branch-extend",
        action="store_false",
        dest="enable_branch_extend",
        default="True",
        help="Disable branch-extension pass",
    )

    options = parser.parse_args(args)

    if options.c02 and options.undoc:
        parser.error("--undoc and --65c02 are mutually exclusive")
    if options.c02 and options.csg4502:
        parser.error("--65c02 and --4502 are mutually exclusive")
    if options.csg4502 and options.undoc:
        parser.error("--undoc and --4502 are mutually exclusive")

    infiles = options.srcfile
    outfile = options.outfile
    listfile = options.listfile
    mapfile = options.mapfile
    enable_branch_extend = options.enable_branch_extend
    enable_undoc_ops = options.undoc
    enable_65c02_exts = options.c02
    enable_4502_exts = options.csg4502
    warn_on_branch_extend = options.warn
    print_summary = options.verbose > 0  # no options set
    print_loaded_files = options.verbose > 1  # v
    print_pass = options.verbose > 2  # dd
    print_ir = options.verbose > 3  # ddd
    print_labels = options.verbose > 4  # dddd
