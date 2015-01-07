"Hi Stella" is a simple "Hello World" program for the "Stella" chip,
more famously known as the Atari 2600. Simply running

ophis hi_stella.oph

should produce hi_stella.bin, a 256-byte file that prints "HI" on
the screen with some rolling color bars.

A more sophisticated program is colortest, which lets the user
explore the 128 colors provided by the system. Use up and down
to move the color value by 2, and left and right to move it
by 16. (The lowest bit in the color value byte is ignored, for
a total of 128 colors available.)
