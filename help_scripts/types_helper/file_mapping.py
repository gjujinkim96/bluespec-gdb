import re_extract as ree
import data_types as dt
import converter as cv

def get_type_mapping_from_files(files):
    type_mapping = dt.default_mapping()

    for file in files:
        with open(file) as f:
            lines = f.readlines()
        
        update_type_mapping_from_bsc('\n'.join(lines), type_mapping)
        print(f'Reading bluespec type information from {file}..')

    return type_mapping

def update_type_mapping_from_bsc(file, type_mapping):
    cleanings = [ree.remove_multi_line_comments, ree.remove_single_line_comments, ree.remove_imports, \
                 ree.remove_module, ree.remove_rule, ree.remove_interface, ree.remove_function]
    
    output = file
    for clean in cleanings:
        output = clean(output)
    
    processings = [
        (ree.process_raw_enum_from_source, ree.remove_enums),
        (ree.process_raw_struct_from_source, ree.remove_structs),
        (ree.process_type_alias_from_source, ree.remove_type_alias)
    ]
    
    pr_results = []
    for pr, rm in processings:
        pr_results.append(pr(output))
        output = rm(output)    
    
    raw_enums, raw_structs, raw_type_alias = pr_results
    
    extra_cleanings = [ree.remove_simple_bit_constants, ree.remove_unnecessary_newline]
    for clean in extra_cleanings:
        output = clean(output)

    cv.convert_single_defs(raw_type_alias, output, type_mapping)
    
    for raw in raw_enums:
        conv = cv.convert_enum(raw, type_mapping)
        type_mapping[conv.name] = conv
    
    for raw in raw_structs:
        conv = cv.convert(raw, type_mapping)
        type_mapping[conv.name] = conv

    dt.update_missing_struct_elements(type_mapping)
    # for k, v in type_mapping.items():
    #     print(k)
    #     print(v)
    #     print()
