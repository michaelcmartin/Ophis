This directory holds files likely to be of use to you in developing your own
programs. The contents of each file is summarized below.


c64_0.oph:     A Commodore 64 equivalent to a modern compiler's "crt0.s" - it
               contains a .PRG file header, a short BASIC program that launches
               the machine language program, and a prologue and epilogue that
               prepare memory for your use and then clean it up again when you
               are done. Memory locations $02 through $8F on the zero page are
               available for your use, and the program lives at the beginning
               a contiguous block of RAM from $0800 through $CFFF. The BASIC
               ROM is swapped out of memory (leaving $A000-$BFFF as RAM) for
               the duration of your program. BASIC's working storage on the
               zero page is backed up in the RAM underneath the KERNAL ROM
               while your program runs.

c64kernal.oph: A collection of standard aliases for the KERNAL routines on the
               Commodore 64. Names for these routines have been chosen to match
               the Commodore 64 Programmer's Reference Guide. Additional useful
               constants are defined for the character codes for color changes
               and case-changing.

libbasic64.oph:A still-experimental set of macros and routines for exploiting
               the software floating point routines in the Commodore 64
               BASIC ROM.

c64header.oph: A much simpler Commodore 64 header that does nothing but jump
               directly to your code. Useful for small programs or those that
               intend to interface with BASIC.

vic20.oph:     A simple header for the unexpanded VIC-20. Equivalent in
               behavior to c64header.oph.

vic20x.oph:    A simple header like the two above, but for expanded VIC-20.

nes.oph:       A somewhat skeletal collection of aliases for the PPU registers
               on the Nintendo Entertainment System. These names were chosen
               to match the constant names given on the NESdev Wiki.

stella.oph:    A collection of aliases for the registers of the Atari 2600.
               These names were taken from the "Stella Programmer's Guide" and
               are in wide use amongst developers and code analysts alike.
