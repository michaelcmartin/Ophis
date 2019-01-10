#!/usr/bin/env python3
import struct

x = bytes(list(range(256)))
bits = struct.unpack("32s32s32s32s32s32s32s32s", x)
norm = [4, 5, 6, 7, 0, 1, 2, 3]
ivrs = [4, 1, 0, 7, 6, 5, 2, 3]
blnk = [4, 3, 2, 7, 0, 1, 6, 5]
normmap = b''.join([bits[x] for x in norm])
ivrsmap = b''.join([bits[x] for x in ivrs])
blnkmap = b''.join([bits[x] for x in blnk])


def dumpfile(n, m):
    f = open(n, 'wb')
    f.write(m)
    f.close()


dumpfile('a2normal.map', normmap)
dumpfile('a2inverse.map', ivrsmap)
dumpfile('a2blink.map', blnkmap)
