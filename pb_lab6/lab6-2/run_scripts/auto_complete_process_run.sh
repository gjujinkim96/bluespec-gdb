#!/bin/bash

function list_programs() {
	COMPREPLY=($(compgen -W "array_sum_1d array_sum_ij array_sum_ji hanoi_tower bubble_sort fibonacci" "${COMP_WORDS[$COMP_CWORD]}"))    
}

complete -F list_programs process_run.sh
