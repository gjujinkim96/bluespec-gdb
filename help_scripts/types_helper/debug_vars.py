import re_extract as ree
import data_types as dt

def split_operation(gdb_name, bluespec_name, type, type_mapping, ret):
    type = type_mapping[type]
    if type.class_type == 'constant':
        split_operation(gdb_name, bluespec_name, type.value, type_mapping, ret)
    elif type.depth <= 1:
        ret.append((gdb_name, bluespec_name, type.name))
    else:
        if type.is_maybe:
            split_operation(f'{gdb_name}.valid', f'isValid({bluespec_name})', type.elems[0][0], type_mapping, ret)
            split_operation(f'{gdb_name}.', f'{bluespec_name}.Valid', type.elems[1][0], type_mapping, ret)
        else:
            for elem_type, elem_name in type.elems:
                split_operation(f'{gdb_name}.{elem_name}', f'{bluespec_name}.{elem_name}', elem_type, type_mapping, ret)
    

def get_debug_vars(file, type_mapping):
    with open(file) as f:
        lines = f.readlines()
    print(f'Reading custom register information from {file}..')

    raw_output = '\n'.join(lines)
    raw_output = ree.remove_xml_comments(raw_output)
    entries = ree.process_debug_vars(raw_output)
    for gdb_name, bluespec_name, bluespec_type in entries:
        if bluespec_type not in type_mapping:
            type_mapping[bluespec_type] = dt.create_missing_type(bluespec_type, type_mapping)
    
    splited = []
    for gdb_name, bluespec_name, bluespec_type in entries:
        split_operation(gdb_name, bluespec_name, bluespec_type, type_mapping, splited)

    for gdb_name, bluespec_name, bluespec_type in splited:
        if bluespec_type not in type_mapping:
            type_mapping[bluespec_type] = dt.create_missing_type(bluespec_type, type_mapping)

    return splited

