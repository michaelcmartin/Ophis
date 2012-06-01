#!/bin/bash

../bin/ophis -q --no-warn testbase.oph a.bin
diff -q testbase.bin a.bin
../bin/ophis -q --no-warn testdata.oph a.bin
diff -q testdata.bin a.bin
../bin/ophis -q --no-warn longbranch_ref.oph a_ref.bin
diff -q longbranch.bin a_ref.bin
../bin/ophis -q --no-warn longbranch.oph a.bin
diff -q longbranch.bin a.bin
../bin/ophis -cq --no-warn test65c02.oph a.bin
diff -q test65c02.bin a.bin
../bin/ophis -uq --no-warn test6510.oph a.bin
diff -q test6510.bin a.bin
../bin/ophis -cq --no-warn branch_c02_ref.oph a_ref.bin
diff -q branch_c02.bin a_ref.bin
../bin/ophis -cq --no-warn branch_c02.oph a.bin
diff -q branch_c02.bin a_ref.bin
rm -f a_ref.bin a.bin
