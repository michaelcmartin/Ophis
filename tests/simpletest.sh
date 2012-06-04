#!/bin/bash

../bin/ophis -q --no-warn testbase.oph
diff -q testbase.bin ophis.bin
../bin/ophis -q --no-warn testdata.oph
diff -q testdata.bin ophis.bin
../bin/ophis -q --no-warn longbranch_ref.oph -o a_ref.bin
diff -q longbranch.bin a_ref.bin
../bin/ophis -q --no-warn longbranch.oph
diff -q longbranch.bin ophis.bin
../bin/ophis -cq --no-warn test65c02.oph
diff -q test65c02.bin ophis.bin
../bin/ophis -uq --no-warn test6510.oph
diff -q test6510.bin ophis.bin
../bin/ophis -cq --no-warn branch_c02_ref.oph -o a_ref.bin
diff -q branch_c02.bin a_ref.bin
../bin/ophis -cq --no-warn branch_c02.oph
diff -q branch_c02.bin ophis.bin
rm -f a_ref.bin ophis.bin
