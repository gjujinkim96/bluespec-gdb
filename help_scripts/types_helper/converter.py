import re_extract as ree
import data_types as dt

def convert_num(num):
    ret = -1
    if "'" in num or '’' in num:
        split_char_found = False
        for c, base in zip('hobd', [16, 8, 2, 10]):
            if c in num:
                split_char_found = True
                break

        if not split_char_found:
            raise ValueError(f'invalid int format: {num}')

        ret = int(num.split(c)[1].replace('_', ''), base)
    else:
        ret = int(num)
    return ret

def convert_struct(data, type_mapping):
    raw_element, name = ree.shuck(data)
    elements = ree.process_struct_elements_from_shucked(raw_element)
    return dt.StructData(name, elements, type_mapping)

def convert_enum(data, type_mapping):
    raw_element, name = ree.shuck(data)
    elements = ree.process_enum_elements_from_shucked(raw_element)
    return dt.EnumData(name, elements)

def convert(data, type_mapping):
    data_type = ree.extract_data_type_from_raw(data)
    if data_type == 'enum':
        return convert_enum(data, type_mapping)
    elif data_type == 'struct':
        return convert_struct(data, type_mapping)
    else:
        raise ValueError()

'''

type_alias examples
typedef Bit#(5) RIndx;

typedef Bit#(7) Opcode;

single def examples
Opcode opLoad    = 7'b0000011;
Opcode opMiscMem = 7'b0001111;
Opcode opOpImm   = 7'b0010011;



'''
def convert_single_defs(type_alias, raw_output, type_mapping):
    types = ree.process_def_and_new_type_from_type_alias('\n'.join(type_alias))

    common_bit_types = {}

    for old_type, new_type in types:
        if old_type == 'void':
            continue

        if ree.check_is_common_bit_type(old_type):
            common_bit_types[new_type] = {
                'old_type': old_type,
                'values': [],
                'bitsize': ree.extract_bitsize_from_common_bit_type(old_type)
            }
        else:
            try:
                constant = int(old_type)
            except ValueError:
                constant = old_type
            type_mapping[new_type] =  dt.Constant(new_type, constant, type_mapping)

    enum_elems = ree.process_enum_elements_from_single_defs(raw_output)
    for type, enum_name, value in enum_elems:
        common_bit_types[type]['values'].append((enum_name, value))


    for type_name, type_dict in common_bit_types.items():
        if (len(type_dict['values']) == 0):
            if type_dict['old_type'].startswith('Maybe'):
                type_datum = dt.StructData.maybe_data(type_dict['old_type'], type_mapping)
            else:
                type_datum = dt.BasicData.common_bit_data(type_dict['old_type'], type_mapping)  
        else:
            type_datum = dt.EnumData(type_name, type_dict['values'], total_bits=type_dict['bitsize'])
        type_mapping[type_name] = type_datum

