#!/bin/bash

cd /build/CA_Summer_Project/lab4/gdbstub/Run
python3.9 types_helper/main_xml.py \
    --filenames /build/CA_Summer_Project/lab4/lib/common-lib/ProcTypes.bsv,/build/CA_Summer_Project/lab4/src/PipelineStructs.bsv \
    --xml /build/CA_Summer_Project/lab4/gdbstub/Run/base.xml > given_def.xml

python3.9 types_helper/main_regs_order.py \
    --filenames /build/CA_Summer_Project/lab4/lib/common-lib/ProcTypes.bsv,/build/CA_Summer_Project/lab4/src/PipelineStructs.bsv \
    --xml /build/CA_Summer_Project/lab4/gdbstub/Run/base.xml > /build/CA_Summer_Project/lab4/gdbstub/regs_bits.txt

sed -e '/<!-- Sed replace given_def.xml here. -->/{r given_def.xml' -e 'd}' base.xml > custom.xml

cd /build/CA_Summer_Project/lab4/src/
./risc-v -p array_sum_1d
