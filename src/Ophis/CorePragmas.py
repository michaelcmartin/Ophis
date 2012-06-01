"""Core pragmas

    Provides the core assembler directives."""

# Copyright 2002-2012 Michael C. Martin and additional contributors.
# You may use, modify, and distribute this file under the MIT
# license: See README for details.

import Ophis.IR as IR
import Ophis.Frontend as FE
import Ophis.Errors as Err

loadedfiles = {}
basecharmap = "".join([chr(x) for x in range(256)])
currentcharmap = basecharmap


def reset():
    global loadedfiles, currentcharmap, basecharmap
    loadedfiles = {}
    currentcharmap = basecharmap


def pragmaInclude(ppt, line, result):
    "Includes a source file"
    filename = line.expect("STRING").value
    line.expect("EOL")
    if type(filename) == str:
        result.append(FE.parse_file(ppt, filename))


def pragmaRequire(ppt, line, result):
    "Includes a source file at most one time"
    filename = line.expect("STRING").value
    line.expect("EOL")
    if type(filename) == str:
        global loadedfiles
        if filename not in loadedfiles:
            loadedfiles[filename] = True
            result.append(FE.parse_file(ppt, filename))


def pragmaIncbin(ppt, line, result):
    "Includes a binary file"
    filename = line.expect("STRING").value
    line.expect("EOL")
    if type(filename) == str:
        try:
            f = file(filename, "rb")
            bytes = f.read()
            f.close()
        except IOError:
            Err.log("Could not read " + filename)
            return
        bytes = [IR.ConstantExpr(ord(x)) for x in bytes]
        result.append(IR.Node(ppt, "Byte", *bytes))


def pragmaCharmap(ppt, line, result):
    "Modify the character map."
    global currentcharmap, basecharmap
    bytes = readData(line)
    if len(bytes) == 0:
        currentcharmap = basecharmap
    else:
        try:
            base = bytes[0].data
            newsubstr = "".join([chr(x.data) for x in bytes[1:]])
            currentcharmap = currentcharmap[:base] + newsubstr + \
                             currentcharmap[base + len(newsubstr):]
            if len(currentcharmap) != 256 or base < 0 or base > 255:
                Err.log("Charmap replacement out of range")
                currentcharmap = currentcharmap[:256]
        except ValueError:
            Err.log("Illegal character in .charmap directive")


def pragmaCharmapbin(ppt, line, result):
    "Load a new character map from a file"
    global currentcharmap
    filename = line.expect("STRING").value
    line.expect("EOL")
    if type(filename) == str:
        try:
            f = file(filename, "rb")
            bytes = f.read()
            f.close()
        except IOError:
            Err.log("Could not read " + filename)
            return
        if len(bytes) == 256:
            currentcharmap = bytes
        else:
            Err.log("Character map " + filename + " not 256 bytes long")


def pragmaOrg(ppt, line, result):
    "Relocates the PC with no output"
    newPC = FE.parse_expr(line)
    line.expect("EOL")
    result.append(IR.Node(ppt, "SetPC", newPC))


def pragmaAdvance(ppt, line, result):
    "Outputs filler until reaching the target PC"
    newPC = FE.parse_expr(line)
    if str(line.lookahead(0)) == ",":
        line.pop()
        fillexpr = FE.parse_expr(line)
    else:
        fillexpr = IR.ConstantExpr(0)
    line.expect("EOL")
    result.append(IR.Node(ppt, "Advance", newPC, fillexpr))


def pragmaCheckpc(ppt, line, result):
    "Enforces that the PC has not exceeded a certain point"
    target = FE.parse_expr(line)
    line.expect("EOL")
    result.append(IR.Node(ppt, "CheckPC", target))


def pragmaAlias(ppt, line, result):
    "Assigns an arbitrary label"
    lbl = line.expect("LABEL").value
    target = FE.parse_expr(line)
    result.append(IR.Node(ppt, "Label", lbl, target))


def pragmaSpace(ppt, line, result):
    "Reserves space in a data segment for a variable"
    lbl = line.expect("LABEL").value
    size = line.expect("NUM").value
    line.expect("EOL")
    result.append(IR.Node(ppt, "Label", lbl, IR.PCExpr()))
    result.append(IR.Node(ppt, "SetPC",
                          IR.SequenceExpr([IR.PCExpr(), "+",
                                           IR.ConstantExpr(size)])))


def pragmaText(ppt, line, result):
    "Switches to a text segment"
    next = line.expect("LABEL", "EOL")
    if next.type == "LABEL":
        line.expect("EOL")
        segment = next.value
    else:
        segment = "*text-default*"
    result.append(IR.Node(ppt, "TextSegment", segment))


def pragmaData(ppt, line, result):
    "Switches to a data segment (no output allowed)"
    next = line.expect("LABEL", "EOL")
    if next.type == "LABEL":
        line.expect("EOL")
        segment = next.value
    else:
        segment = "*data-default*"
    result.append(IR.Node(ppt, "DataSegment", segment))


def readData(line):
    "Read raw data from a comma-separated list"
    if line.lookahead(0).type == "STRING":
        data = [IR.ConstantExpr(ord(x))
                for x in line.expect("STRING").value.translate(currentcharmap)]
    else:
        data = [FE.parse_expr(line)]
    next = line.expect(',', 'EOL').type
    while next == ',':
        if line.lookahead(0).type == "STRING":
            data.extend([IR.ConstantExpr(ord(x))
                         for x in line.expect("STRING").value])
        else:
            data.append(FE.parse_expr(line))
        next = line.expect(',', 'EOL').type
    return data


def pragmaByte(ppt, line, result):
    "Raw data, a byte at a time"
    bytes = readData(line)
    result.append(IR.Node(ppt, "Byte", *bytes))


def pragmaWord(ppt, line, result):
    "Raw data, a word at a time, little-endian"
    words = readData(line)
    result.append(IR.Node(ppt, "Word", *words))


def pragmaDword(ppt, line, result):
    "Raw data, a double-word at a time, little-endian"
    dwords = readData(line)
    result.append(IR.Node(ppt, "Dword", *dwords))


def pragmaWordbe(ppt, line, result):
    "Raw data, a word at a time, big-endian"
    words = readData(line)
    result.append(IR.Node(ppt, "WordBE", *words))


def pragmaDwordbe(ppt, line, result):
    "Raw data, a dword at a time, big-endian"
    dwords = readData(line)
    result.append(IR.Node(ppt, "DwordBE", *dwords))


def pragmaScope(ppt, line, result):
    "Create a new lexical scoping block"
    line.expect("EOL")
    result.append(IR.Node(ppt, "ScopeBegin"))


def pragmaScend(ppt, line, result):
    "End the innermost lexical scoping block"
    line.expect("EOL")
    result.append(IR.Node(ppt, "ScopeEnd"))


def pragmaMacro(ppt, line, result):
    "Begin a macro definition"
    lbl = line.expect("LABEL").value
    line.expect("EOL")
    result.append(IR.Node(ppt, "MacroBegin", lbl))


def pragmaMacend(ppt, line, result):
    "End a macro definition"
    line.expect("EOL")
    result.append(IR.Node(ppt, "MacroEnd"))


def pragmaInvoke(ppt, line, result):
    macro = line.expect("LABEL").value
    if line.lookahead(0).type == "EOL":
        args = []
    else:
        args = readData(line)
    result.append(IR.Node(ppt, "MacroInvoke", macro, *args))
