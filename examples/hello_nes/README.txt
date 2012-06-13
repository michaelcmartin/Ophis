This is a "Hello World" program for the Nintendo Entertainment System,
which uses the sprite system to display and color-cycle the letters.

Since NES cartridges tended to have sophisticated circuitry built into them
that controlled memory addressing, several standards have arisen to represent
this information. The program code for "Hello, NES" is split into two halves;
a hello_prg.oph containing the executable code (PRG-ROM), and a hello_chr.oph
containing the graphics tile information (CHR-ROM). These can then be packaged
one of two ways - the popular iNES format (hello_ines.oph) or the
mostly-defunct UNIF format (hello_unif.oph). Simply running

ophis hello_ines.oph

or

ophis hello_unif.oph

should produce hello.nes and hello.unf, respectively. Although UNIF is not a
common format, its "chunk" system is not rare. The hello_unif.oph file
demonstrates some techniques for automatically computing chunk sizes in Ophis.

Be warned that as these techniques use the program counter, attempting to use
labels to compute chunk size of assembled code is likely to backfire
spectacularly - this technique should really only be used for inline strings
and data.

