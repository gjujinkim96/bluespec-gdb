import re
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
                    prog='main_xml',
                    # description="Create 'type' to be used in target description in xml format"
                    )
    parser.add_argument('--proc', help="Proc bsc file", required=True)
    parser.add_argument('--custom_reg_code', help='custom_reg code for debugging', required=True)
    args = parser.parse_args()

    with open(args.proc) as f:
        lines = f.readlines()
    proc_file = ''.join(lines)

    with open(args.custom_reg_code) as f:
        lines = f.readlines()
    custom_code = ''.join(lines)



    pat = r'(// Sed Custom Reg Replacment START // DO NOT MODIFY)([\s\S]*?)(// Sed Custom Reg Replacment END // DO NOT MODIFY)'
    print(re.sub(pat, rf'\1\n{custom_code}\n\3', proc_file))

if __name__ == '__main__':
    main()
