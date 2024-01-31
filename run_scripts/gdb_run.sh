#!/bin/bash

cd /build/CA_Summer_Project/lab4/gdbstub/Run
cat /build/CA_Summer_Project/lab4/lib/common-lib/ProcTypes.bsv \
    /build/CA_Summer_Project/lab4/src/PipelineStructs.bsv | python3.9 types2xml.py > given_def.xml
sed -e '/<!-- Sed replace given_def.xml here. -->/{r given_def.xml' -e 'd}' base.xml > custom.xml
riscv64-unknown-elf-gdb -x start.gdb
