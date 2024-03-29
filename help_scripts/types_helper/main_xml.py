import data_types as dt
import file_mapping as fm
import custom_regs as cr
import types2xml
import argparse

def main():
    parser = argparse.ArgumentParser(
                    description="Create 'type' to be used in target description in xml format")
    parser.add_argument('--filenames', help="bsc filenames separated by ','", required=True)
    parser.add_argument('--xml', help='xml file to parse custom regs', required=False)
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

    for name, tp in type_mapping.items():
        if types2xml.xml_conversion_needed(tp, type_mapping):
            print(types2xml.make_xml(tp, type_mapping))
            print()

if __name__ == '__main__':
    main()
