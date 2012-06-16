#!/usr/bin/python
import struct

x = ''.join([chr(x) for x in range(256)])
bits = struct.unpack("32s32s32s32s32s32s32s32s", x)
norm = [4, 5, 6, 7, 0, 1, 2, 3]
ivrs = [4, 1, 0, 7, 6, 5, 2, 3]
blnk = [4, 3, 2, 7, 0, 1, 6, 5]
normmap = ''.join([bits[x] for x in norm])
ivrsmap = ''.join([bits[x] for x in ivrs])
blnkmap = ''.join([bits[x] for x in blnk])


def dumpfile(n, m):
    f = file(n, 'wb')
    f.write(m)
    f.close()


dumpfile('a2normal.map', normmap)
dumpfile('a2inverse.map', ivrsmap)
dumpfile('a2blink.map', blnkmap)
