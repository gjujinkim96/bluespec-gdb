import data_types as dt
import file_mapping as fm
import custom_regs as cr
import types2xml
import argparse

def unpack(tp_name, type_mapping):
    tp = type_mapping[tp_name]
    if tp.class_type == 'basic':
        return [tp.total_bits], [tp.expand_bits]
    elif tp.class_type == 'enum':
        return [tp.total_bits], [tp.expand_bits]
    elif tp.class_type == 'struct':
        total_ret = []
        expand_ret = []
        for elem_type, _ in tp.elems:
            elem_total, elem_expand = unpack(elem_type, type_mapping)
            total_ret.extend(elem_total)
            expand_ret.extend(elem_expand)
        return total_ret, expand_ret
    else:
        raise ValueError(f'invalid type: {tp.class_type}')

def main():
    parser = argparse.ArgumentParser(
                    prog='main_xml',
                    description="Create raw bits and expanded bits for regs")
    parser.add_argument('--filenames', help="bsc filenames separated by ','", required=True)
    parser.add_argument('--xml', help='xml file to parse custom regs', required=True)
    args = parser.parse_args()

    type_mapping = dt.default_mapping()

    files = args.filenames.split(',')
    for file in files:
        with open(file) as f:
            lines = f.readlines()
        
        fm.update_type_mapping_from_bsc('\n'.join(lines), type_mapping)

    if args.xml is not None:
        with open(args.xml) as f:
            lines = f.readlines()
    
        custom_regs = cr.extract_custom_regs_from_xml('\n'.join(lines))
        cr.update_type_mapping_from_custom_regs(custom_regs, type_mapping)   

    all_bits_info = [unpack(custom_reg.type, type_mapping) for custom_reg in custom_regs]

    print(len(custom_regs))
    print(max([len(x[0]) for x in all_bits_info]))
    for total_ret, expand_ret in all_bits_info:
        for ele in total_ret:
            print(ele, end=' ')
        print()
        for ele in expand_ret:
            print(ele, end=' ')
        print()

if __name__ == '__main__':
    main()
