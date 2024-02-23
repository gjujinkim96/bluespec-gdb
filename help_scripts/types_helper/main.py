from file_mapping import get_type_mapping_from_files
from debug_vars import get_debug_vars
from custom_reg_bsv_maker import replace_custom_reg_code
from custom_regs_order_maker import create_custom_reg_order_file
from xml_creator import custom_xml_creator
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filenames', help="files containing bsc type definition separated by ','", required=True)
    parser.add_argument('--debug_vars', help='xml file with debugging registers to show', required=True)
    parser.add_argument('--proc', help='proc.bsv to add auto-generated code', required=True)
    parser.add_argument('--reg_order', help='output file to write about custom register bit information', required=True)
    parser.add_argument('--base_xml', help='base xml file containing general registers', required=True)
    parser.add_argument('--output_xml', help='output xml file containing all registers', required=True)
    
    args = parser.parse_args()

    files = args.filenames.split(',')
    type_mapping = get_type_mapping_from_files(files)
    splited_debug_regs = get_debug_vars(args.debug_vars, type_mapping)


    replace_custom_reg_code(splited_debug_regs, args.proc)
    create_custom_reg_order_file(splited_debug_regs, type_mapping, args.reg_order)

    custom_xml_creator(args.base_xml, args.output_xml, type_mapping, splited_debug_regs)
    
if __name__ == '__main__':
    main()
