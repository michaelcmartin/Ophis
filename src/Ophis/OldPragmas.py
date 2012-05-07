"""P65-Perl compatibility pragmas

    Additional assembler directives to permit assembly of
    old P65-Perl sources.  This is not, in itself, sufficient,
    as the precedence of < and > vs. + and - has changed
    between P65-Perl and Ophis.

    Supported pragmas are: .ascii (byte), .address (word),
    .segment (text), .code (text), and .link."""

# Copyright 2002-2012 Michael C. Martin and additional contributors.
# You may use, modify, and distribute this file under the MIT
# license: See README for details.

import Ophis.CorePragmas as core

pragmaAscii   = core.pragmaByte
pragmaAddress = core.pragmaWord
pragmaSegment = core.pragmaText
pragmaCode    = core.pragmaText

def pragmaLink(ppt, line, result):
    "Load a file in a precise memory location."
    filename = line.expect("STRING").value
    newPC = FE.parse_expr(line)
    line.expect("EOL")
    result.append(IR.Node(ppt, "SetPC", newPC))
    if type(filename)==str:    result.append(FE.parse_file(ppt, filename))
