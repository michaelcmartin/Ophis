"""The Ophis Assembler passes

    Ophis's design philosophy is to build the IR once, then run a great
    many assembler passes over the result.  Thus, each pass does a
    single, specialized job.  When strung together, the full
    translation occurs.  This structure also makes the assembler
    very extensible; additional analyses or optimizations may be
    added as new subclasses of Pass."""
    
# Copyright 2002-2012 Michael C. Martin and additional contributors.
# You may use, modify, and distribute this file under the MIT
# license: See README for details.

import Ophis.Errors as Err
import Ophis.IR as IR
import Ophis.Opcodes as Ops
import Ophis.CmdLine as Cmd
import Ophis.Macro as Macro

# The passes themselves

class Pass:
    """Superclass for all assembler passes.  Automatically handles IR
    types that modify the environent's structure, and by default
    raises an error on anything else.  Override visitUnknown in your
    extension pass to produce a pass that accepts everything."""
    name = "Default Pass"
    def __init__(self):
        self.writeOK = 1
    def visitNone(self, node, env):
        pass
    def visitSEQUENCE(self, node, env):
        Err.currentpoint = node.ppt
        for n in node.data:
            n.accept(self, env)
    def visitDataSegment(self, node, env):
        self.writeOK = 0
        env.setsegment(node.data[0])
    def visitTextSegment(self, node, env):
        self.writeOK = 1
        env.setsegment(node.data[0])
    def visitScopeBegin(self, node, env):
        env.newscope()
    def visitScopeEnd(self, node, env):
        env.endscope()
    def visitUnknown(self, node, env):
        Err.log("Internal error!  "+self.name+" cannot understand node type "+node.nodetype)
    def prePass(self):
        pass
    def postPass(self):
        pass
    def go(self, node, env):
        """Prepares the environment and runs this pass, possibly 
        printing debugging information."""
        if Err.count == 0:
            if Cmd.verbose > 1: print "Running: "+self.name
            env.reset()
            self.prePass()
            node.accept(self, env)
            self.postPass()
            env.reset()
            if Cmd.verbose > 3:
                print "Current labels:"
                print env
            if Cmd.verbose > 2: 
                print "Current IR:"
                print node

class FixPoint:
    """A specialized class that is not a pass but can be run like one.
    This class takes a list of passes and a "fixpoint" function."""
    def __init__(self, name, passes, fixpoint):
        self.name = name
        self.passes = passes
        self.fixpoint = fixpoint
    def go(self, node, env):
        """Runs this FixPoint's passes, in order, until the fixpoint
        is true.  Always runs the passes at least once."""
        for i in xrange(100):
            if Err.count != 0: break
            for p in self.passes:
                p.go(node, env)
            if Err.count != 0: break
            if self.fixpoint(): break 
            if Cmd.verbose > 1: print "Fixpoint failed, looping back"
        else:
            Err.log("Can't make %s converge!  Maybe there's a recursive dependency somewhere?" % self.name)

class DefineMacros(Pass):
    "Extract macro definitions and remove them from the IR"
    name = "Macro definition pass"
    def prePass(self):
        self.inDef = 0
        self.nestedError = 0
    def postPass(self):
        if self.inDef:
            Err.log("Unmatched .macro")
        elif Cmd.verbose > 2:
            print "Macro definitions:"
            Macro.dump()
    def visitMacroBegin(self, node, env):
        if self.inDef:
            Err.log("Nested macro definition")
            self.nestedError = 1
        else:
            Macro.newMacro(node.data[0])
            node.nodetype = "None"
            node.data = []
            self.inDef = 1
    def visitMacroEnd(self, node, env):
        if self.inDef:
            Macro.endMacro()
            node.nodetype = "None"
            node.data = []
            self.inDef = 0
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
        self.changed = 0
    def visitMacroInvoke(self, node, env):
        replacement = Macro.expandMacro(node.ppt, node.data[0], node.data[1:])
        node.nodetype = replacement.nodetype
        node.data = replacement.data
        self.changed = 1
    def visitUnknown(self, node, env):
        pass

class InitLabels(Pass):
    "Finds all reachable labels"
    name = "Label initialization pass"
    def __init__(self):
        Pass.__init__(self)
        self.labelmap = {}
    def prePass(self):
        self.changed = 0
        self.PCvalid = 1
    def visitAdvance(self, node, env):
        self.PCvalid=node.data[0].valid(env, self.PCvalid)
    def visitSetPC(self, node, env):
        self.PCvalid=node.data[0].valid(env, self.PCvalid)
    def visitLabel(self, node, env):
        (label, val) = node.data
        fulllabel = "%d:%s" % (env.stack[0], label)
        if fulllabel in self.labelmap and self.labelmap[fulllabel] is not node: 
            Err.log("Duplicate label definition '%s'" % label)
        if fulllabel not in self.labelmap:
            self.labelmap[fulllabel] = node
        if val.valid(env, self.PCvalid) and label not in env:
            env[label]=0
            self.changed=1
    def visitUnknown(self, node, env):
        pass

class CircularityCheck(Pass):
    "Checks for circular label dependencies"
    name = "Circularity check pass"
    def prePass(self):
        self.changed=0
        self.PCvalid=1
    def visitAdvance(self, node, env):
        PCvalid = self.PCvalid
        self.PCvalid=node.data[0].valid(env, self.PCvalid)
        if not node.data[0].valid(env, PCvalid):
            Err.log("Undefined or circular reference on .advance")
    def visitSetPC(self, node, env):
        PCvalid = self.PCvalid
        self.PCvalid=node.data[0].valid(env, self.PCvalid)
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
        for i in [x for x in node.data if isinstance(x, IR.Expr)]:
            i.value(env)  # Throw away result, just confirm validity of all expressions

class EasyModes(Pass):
    "Assigns address modes to hardcoded and branch instructions"
    name = "Easy addressing modes pass"
    def visitMemory(self, node, env):
        if Ops.opcodes[node.data[0]][14] is not None:
            node.nodetype = "Relative"
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
    def visitUnknown(self, node, env):
        pass

class UpdateLabels(Pass):
    "Computes the new values for all entries in the symbol table"
    name = "Label Update Pass"
    def prePass(self):
        self.changed = 0
    def visitSetPC(self, node, env): env.setPC(node.data[0].value(env))
    def visitAdvance(self, node, env): env.setPC(node.data[0].value(env))
    def visitImplied(self, node, env): env.incPC(1)
    def visitImmediate(self, node, env): env.incPC(2)
    def visitIndirectX(self, node, env): env.incPC(2)
    def visitIndirectY(self, node, env): env.incPC(2)
    def visitZPIndirect(self, node, env): env.incPC(2)
    def visitZeroPage(self, node, env): env.incPC(2)
    def visitZeroPageX(self, node, env): env.incPC(2)
    def visitZeroPageY(self, node, env): env.incPC(2)
    def visitRelative(self, node, env): env.incPC(2)
    def visitIndirect(self, node, env): env.incPC(3)
    def visitAbsolute(self, node, env): env.incPC(3)
    def visitAbsoluteX(self, node, env): env.incPC(3)
    def visitAbsoluteY(self, node, env): env.incPC(3)
    def visitAbsIndX(self, node, env): env.incPC(3)
    def visitAbsIndY(self, node, env): env.incPC(3)
    def visitMemory(self, node, env): env.incPC(3)
    def visitMemoryX(self, node, env): env.incPC(3)
    def visitMemoryY(self, node, env): env.incPC(3)
    def visitPointer(self, node, env): env.incPC(3)
    def visitPointerX(self, node, env): env.incPC(3)
    def visitPointerY(self, node, env): env.incPC(3)
    def visitCheckPC(self, node, env): pass
    def visitLabel(self, node, env):
        (label, val) = node.data
        old = env[label]
        env[label] = val.value(env)
        if old != env[label]:
            self.changed = 1
    def visitByte(self, node, env): env.incPC(len(node.data))
    def visitWord(self, node, env): env.incPC(len(node.data)*2)
    def visitDword(self, node, env): env.incPC(len(node.data)*4)
    def visitWordBE(self, node, env): env.incPC(len(node.data)*2)
    def visitDwordBE(self, node, env): env.incPC(len(node.data)*4)

class Collapse(Pass):
    """Selects as many zero-page instructions to convert as 
    possible, and tracks how many instructions have been 
    converted this pass."""
    name = "Instruction Collapse Pass"
    def prePass(self):
        self.collapsed = 0
    def visitMemory(self, node, env):
        if collapse_no_index(node, env): self.collapsed += 1
    def visitMemoryX(self, node, env):
        if collapse_x(node, env): self.collapsed += 1
    def visitMemoryY(self, node, env):
        if collapse_y(node, env): self.collapsed += 1
    def visitPointer(self, node, env):
        if collapse_no_index_ind(node, env): self.collapsed += 1
    def visitPointerX(self, node, env):
        if collapse_x_ind(node, env): self.collapsed += 1
    def visitPointerY(self, node, env):
        if collapse_y_ind(node, env): self.collapsed += 1
    def visitUnknown(self, node, env):
        pass

def collapse_no_index(node, env):
    """Transforms a Memory node into a ZeroPage one if possible.
    Returns 1 if it made the collapse, false otherwise."""
    if node.data[1].value(env) < 0x100 and Ops.opcodes[node.data[0]][2] is not None:
        node.nodetype = "ZeroPage"
        return 1
    else:
        return 0

def collapse_x(node, env):
    """Transforms a MemoryX node into a ZeroPageX one if possible.
    Returns 1 if it made the collapse, false otherwise."""
    if node.data[1].value(env) < 0x100 and Ops.opcodes[node.data[0]][3] is not None:
        node.nodetype = "ZeroPageX"
        return 1
    else:
        return 0

def collapse_y(node, env):
    """Transforms a MemoryY node into a ZeroPageY one if possible.
    Returns 1 if it made the collapse, false otherwise."""
    if node.data[1].value(env) < 0x100 and Ops.opcodes[node.data[0]][4] is not None:
        node.nodetype = "ZeroPageY"
        return 1
    else:
        return 0

def collapse_no_index_ind(node, env):
    """Transforms a Pointer node into a ZPIndirect one if possible.
    Returns 1 if it made the collapse, false otherwise."""
    if node.data[1].value(env) < 0x100 and Ops.opcodes[node.data[0]][11] is not None:
        node.nodetype = "ZPIndirect"
        return 1
    else:
        return 0

def collapse_x_ind(node, env):
    """Transforms a PointerX node into an IndirectX one if possible.
    Returns 1 if it made the collapse, false otherwise."""
    if node.data[1].value(env) < 0x100 and Ops.opcodes[node.data[0]][12] is not None:
        node.nodetype = "IndirectX"
        return 1
    else:
        return 0

def collapse_y_ind(node, env):
    """Transforms a PointerY node into an IndirectY one if possible.
    Returns 1 if it made the collapse, false otherwise."""
    if node.data[1].value(env) < 0x100 and Ops.opcodes[node.data[0]][13] is not None:
        node.nodetype = "IndirectY"
        return 1
    else:
        return 0


class NormalizeModes(Pass):
    """Eliminates the intermediate "Memory" and "Pointer" nodes,
    converting them to "Absolute"."""
    name = "Mode Normalization pass"
    def visitMemory(self, node, env): node.nodetype = "Absolute"
    def visitMemoryX(self, node, env): node.nodetype = "AbsoluteX"
    def visitMemoryY(self, node, env): node.nodetype = "AbsoluteY"
    def visitPointer(self, node, env): node.nodetype = "Indirect"
    def visitPointerX(self, node, env): node.nodetype = "AbsIndX"
    # If we ever hit a PointerY by this point, we have a bug.
    def visitPointerY(self, node, env): node.nodetype = "AbsIndY"
    def visitUnknown(self, node, env): pass

class Assembler(Pass):
    """Converts the IR into a list of bytes, suitable for writing to 
    a file."""
    name = "Assembler"

    def prePass(self):
        self.output = []
        self.code = 0
        self.data = 0
        self.filler = 0

    def postPass(self):
        if Cmd.verbose > 0 and Err.count == 0:
            print "Assembly complete: %s bytes output (%s code, %s data, %s filler)" \
                % (len(self.output), self.code, self.data, self.filler)

    def outputbyte(self, expr, env):
        'Outputs a byte, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x00 or val > 0xff:
                Err.log("Byte constant "+str(expr)+" out of range")
                val = 0
            self.output.append(int(val))
        else:
            Err.log("Attempt to write to data segment")
    def outputword(self, expr, env):
        'Outputs a little-endian word, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x0000 or val > 0xFFFF:
                Err.log("Word constant "+str(expr)+" out of range")
                val = 0
            self.output.append(int(val & 0xFF))
            self.output.append(int((val >> 8) & 0xFF))
        else:
            Err.log("Attempt to write to data segment")
    def outputdword(self, expr, env):
        'Outputs a little-endian dword, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x00000000 or val > 0xFFFFFFFFL:
                Err.log("DWord constant "+str(expr)+" out of range")
                val = 0
            self.output.append(int(val & 0xFF))
            self.output.append(int((val >> 8) & 0xFF))
            self.output.append(int((val >> 16) & 0xFF))
            self.output.append(int((val >> 24) & 0xFF))
        else:
            Err.log("Attempt to write to data segment")

    def outputword_be(self, expr, env):
        'Outputs a big-endian word, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x0000 or val > 0xFFFF:
                Err.log("Word constant "+str(expr)+" out of range")
                val = 0
            self.output.append(int((val >> 8) & 0xFF))
            self.output.append(int(val & 0xFF))
        else:
            Err.log("Attempt to write to data segment")
    def outputdword_be(self, expr, env):
        'Outputs a big-endian dword, with range checking'
        if self.writeOK:
            val = expr.value(env)
            if val < 0x00000000 or val > 0xFFFFFFFFL:
                Err.log("DWord constant "+str(expr)+" out of range")
                val = 0
            self.output.append(int((val >> 24) & 0xFF))
            self.output.append(int((val >> 16) & 0xFF))
            self.output.append(int((val >> 8) & 0xFF))
            self.output.append(int(val & 0xFF))
        else:
            Err.log("Attempt to write to data segment")

    def assemble(self, node, mode, env):
        "A generic instruction called by the visitor methods themselves"
        (opcode, expr) = node.data
        bin_op = Ops.opcodes[opcode][mode]
        if bin_op is None:
            Err.log('%s does not have mode "%s"' % (opcode.upper(), Ops.modes[mode]))
            return
        self.outputbyte(IR.ConstantExpr(bin_op), env)
        arglen = Ops.lengths[mode]
        if mode == 14:  # Special handling for relative mode
            arg = expr.value(env)
            arg = arg-(env.getPC()+2)
            if arg < -128 or arg > 127:
                Err.log("Branch target out of bounds")
                arg = 0
            if arg < 0: arg += 256
            expr = IR.ConstantExpr(arg)
        if arglen == 1: self.outputbyte(expr, env)
        if arglen == 2: self.outputword(expr, env)
        env.incPC(1+arglen)
        self.code += 1+arglen

    def visitImplied(self, node, env):    self.assemble(node,  0, env)
    def visitImmediate(self, node, env):  self.assemble(node,  1, env)
    def visitZeroPage(self, node, env):   self.assemble(node,  2, env)
    def visitZeroPageX(self, node, env):  self.assemble(node,  3, env)
    def visitZeroPageY(self, node, env):  self.assemble(node,  4, env)
    def visitAbsolute(self, node, env):   self.assemble(node,  5, env)
    def visitAbsoluteX(self, node, env):  self.assemble(node,  6, env)
    def visitAbsoluteY(self, node, env):  self.assemble(node,  7, env)
    def visitIndirect(self, node, env):   self.assemble(node,  8, env)
    def visitAbsIndX(self, node, env):    self.assemble(node,  9, env)
    def visitAbsIndY(self, node, env):    self.assemble(node, 10, env)
    def visitZPIndirect(self, node, env): self.assemble(node, 11, env)
    def visitIndirectX(self, node, env):  self.assemble(node, 12, env)
    def visitIndirectY(self, node, env):  self.assemble(node, 13, env)
    def visitRelative(self, node, env):   self.assemble(node, 14, env)
    def visitLabel(self, node, env): pass
    def visitByte(self, node, env):
        for expr in node.data:
            self.outputbyte(expr, env)
        env.incPC(len(node.data))
        self.data += len(node.data)
    def visitWord(self, node, env):
        for expr in node.data:
            self.outputword(expr, env)
        env.incPC(len(node.data)*2)
        self.data += len(node.data)*2
    def visitDword(self, node, env):
        for expr in node.data:
            self.outputdword(expr, env)
        env.incPC(len(node.data)*4)
        self.data += len(node.data)*4
    def visitWordBE(self, node, env):
        for expr in node.data:
            self.outputword_be(expr, env)
        env.incPC(len(node.data)*2)
        self.data += len(node.data)*2
    def visitDwordBE(self, node, env):
        for expr in node.data:
            self.outputdword_be(expr, env)
        env.incPC(len(node.data)*4)
        self.data += len(node.data)*4
    def visitSetPC(self, node, env): 
        env.setPC(node.data[0].value(env))
    def visitCheckPC(self, node, env):
        pc = env.getPC()
        target = node.data[0].value(env)
        if (pc > target):
            Err.log(".checkpc assertion failed: $%x > $%x" % (pc, target))
    def visitAdvance(self, node, env): 
        pc = env.getPC()
        target = node.data[0].value(env)
        if (pc > target):
            Err.log("Attempted to .advance backwards: $%x to $%x" % (pc, target))
        else:
            zero = IR.ConstantExpr(0)
            for i in xrange(target-pc): self.outputbyte(zero, env)
            self.filler += target-pc
        env.setPC(target)
