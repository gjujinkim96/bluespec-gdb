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

default_mapping = dt.default_mapping()

def convert_single_defs(type_alias, raw_output, type_mapping):
    bitsize_and_names = ree.process_bitsize_and_name_from_type_alias('\n'.join(type_alias))
    type_alias_dict = {}
    for bitsize, name in bitsize_and_names:
        type_alias_dict[name] = {
            'bitsize': int(bitsize),
            'values': []
        }

    enum_elems = ree.process_enum_elements_from_single_defs(raw_output)
    for tp, enum_name, value in enum_elems:
        type_alias_dict[tp]['values'].append((enum_name, value))

    result = {}
    for type_name, type_dict in type_alias_dict.items():
        if len(type_dict['values']) == 0:
            if type_dict['bitsize'] <= 8:
                using_bitsize = 8
            elif type_dict['bitsize'] <= 16:
                using_bitsize = 16
            elif type_dict['bitsize'] <= 32:
                using_bitsize = 32
            else:
                raise ValueError()
            
            if type_name in default_mapping:
                result[type_name] = dt.BasicData(type_name, f'int{using_bitsize}', type_dict['bitsize'], using_bitsize)
            else:
                result[type_name] = dt.StructData(type_name, [(f'int{using_bitsize}', 'value')], type_mapping)
        else:
            result[type_name] = dt.EnumData(type_name, type_dict['values'])
    return result
