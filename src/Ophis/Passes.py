"""The Ophis Assembler passes

    Ophis's design philosophy is to build the IR once, then run a great
    many assembler passes over the result.  Thus, each pass does a
    single, specialized job.  When strung together, the full
    translation occurs.  This structure also makes the assembler
    very extensible; additional analyses or optimizations may be
    added as new subclasses of Pass."""

# Copyright 2002-2014 Michael C. Martin and additional contributors.
# You may use, modify, and distribute this file under the MIT
# license: See README for details.

import sys
import Ophis.Errors as Err
import Ophis.IR as IR
import Ophis.Opcodes as Ops
import Ophis.CmdLine as Cmd
import Ophis.Listing as Listing
import Ophis.Macro as Macro


class Pass(object):
    """Superclass for all assembler passes.  Automatically handles IR
    types that modify the environent's structure, and by default
    raises an error on anything else.  Override visitUnknown in your
    extension pass to produce a pass that accepts everything."""
    name = "Default Pass"

    def __init__(self):
        self.writeOK = True

    def visitNone(self, node, env):
        pass

    def visitSEQUENCE(self, node, env):
        Err.currentpoint = node.ppt
        for n in node.data:
            n.accept(self, env)

    def visitDataSegment(self, node, env):
        self.writeOK = False
        env.setsegment(node.data[0])

    def visitTextSegment(self, node, env):
        self.writeOK = True
        env.setsegment(node.data[0])

    def visitScopeBegin(self, node, env):
        env.newscope()

    def visitScopeEnd(self, node, env):
        env.endscope()

    def visitUnknown(self, node, env):
        Err.log("Internal error!  " + self.name +
                " cannot understand node type " + node.nodetype)

    def prePass(self):
        pass

    def postPass(self):
        pass

    def go(self, node, env):
        """Prepares the environment and runs this pass, possibly
        printing debugging information."""
        if Err.count == 0:
            if Cmd.print_pass:
                print("Running: " + self.name, file=sys.stderr)
            env.reset()
            self.prePass()
            node.accept(self, env)
            self.postPass()
            env.reset()
            if Cmd.print_labels:
                print("Current labels:", file=sys.stderr)
                print(env, file=sys.stderr)
            if Cmd.print_ir:
                print("Current IR:", file=sys.stderr)
                print(node, file=sys.stderr)


class FixPoint(object):
    """A specialized class that is not a pass but can be run like one.
    This class takes a list of passes and a "fixpoint" function."""
    def __init__(self, name, passes, fixpoint):
        self.name = name
        self.passes = passes
        self.fixpoint = fixpoint

    def go(self, node, env):
        """Runs this FixPoint's passes, in order, until the fixpoint
        is true.  Always runs the passes at least once."""
        for i in range(100):
            if Err.count != 0:
                break
            for p in self.passes:
                p.go(node, env)
            if Err.count != 0:
                break
            if self.fixpoint():
                break
            if Cmd.print_pass:
                print("Fixpoint failed, looping back", file=sys.stderr)
        else:
            Err.log("Can't make %s converge!  Maybe there's a recursive "
                    "dependency somewhere?" % self.name)


class DefineMacros(Pass):
    "Extract macro definitions and remove them from the IR"
    name = "Macro definition pass"

    def prePass(self):
        self.inDef = False
        self.nestedError = False

    def postPass(self):
        if self.inDef:
            Err.log("Unmatched .macro")
        elif Cmd.print_ir:
            print("Macro definitions:", file=sys.stderr)
            Macro.dump()

    def visitMacroBegin(self, node, env):
        if self.inDef:
            Err.log("Nested macro definition")
            self.nestedError = True
        else:
            Macro.newMacro(node.data[0])
            node.nodetype = "None"
            node.data = []
            self.inDef = True

    def visitMacroEnd(self, node, env):
        if self.inDef:
            Macro.endMacro()
            node.nodetype = "None"
            node.data = []
            self.inDef = False
        elif not self.nestedError:
            Err.log("Unmatched .macend")

    def visitUnknown(self, node, env):
        if self.inDef:
            Macro.registerNode(node)
            node.nodetype = "None"
            node.data = []


class ExpandMacros(Pass):
    "Replace macro invocations with the appropriate text"
    name = "Macro expansion pass"

    def prePass(self):
        self.changed = False

    def visitMacroInvoke(self, node, env):
        replacement = Macro.expandMacro(node.ppt, node.data[0], node.data[1:])
        node.nodetype = replacement.nodetype
        node.data = replacement.data
        self.changed = True

    def visitUnknown(self, node, env):
        pass


class InitLabels(Pass):
    "Finds all reachable labels"
    name = "Label initialization pass"

    def __init__(self):
        Pass.__init__(self)
        self.labelmap = {}
        self.runcount = 0

    def prePass(self):
        self.changed = False
        self.PCvalid = True
        self.runcount += 1

    def visitAdvance(self, node, env):
        self.PCvalid = node.data[0].valid(env, self.PCvalid)

    def visitSetPC(self, node, env):
        self.PCvalid = node.data[0].valid(env, self.PCvalid)

    def visitLabel(self, node, env):
        (label, val) = node.data
        fulllabel = "%d:%s" % (env.stack[0], label)
        if fulllabel in self.labelmap and self.labelmap[fulllabel] is not node:
            Err.log("Duplicate label definition '%s'" % label)
        if fulllabel not in self.labelmap:
            self.labelmap[fulllabel] = node
        if val.valid(env, self.PCvalid) and label not in env:
            env[label] = 0
            self.changed = True
        if label in ['a', 'x', 'y'] and self.runcount == 1:
            print(str(node.ppt) + ": WARNING: " \
                "using register name as label", file=sys.stderr)
        if label in Ops.opcodes and self.runcount == 1:
            print(str(node.ppt) + ": WARNING: " \
                "using opcode name as label", file=sys.stderr)

    def visitUnknown(self, node, env):
        pass


class CircularityCheck(Pass):
    "Checks for circular label dependencies"
    name = "Circularity check pass"

    def prePass(self):
        self.changed = False
        self.PCvalid = True

    def visitAdvance(self, node, env):
        PCvalid = self.PCvalid
        self.PCvalid = node.data[0].valid(env, self.PCvalid)
        if not node.data[0].valid(env, PCvalid):
            Err.log("Undefined or circular reference on .advance")

    def visitSetPC(self, node, env):
        PCvalid = self.PCvalid
        self.PCvalid = node.data[0].valid(env, self.PCvalid)
        if not node.data[0].valid(env, PCvalid):
            Err.log("Undefined or circular reference on program counter set")

    def visitCheckPC(self, node, env):
        if not node.data[0].valid(env, self.PCvalid):
            Err.log("Undefined or circular reference on program counter check")

    def visitLabel(self, node, env):
        (label, val) = node.data
        if not val.valid(env, self.PCvalid):
            Err.log("Undefined or circular dependency for label '%s'" % label)

    def visitUnknown(self, node, env):
        pass


class CheckExprs(Pass):
    "Ensures all expressions can resolve"
    name = "Expression checking pass"

    def visitUnknown(self, node, env):
        # Throw away result, just confirm validity of all expressions
        for i in [x for x in node.data if isinstance(x, IR.Expr)]:
            i.value(env)


class EasyModes(Pass):
    "Assigns address modes to hardcoded and branch instructions"
    name = "Easy addressing modes pass"

    def visitMemory(self, node, env):
        if Ops.opcodes[node.data[0]][Ops.modes.index("Relative")] is not None:
            node.nodetype = "Relative"
            return
        if Ops.opcodes[node.data[0]][Ops.modes.index("RelativeLong")] is not None:
            node.nodetype = "RelativeLong"
            return
        if node.data[1].hardcoded:
            if not collapse_no_index(node, env):
                node.nodetype = "Absolute"

    def visitMemoryX(self, node, env):
        if node.data[1].hardcoded:
            if not collapse_x(node, env):
                node.nodetype = "AbsoluteX"

    def visitMemoryY(self, node, env):
        if node.data[1].hardcoded:
            if not collapse_y(node, env):
                node.nodetype = "AbsoluteY"

    def visitMemory2(self, node, env):
        node.nodetype = "ZPRelative"

    def visitPointer(self, node, env):
        if node.data[1].hardcoded:
            if not collapse_no_index_ind(node, env):
                node.nodetype = "Indirect"

    def visitPointerX(self, node, env):
        if node.data[1].hardcoded:
            if not collapse_x_ind(node, env):
                node.nodetype = "AbsIndX"

    def visitPointerY(self, node, env):
        if node.data[1].hardcoded:
            if not collapse_y_ind(node, env):
                node.nodetype = "AbsIndY"

    def visitPointerSPY(self, node, env):
        if node.data[1].hardcoded:
            if not collapse_spy_ind(node, env):
                node.nodetype = "AbsIndSPY"

    def visitPointerZ(self, node, env):
        if node.data[1].hardcoded:
            if not collapse_z_ind(node, env):
                node.nodetype = "AbsIndZ"

    def visitUnknown(self, node, env):
        pass


class PCTracker(Pass):
    "Superclass for passes that need an accurate program counter."
    name = "**BUG** PC Tracker Superpass used directly"

    def visitSetPC(self, node, env):
        env.setPC(node.data[0].value(env))

    def visitAdvance(self, node, env):
        env.setPC(node.data[0].value(env))

    def visitImplied(self, node, env):
        env.incPC(1)

    def visitImmediate(self, node, env):
        env.incPC(2)

    def visitImmediateLong(self, node, env):
        env.incPC(3)

    def visitIndirectX(self, node, env):
        env.incPC(2)

    def visitIndirectY(self, node, env):
        env.incPC(2)

    def visitIndirectSPY(self, node, env):
        env.incPC(2)

    def visitIndirectZ(self, node, env):
        env.incPC(2)

    def visitZPIndirect(self, node, env):
        env.incPC(2)

    def visitZeroPage(self, node, env):
        env.incPC(2)

    def visitZeroPageX(self, node, env):
        env.incPC(2)

    def visitZeroPageY(self, node, env):
        env.incPC(2)

    def visitRelative(self, node, env):
        env.incPC(2)

    def visitRelativeLong(self, node, env):
        env.incPC(3)

    def visitZPRelative(self, node, env):
        env.incPC(3)

    def visitIndirect(self, node, env):
        env.incPC(3)

    def visitAbsolute(self, node, env):
        env.incPC(3)

    def visitAbsoluteX(self, node, env):
        env.incPC(3)

    def visitAbsoluteY(self, node, env):
        env.incPC(3)

    def visitAbsIndX(self, node, env):
        env.incPC(3)

    def visitAbsIndY(self, node, env):
        env.incPC(3)

    def visitAbsIndZ(self, node, env):
        env.incPC(3)

    def visitMemory(self, node, env):
        env.incPC(3)

    def visitMemoryX(self, node, env):
        env.incPC(3)

    def visitMemoryY(self, node, env):
        env.incPC(3)

    def visitMemoryZ(self, node, env):
        env.incPC(3)

    def visitPointer(self, node, env):
        env.incPC(3)

    def visitPointerX(self, node, env):
        env.incPC(3)

    def visitPointerY(self, node, env):
        env.incPC(3)

    def visitCheckPC(self, node, env):
        pass

    def visitLabel(self, node, env):
        pass

    def visitByte(self, node, env):
        env.incPC(len(node.data))

    def visitByteRange(self, node, env):
        if node.data[1].valid(env):
            env.incPC(node.data[1].value(env))

    def visitWord(self, node, env):
        env.incPC(len(node.data) * 2)

    def visitDword(self, node, env):
        env.incPC(len(node.data) * 4)

    def visitWordBE(self, node, env):
        env.incPC(len(node.data) * 2)

    def visitDwordBE(self, node, env):
        env.incPC(len(node.data) * 4)


class UpdateLabels(PCTracker):
    "Computes the new values for all entries in the symbol table"
    name = "Label Update Pass"

    def prePass(self):
        self.changed = False

    def visitLabel(self, node, env):
        (label, val) = node.data
        old = env[label]
        env[label] = val.value(env)
        if old != env[label]:
            self.changed = True


class Collapse(PCTracker):
    "Selects as many zero-page instructions to convert as possible."
    name = "Instruction Collapse Pass"

    def prePass(self):
        self.changed = False

    def visitMemory(self, node, env):
        self.changed |= collapse_no_index(node, env)
        PCTracker.visitMemory(self, node, env)

    def visitMemoryX(self, node, env):
        self.changed |= collapse_x(node, env)
        PCTracker.visitMemoryX(self, node, env)

    def visitMemoryY(self, node, env):
        self.changed |= collapse_y(node, env)
        PCTracker.visitMemoryY(self, node, env)

    def visitMemoryZ(self, node, env):
        PCTracker.visitMemoryZ(self, node, env)

    def visitPointer(self, node, env):
        self.changed |= collapse_no_index_ind(node, env)
        PCTracker.visitPointer(self, node, env)

    def visitPointerX(self, node, env):
        self.changed |= collapse_x_ind(node, env)
        PCTracker.visitPointerX(self, node, env)

    def visitPointerY(self, node, env):
        self.changed |= collapse_y_ind(node, env)
        PCTracker.visitPointerY(self, node, env)

    # Previously zero-paged elements may end up un-zero-paged by
    # the branch extension pass. Force them to Absolute equivalents
    # if this happens.

    def visitImmediate(self, node, env):
        if node.data[1].value(env) >= 0x100:
            if Ops.opcodes[node.data[0]][Ops.modes.index("ImmediateLong")] is not None:
                node.nodetype = "ImmediateLong"
                PCTracker.visitImmediateLong(self, node, env)
                self.changed = True
                return
        PCTracker.visitImmediate(self, node, env)

    def visitZeroPage(self, node, env):
        if node.data[1].value(env) >= 0x100:
            if Ops.opcodes[node.data[0]][Ops.modes.index("Absolute")] is not None:
                node.nodetype = "Absolute"
                PCTracker.visitAbsolute(self, node, env)
                self.changed = True
                return
        PCTracker.visitZeroPage(self, node, env)

    def visitZeroPageX(self, node, env):
        if node.data[1].value(env) >= 0x100:
            if Ops.opcodes[node.data[0]][Ops.modes.index("Absolute, X")] is not None:
                node.nodetype = "AbsoluteX"
                PCTracker.visitAbsoluteX(self, node, env)
                self.changed = True
                return
        PCTracker.visitZeroPageX(self, node, env)

    def visitZeroPageY(self, node, env):
        if node.data[1].value(env) >= 0x100:
            if Ops.opcodes[node.data[0]][Ops.modes.index("Absolute, Y")] is not None:
                node.nodetype = "AbsoluteY"
                PCTracker.visitAbsoluteY(self, node, env)
                self.changed = True
                return
        PCTracker.visitZeroPageY(self, node, env)


def collapse_no_index(node, env):
    """Transforms a Memory node into a ZeroPage one if possible.
    Returns boolean indicating whether or not it made the collapse."""
    if node.data[1].value(env) < 0x100:
        if Ops.opcodes[node.data[0]][Ops.modes.index("Zero Page")] is not None:
            node.nodetype = "ZeroPage"
            return True
    return False


def collapse_x(node, env):
    """Transforms a MemoryX node into a ZeroPageX one if possible.
    Returns boolean indicating whether or not it made the collapse."""
    if node.data[1].value(env) < 0x100:
        if Ops.opcodes[node.data[0]][Ops.modes.index("Zero Page, X")] is not None:
            node.nodetype = "ZeroPageX"
            return True
    return False


def collapse_y(node, env):
    """Transforms a MemoryY node into a ZeroPageY one if possible.
    Returns boolean indicating whether or not it made the collapse."""
    if node.data[1].value(env) < 0x100:
        if Ops.opcodes[node.data[0]][Ops.modes.index("Zero Page, Y")] is not None:
            node.nodetype = "ZeroPageY"
            return True
    return False

def collapse_no_index_ind(node, env):
    """Transforms a Pointer node into a ZPIndirect one if possible.
    Returns boolean indicating whether or not it made the collapse."""
    if node.data[1].value(env) < 0x100:
        if Ops.opcodes[node.data[0]][Ops.modes.index("(Zero Page)")] is not None:
            node.nodetype = "ZPIndirect"
            return True
    return False


def collapse_x_ind(node, env):
    """Transforms a PointerX node into an IndirectX one if possible.
    Returns boolean indicating whether or not it made the collapse."""
    if node.data[1].value(env) < 0x100:
        if Ops.opcodes[node.data[0]][Ops.modes.index("(Zero Page, X)")] is not None:
            node.nodetype = "IndirectX"
            return True
    return False


def collapse_y_ind(node, env):
    """Transforms a PointerY node into an IndirectY one if possible.
    Returns boolean indicating whether or not it made the collapse."""
    if node.data[1].value(env) < 0x100:
        if Ops.opcodes[node.data[0]][Ops.modes.index("(Zero Page), Y")] is not None:
            node.nodetype = "IndirectY"
            return True
    return False

def collapse_spy_ind(node, env):
    """Transforms a PointerSPY node into an IndirectY one if possible.
    Returns boolean indicating whether or not it made the collapse."""
    if node.data[1].value(env) < 0x100:
        if Ops.opcodes[node.data[0]][Ops.modes.index("(Zero Page, SP), Y")] is not None:
            node.nodetype = "IndirectSPY"
            return True
    return False

def collapse_z_ind(node, env):
    """Transforms a PointerZ node into an IndirectZ one if possible.
    Returns boolean indicating whether or not it made the collapse."""
    if node.data[1].value(env) < 0x100:
        if Ops.opcodes[node.data[0]][Ops.modes.index("(Zero Page), Z")] is not None:
            node.nodetype = "IndirectZ"
            return True
    return False


class ExtendBranches(PCTracker):
    """Eliminates any branch instructions that would end up going past
    the 128-byte range, and replaces them with a branch-jump pair."""
    name = "Branch Expansion Pass"
    reversed = {'bcc': 'bcs',
                'bcs': 'bcc',
                'beq': 'bne',
                'bmi': 'bpl',
                'bne': 'beq',
                'bpl': 'bmi',
                'bvc': 'bvs',
                'bvs': 'bvc',
                # 65c02 ones. 'bra' is special, though, having no inverse
                'bbr0': 'bbs0',
                'bbs0': 'bbr0',
                'bbr1': 'bbs1',
                'bbs1': 'bbr1',
                'bbr2': 'bbs2',
                'bbs2': 'bbr2',
                'bbr3': 'bbs3',
                'bbs3': 'bbr3',
                'bbr4': 'bbs4',
                'bbs4': 'bbr4',
                'bbr5': 'bbs5',
                'bbs5': 'bbr5',
                'bbr6': 'bbs6',
                'bbs6': 'bbr6',
                'bbr7': 'bbs7',
                'bbs7': 'bbr7'
                }

    def prePass(self):
        self.changed = False

    def visitRelative(self, node, env):
        (opcode, expr) = node.data[:2]
        arg = expr.value(env)
        arg = arg - (env.getPC() + 2)
        if arg < -128 or arg > 127:
            if Cmd.enable_4502_exts:
                node.nodetype = "RelativeLong"
                if Cmd.warn_on_branch_extend:
                    print(str(node.ppt) + ": WARNING: " \
                        "branch out of range, replacing with 16-bit relative branch", file=sys.stderr)
            else:
                if opcode == 'bra':
                    # If BRA - BRanch Always - is out of range, it's a JMP.
                    node.data = ('jmp', expr, None)
                    node.nodetype = "Absolute"
                    if Cmd.warn_on_branch_extend:
                        print(str(node.ppt) + ": WARNING: " \
                            "bra out of range, replacing with jmp", file=sys.stderr)
                else:
                    # Otherwise, we replace it with a 'macro' of sorts by hand:
                    # $branch LOC -> $reversed_branch ^+5; JMP LOC
                    # We don't use temp labels here because labels need to have
                    # been fixed in place by this point, and JMP is always 3
                    # bytes long.
                    expansion = [IR.Node(node.ppt, "Relative",
                                     ExtendBranches.reversed[opcode],
                                     IR.SequenceExpr([IR.PCExpr(), "+",
                                                      IR.ConstantExpr(5)]),
                                     None),
                             IR.Node(node.ppt, "Absolute", 'jmp', expr, None)]
                    node.nodetype = 'SEQUENCE'
                    node.data = expansion
                    if Cmd.warn_on_branch_extend:
                        print(str(node.ppt) + ": WARNING: " + \
                                       opcode + " out of range, " \
                                       "replacing with " + \
                                       ExtendBranches.reversed[opcode] + \
                                       "/jmp combo", file=sys.stderr)
                    self.changed = True
                    node.accept(self, env)
        else:
            PCTracker.visitRelative(self, node, env)

    def visitZPRelative(self, node, env):
        (opcode, tested, expr) = node.data
        arg = expr.value(env)
        arg = arg - (env.getPC() + 3)
        if arg < -128 or arg > 127:
            # Otherwise, we replace it with a 'macro' of sorts by hand:
            # $branch LOC -> $reversed_branch ^+6; JMP LOC
            # We don't use temp labels here because labels need to have
            # been fixed in place by this point, and JMP is always 3
            # bytes long.
            expansion = [IR.Node(node.ppt, "ZPRelative",
                                 ExtendBranches.reversed[opcode],
                                 tested,
                                 IR.SequenceExpr([IR.PCExpr(), "+",
                                                  IR.ConstantExpr(6)])),
                         IR.Node(node.ppt, "Absolute", 'jmp', expr, None)]
            node.nodetype = 'SEQUENCE'
            node.data = expansion
            if Cmd.warn_on_branch_extend:
                print(str(node.ppt) + ": WARNING: " + \
                    opcode + " out of range, " \
                    "replacing with " + \
                    ExtendBranches.reversed[opcode] + \
                    "/jmp combo", file=sys.stderr)
            self.changed = True
            node.accept(self, env)
        else:
            PCTracker.visitZPRelative(self, node, env)


class NormalizeModes(Pass):
    """Eliminates the intermediate "Memory" and "Pointer" nodes,
    converting them to "Absolute"."""
    name = "Mode Normalization pass"

    def visitMemory(self, node, env):
        node.nodetype = "Absolute"

    def visitMemoryX(self, node, env):
        node.nodetype = "AbsoluteX"

    def visitMemoryY(self, node, env):
        node.nodetype = "AbsoluteY"

    def visitPointer(self, node, env):
        node.nodetype = "Indirect"

    def visitPointerX(self, node, env):
        node.nodetype = "AbsIndX"

    # If we ever hit a PointerY by this point, we have a bug.

    def visitPointerY(self, node, env):
        node.nodetype = "AbsIndY"

    def visitPointerZ(self, node, env):
        node.nodetype = "AbsIndZ"

    def visitUnknown(self, node, env):
        pass


class Assembler(Pass):
    """Converts the IR into a list of bytes, suitable for writing to
    a file."""
    name = "Assembler"

    # The self.listing field defined in prePass and referred to elsewhere
    # holds the necessary information to build the program listing later.
    # Each member of this list is either a string (in which case it is
    # a listed instruction to be echoed) or it is a tuple of
    # (startPC, bytes). Byte listings need to be interrupted when the
    # PC is changed by an .org, which may happen in the middle of
    # data definition blocks.
    def prePass(self):
        self.output = []
        self.code = 0
        self.data = 0
        self.filler = 0
        if Cmd.listfile is not None:
            self.listing = Listing.Listing(Cmd.listfile)
        else:
            self.listing = Listing.NullLister()
        if Cmd.mapfile is not None:
            self.mapper = Listing.LabelMapper(Cmd.mapfile)
        else:
            self.mapper = Listing.NullLabelMapper()

    def postPass(self):
        self.listing.dump()
        self.mapper.dump()
        if Cmd.print_summary and Err.count == 0:
            print("Assembly complete: %s bytes output " \
                               "(%s code, %s data, %s filler)" \
                               % (len(self.output),
                                  self.code, self.data, self.filler), file=sys.stderr)

    def outputbyte(self, expr, env, tee=None):
        'Outputs a byte, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x00 or val > 0xff:
                Err.log("Byte constant " + str(expr) + " out of range")
                val = 0
            self.output.append(int(val))
            if tee is not None:
                tee.append(self.output[-1])
        else:
            Err.log("Attempt to write to data segment")

    def outputword(self, expr, env, tee=None):
        'Outputs a little-endian word, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x0000 or val > 0xFFFF:
                Err.log("Word constant " + str(expr) + " out of range")
                val = 0
            self.output.append(int(val & 0xFF))
            self.output.append(int((val >> 8) & 0xFF))
            if tee is not None:
                tee.extend(self.output[-2:])
        else:
            Err.log("Attempt to write to data segment")

    def outputdword(self, expr, env, tee=None):
        'Outputs a little-endian dword, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x00000000 or val > 0xFFFFFFFF:
                Err.log("DWord constant " + str(expr) + " out of range")
                val = 0
            self.output.append(int(val & 0xFF))
            self.output.append(int((val >> 8) & 0xFF))
            self.output.append(int((val >> 16) & 0xFF))
            self.output.append(int((val >> 24) & 0xFF))
            if tee is not None:
                tee.extend(self.output[-4:])
        else:
            Err.log("Attempt to write to data segment")

    def outputword_be(self, expr, env, tee=None):
        'Outputs a big-endian word, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x0000 or val > 0xFFFF:
                Err.log("Word constant " + str(expr) + " out of range")
                val = 0
            self.output.append(int((val >> 8) & 0xFF))
            self.output.append(int(val & 0xFF))
            if tee is not None:
                tee.extend(self.output[-2:])
        else:
            Err.log("Attempt to write to data segment")

    def outputdword_be(self, expr, env, tee=None):
        'Outputs a big-endian dword, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x00000000 or val > 0xFFFFFFFF:
                Err.log("DWord constant " + str(expr) + " out of range")
                val = 0
            self.output.append(int((val >> 24) & 0xFF))
            self.output.append(int((val >> 16) & 0xFF))
            self.output.append(int((val >> 8) & 0xFF))
            self.output.append(int(val & 0xFF))
            if tee is not None:
                tee.extend(self.output[-4:])
        else:
            Err.log("Attempt to write to data segment")

    def relativize(self, expr, env, arglen):
        "Convert an expression into one for use in relative addressing"
        arg = expr.value(env)
        arg = arg - (env.getPC() + arglen + 1)
        if arg < -128 or arg > 127:
            Err.log("Branch target out of bounds")
            arg = 0
        if arg < 0:
            arg += 256
        return IR.ConstantExpr(arg)

    def relativizelong(self, expr, env, arglen):
        "Convert an expression into one for use in relative addressing"
        arg = expr.value(env)
        arg = arg - (env.getPC() + arglen)
        if arg < 0:
            arg += 65536
        return IR.ConstantExpr(arg)

    def listing_string(self, pc, binary, mode, opcode, val1, val2):
        base = " %04X " % pc
        base += (" %02X" * len(binary)) % tuple(binary)
        formats = ["",
                   "#$%02X",
                   "#$%04X",
                   "$%02X",
                   "$%02X, X",
                   "$%02X, Y",
                   "$%04X",
                   "$%04X, X",
                   "$%04X, Y",
                   "($%04X)",
                   "($%04X, X)",
                   "($%04X), Y",
                   "($%04X), Z",
                   "($%02X)",
                   "($%02X, X)",
                   "($%02X), Y",
                   "($%02X, SP), Y",
                   "($%02X), Z",
                   "$%04X",
                   "$%04X",
                   "$%02X, $%04X"]
        fmt = ("%-16s %-5s" % (base, opcode.upper())) + formats[mode]
        if val1 is None:
            return fmt
        elif val2 is None:
            arglen = Ops.lengths[mode]
            mask = 0xFF
            # Relative is a full address in a byte, so it also has the
            # 0xFFFF mask.
            if arglen == 2 or mode == Ops.modes.index("Relative"):
                mask = 0xFFFF
            return fmt % (val1 & mask)
        else:
            # Mode is "Zero Page, Relative"
            return fmt % (val1 & 0xFF, val2 & 0xFFFF)

    def assemble(self, node, mode, env):
        "A generic instruction called by the visitor methods themselves"
        (opcode, expr, expr2) = node.data
        bin_op = Ops.opcodes[opcode][mode]
        if bin_op is None:
            Err.log('%s does not have mode "%s"' % (opcode.upper(),
                                                    Ops.modes[mode]))
            return
        inst_bytes = []
        self.outputbyte(IR.ConstantExpr(bin_op), env, inst_bytes)
        arglen = Ops.lengths[mode]
        val1 = None
        val2 = None
        if expr is not None:
            val1 = expr.value(env)
        if expr2 is not None:
            val2 = expr2.value(env)
        if mode == Ops.modes.index("Zero Page, Relative"):
            expr2 = self.relativize(expr2, env, arglen)
            self.outputbyte(expr, env, inst_bytes)
            self.outputbyte(expr2, env, inst_bytes)
        else:
            if mode == Ops.modes.index("Relative"):
                expr = self.relativize(expr, env, arglen)
            elif mode == Ops.modes.index("RelativeLong"):
                expr = self.relativizelong(expr, env, arglen)
            if arglen == 1:
                self.outputbyte(expr, env, inst_bytes)
            elif arglen == 2:
                self.outputword(expr, env, inst_bytes)
        self.listing.listInstruction([node.ppt, self.listing_string(env.getPC(),
                                                         inst_bytes,
                                                         mode, opcode,
                                                         val1, val2)])
        env.incPC(1 + arglen)
        self.code += 1 + arglen

    def visitImplied(self, node, env):
        self.assemble(node,  Ops.modes.index("Implied"), env)

    def visitImmediate(self, node, env):
        self.assemble(node,  Ops.modes.index("Immediate"), env)

    def visitImmediateLong(self, node, env):
        self.assemble(node,  Ops.modes.index("ImmediateLong"), env)

    def visitZeroPage(self, node, env):
        self.assemble(node,  Ops.modes.index("Zero Page"), env)

    def visitZeroPageX(self, node, env):
        self.assemble(node,  Ops.modes.index("Zero Page, X"), env)

    def visitZeroPageY(self, node, env):
        self.assemble(node,  Ops.modes.index("Zero Page, Y"), env)

    def visitAbsolute(self, node, env):
        self.assemble(node,  Ops.modes.index("Absolute"), env)

    def visitAbsoluteX(self, node, env):
        self.assemble(node,  Ops.modes.index("Absolute, X"), env)

    def visitAbsoluteY(self, node, env):
        self.assemble(node,  Ops.modes.index("Absolute, Y"), env)

    def visitIndirect(self, node, env):
        self.assemble(node,  Ops.modes.index("(Absolute)"), env)

    def visitAbsIndX(self, node, env):
        self.assemble(node,  Ops.modes.index("(Absolute, X)"), env)

    def visitAbsIndY(self, node, env):
        self.assemble(node, Ops.modes.index("(Absolute), Y"), env)

    def visitAbsIndZ(self, node, env):
        self.assemble(node, Ops.modes.index("(Absolute), Z"), env)

    def visitZPIndirect(self, node, env):
        self.assemble(node, Ops.modes.index("(Zero Page)"), env)

    def visitIndirectX(self, node, env):
        self.assemble(node, Ops.modes.index("(Zero Page, X)"), env)

    def visitIndirectY(self, node, env):
        self.assemble(node, Ops.modes.index("(Zero Page), Y"), env)

    def visitIndirectZ(self, node, env):
        self.assemble(node, Ops.modes.index("(Zero Page), Z"), env)

    def visitIndirectSPY(self, node, env):
        self.assemble(node, Ops.modes.index("(Zero Page, SP), Y"), env)

    def visitRelative(self, node, env):
        self.assemble(node, Ops.modes.index("Relative"), env)

    def visitRelativeLong(self, node, env):
        self.assemble(node, Ops.modes.index("RelativeLong"), env)

    def visitZPRelative(self, node, env):
        self.assemble(node, Ops.modes.index("Zero Page, Relative"), env)

    def visitLabel(self, node, env):
        (label, val) = node.data
        location = val.value(env)
        self.mapper.mapLabel(label, str(node.ppt), location)

    def visitByte(self, node, env):
        created = []
        for expr in node.data:
            self.outputbyte(expr, env, created)
        self.registerData(created, env.getPC())
        env.incPC(len(node.data))
        self.data += len(node.data)

    def visitByteRange(self, node, env):
        offset = node.data[0].value(env) + 2
        length = node.data[1].value(env)
        if offset < 2:
            Err.log("Negative offset in .incbin")
        elif offset > len(node.data):
            Err.log("Offset extends past end of file")
        elif length < 0:
            Err.log("Negative length")
        elif offset + length > len(node.data):
            Err.log("File too small for .incbin subrange")
        else:
            created = []
            for expr in node.data[offset:(offset + length)]:
                self.outputbyte(expr, env, created)
            self.registerData(created, env.getPC())
            env.incPC(length)
            self.data += length

    def visitWord(self, node, env):
        created = []
        for expr in node.data:
            self.outputword(expr, env, created)
        self.registerData(created, env.getPC())
        env.incPC(len(node.data) * 2)
        self.data += len(node.data) * 2

    def visitDword(self, node, env):
        created = []
        for expr in node.data:
            self.outputdword(expr, env, created)
        self.registerData(created, env.getPC())
        env.incPC(len(node.data) * 4)
        self.data += len(node.data) * 4

    def visitWordBE(self, node, env):
        created = []
        for expr in node.data:
            self.outputword_be(expr, env, created)
        self.registerData(created, env.getPC())
        env.incPC(len(node.data) * 2)
        self.data += len(node.data) * 2

    def visitDwordBE(self, node, env):
        created = []
        for expr in node.data:
            self.outputdword_be(expr, env, created)
        self.registerData(created, env.getPC())
        env.incPC(len(node.data) * 4)
        self.data += len(node.data) * 4

    def visitSetPC(self, node, env):
        val = node.data[0].value(env)
        if self.writeOK and env.getPC() != val:
            self.listing.listDivider(val)
        env.setPC(val)

    def visitCheckPC(self, node, env):
        pc = env.getPC()
        target = node.data[0].value(env)
        if (pc > target):
            Err.log(".checkpc assertion failed: $%x > $%x" % (pc, target))

    def visitAdvance(self, node, env):
        pc = env.getPC()
        target = node.data[0].value(env)
        if (pc > target):
            Err.log("Attempted to .advance backwards: $%x to $%x" %
                    (pc, target))
        else:
            created = []
            for i in range(target - pc):
                self.outputbyte(node.data[1], env, created)
            self.filler += target - pc
            self.registerData(created, env.getPC())
        env.setPC(target)

    def registerData(self, vals, pc):
        self.listing.listData(vals, pc)
