import re_extract as ree

def make_custom_reg_bsv(debug_regs):
    ret = ''

    for idx, (gdb_name, bluespec_name, bluespec_type) in enumerate(debug_regs):
        # print(bluespec_name, bluespec_type)
        # if bluespec_name.startswith('Maybe#('):

        if idx != 0:
            ret += '  else '
        else:
            ret += '  '
        ret += f'if (custom_reg_addr == {idx})\n'
        ret += f'    data = zeroExtend(pack({bluespec_name}));\n'
    ret += '  else begin\n'
    ret += f'    $fwrite(stderr, "rl_debug_read_custom_reg: Invalid custom_reg %h found\\\\n", custom_reg_addr);\n'
    ret += '    $finish(1);\n'
    ret += '  end\n'  
    return ret

def replace_custom_reg_code(debug_regs, proc):
    code = make_custom_reg_bsv(debug_regs)

    with open(proc) as f:
        lines = f.readlines()
    proc_file = ''.join(lines)

    mod_code = ree.replace_bsv_code(code, proc_file)

    with open(proc, 'w') as f:
        f.write(mod_code)

    print(f'Added code to read custom registers in {proc}..')
    