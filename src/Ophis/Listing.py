"""The Ophis program lister

    When displaying an assembled binary for human inspection, it is
    traditional to mix binary with reconstructed instructions that
    have all arguments precomputed. This class manages that."""

# Copyright 2002-2014 Michael C. Martin and additional contributors.
# You may use, modify, and distribute this file under the MIT
# license: See README for details.

import sys


class Listing(object):
    """Encapsulates the program listing. Accepts fully formatted
    instruction strings, or batches of data bytes. Batches of data
    bytes are assumed to be contiguous unless a divider is explicitly
    requested."""

    def __init__(self, fname):
        self.listing = [(0, [])]
        self.filename = fname

    def listInstruction(self, inst):
        "Add a preformatted instruction list to the listing."
        self.listing.append(inst)

    def listDivider(self, newpc):
        "Indicate that the next data block will begin at the given PC."
        self.listing.append((newpc, []))

    def listData(self, vals, pc):
        """Add a batch of data to the listing. If this starts a new
        batch of data, begin that batch at the listed PC."""
        if type(self.listing[-1]) is not tuple:
            self.listing.append((pc, []))
        self.listing[-1][1].extend(vals)

    def dump(self):
        openfiles = []
        filelines = {}
        prevline = None
        prevfile = None
        prevrow = None
        if self.filename == "-":
            out = sys.stdout
        else:
            out = open(self.filename, "wt")
        for x in self.listing:
            if type(x) is str:
                print(x, file=out)
            elif type(x) is list:
                prevrow = None
                curline = x[0].split('->')[0]
                curfile, curln = curline.split(':')
                curln = int(curln)
                if not curfile in openfiles:
                    openfiles.append(curfile)
                    with open(curfile, 'rt') as f:
                        filelines['curfile'] = f.read().splitlines()
                if not prevfile == curfile:
                    prevfile = curfile  
                    print("Source file: %s" % curfile, file=out)
                srcline = filelines['curfile'][curln - 1].strip()
                if prevline == curline:
                    print("%-32s" % (x[1]), file=out)
                else:
                    prevline = curline
                    print("%-32s %5d  %s" % (x[1], curln, srcline), file=out)
            elif type(x) is tuple:
                prevline = None
                i = 0
                pc = x[0]
                dupestring = None
                prevrow = None
                while True:
                    row = x[1][i:i + 16]
                    if row == []:
                        break
                    if prevrow == row:
                        i += 16
                        if not dupestring:
                            dupestring = "   . . ."
                            print(dupestring, file=out)
                        continue
                    else:
                        dupestring = None
                        prevrow = row
                    dataline = " %04X " % (pc + i)
                    dataline += (" %02X" * len(row)) % tuple(row)
                    charline = ""
                    for c in row:
                        if c < 32 or c > 126:
                            charline += "."
                        else:
                            charline += chr(c)
                    print("%-54s  |%-16s|" % (dataline, charline), file=out)
                    i += 16
        if self.filename != "-":
            out.close()


class NullLister(object):
    "A dummy Lister that actually does nothing."
    def listInstruction(self, inst):
        pass

    def listDivider(self, newpc):
        pass

    def listData(self, vals, pc):
        pass

    def dump(self):
        pass


class LabelMapper(object):
    """Encapsulates the label map. Accepts label names, string
    representations of program points, and the location."""
    def __init__(self, fname):
        self.labeldata = []
        self.filename = fname

    def mapLabel(self, label, ppt, location):
        if label.startswith("_"):
            try:
                macroarg = int(label[1:], 10)
                # If that didn't throw, this is a macro argument
                # and we don't want to track it.
                return
            except ValueError:
                pass
            if label.startswith("_*"):
                # This is the caller side of the macro arguments,
                # and we don't want to track that either.
                return
        if label.startswith("*"):
            # Unprocess anonymous labels
            label = "*"
        shortlocs = []
        # Filenames tend to become absolute paths for better
        # error processing, but that's a disaster in these
        # charts. We split out the leafs here and then re-join
        # the macro application arrows.
        for loc in ppt.split('->'):
            shortloc = loc.split('/')[-1]
            shortloc = shortloc.split('\\')[-1]
            shortlocs.append(shortloc)
        self.labeldata.append((location, label, '->'.join(shortlocs)))

    def dump(self):
        if self.filename == "-":
            out = sys.stdout
        else:
            out = open(self.filename, "wt")
        maxlabellen = 0
        self.labeldata.sort()
        for (loc, label, srcloc) in self.labeldata:
            if len(label) > maxlabellen:
                maxlabellen = len(label)
        formatstr = "$%%04X | %%-%ds | %%s\n" % (maxlabellen)
        for l in self.labeldata:
            out.write(formatstr % l)
        if self.filename != "-":
            out.close()


class NullLabelMapper(object):
    "A dummy LabelMapper that actually does nothing."
    def mapLabel(self, label, ppt, location):
        pass

    def dump(self):
        pass
