#!/bin/bash

function show_help_and_exit() {
    echo "Usage:"
    echo "    $0 program_list"
    echo "program list = [array_sum_1d, array_sum_ij, array_sum_ji]"
    echo "               [hanoi_tower, bubble_sort, fibonacci]"
    exit 1
}

program="$1"
if [ -z "$program" ]; then
    show_help_and_exit
fi

program_lists=("array_sum_1d" "array_sum_ij" "array_sum_ji" "hanoi_tower" "bubble_sort" "fibonacci")
found=0
for item in "${program_lists[@]}";do
    if [ "$item" = "$program" ]; then
        found=1
        break
    fi
done

if [ "$found" = "0" ]; then
    echo found invalid program "'$program'"
    show_help_and_exit
fi

echo $program > .running_program.txt

cd /build/CA_Summer_Project/pb_lab6/lab6-1/src/
rm -f gdb/unix_socket/*
./risc-v -p $program
