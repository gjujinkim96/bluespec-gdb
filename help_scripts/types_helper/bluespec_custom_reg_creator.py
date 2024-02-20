import re
import argparse
import data_types as dt
import file_mapping as fm

def main():
    parser = argparse.ArgumentParser(
                    prog='main_xml',
                    # description="Create 'type' to be used in target description in xml format"
                    )
    parser.add_argument('--filenames', help="bsc filenames separated by ','", required=True)
    parser.add_argument('--debug_vars', help='xml file holding debug variables', required=True)
    args = parser.parse_args()

    type_mapping = dt.default_mapping()

    files = args.filenames.split(',')
    for file in files:
        with open(file) as f:
            lines = f.readlines()
        
        fm.update_type_mapping_from_bsc('\n'.join(lines), type_mapping)

    with open(args.debug_vars) as f:
        lines = f.readlines()

    raw_output = '\n'.join(lines)
    pat = r'<\s*?data\s*?gdb_name\s*?=\s*?"([\s\S]*?)"\s+?bluespec_name\s*?=\s*?"([\s\S]*?)"\s+?bluespec_type\s*?=\s*?"([\s\S]*?)">'
    entries = re.findall(pat, raw_output)

    for idx, (gdb_name, bluespec_name, bluespec_type) in enumerate(entries):
        if idx != 0:
            print('else ', end='')
        print(f'if (custom_reg_addr == {idx})')
        print(f'\tdata = zeroExtend(pack({bluespec_name}));')
    print('else begin')
    print(fr'\t$fwrite(stderr, "rl_debug_read_custom_reg: Invalid custom_reg %h found\\n", custom_reg_addr);')
    print('\t$finish(1);')
    print('end')  


if __name__ == '__main__':
    main()