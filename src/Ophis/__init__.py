"Ophis - a cross-assembler for the 6502 series of chips"

# Copyright 2002-2024 Michael C. Martin and additional contributors.
# You may use, modify, and distribute this file under the MIT
# license: See README for details.

import sys
import Ophis.Main

def ophis_argv():
    sys.exit(Ophis.Main.run_ophis(sys.argv[1:]))
