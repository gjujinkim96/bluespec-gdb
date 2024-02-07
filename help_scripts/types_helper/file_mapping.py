import re_extract as ree
import data_types as dt
import converter as cv

def update_type_mapping_from_bsc(file, type_mapping):
    cleanings = [ree.remove_multi_line_comments, ree.remove_single_line_comments, ree.remove_imports, \
                 ree.remove_interface, ree.remove_function]
    
    output = file
    for clean in cleanings:
        output = clean(output)
    
    processings = [ree.process_raw_enum_from_source, ree.process_raw_struct_from_source, ree.process_type_alias_from_source]
    removings = [ree.remove_enums, ree.remove_structs, ree.remove_type_alias]
    
    pr_results = []
    for pr, rm in zip(processings, removings):
        pr_results.append(pr(output))
        output = rm(output)    
    
    raw_enums, raw_structs, raw_type_alias = pr_results
    
    extra_cleanings = [ree.remove_simple_bit_constants, ree.remove_unnecessary_newline]
    for clean in extra_cleanings:
        output = clean(output)
    
    single_defs_result = cv.convert_single_defs(raw_type_alias, output, type_mapping)
    type_mapping.update(single_defs_result)
    
    for raw in raw_enums:
        conv = cv.convert(raw, type_mapping)
        type_mapping[conv.name] = conv
    
    all_maybes = set(ree.process_maybes_from_structs('\n'.join(raw_structs)))
    for type_name, inner_type in all_maybes:
        type_mapping[type_name] = dt.StructData.maybe_data(type_name, type_mapping)
    
    for raw in raw_structs:
        conv = cv.convert(raw, type_mapping)
        type_mapping[conv.name] = conv
    