import re

def shuck(data):
    pat = r'{([\s\S]*?)}\s+?(\S+)'
    results = re.search(pat, data)
    return results.group(1).strip(), results.group(2)

def process_raw_enum_from_source(source):
    pat = r'typedef\s*enum[\s\S]*?;'
    return re.findall(pat, source)

def process_raw_struct_from_source(source):
    pat = r'typedef\s*?struct\s*?{[\s\S]*?}[\s\S]*?;'
    return re.findall(pat, source)

def process_type_alias_from_source(source):    
    pat = r'typedef[\s\S]*?;'
    return re.findall(pat, source)
    
    
def process_struct_elements_from_shucked(shucked):
    pat = r'(\S+?)\s+?(\S+?)\s*?;'
    return re.findall(pat, shucked)

def process_enum_elements_from_shucked(shucked):
    pat = r'(\S+?)(?:\s*?=\s*?([\dobh\'a-fA-F]+?)\s*?)??(?:,|\s*?$)'
    return re.findall(pat, shucked)

def process_bitsize_and_name_from_type_alias(type_alias):
    pat = r'typedef\s+?Bit#\((\d+)\)\s+?(\S+);' # ignore void
    return re.findall(pat, type_alias) # [(bitsize, name), (bitsize, name)] 

def process_enum_elements_from_single_defs(raw):
    pat = r'(\S+?)\s*?(\S+?)\s*?=\s*?([\dobh\'a-fA-F]+?);'
    return re.findall(pat, raw) #[(type, enum_name, value), (type, enum_name, value)]

def process_maybes_from_structs(structs):
    pat = r'(Maybe#\((\S+?)\))'
    return re.findall(pat, structs)



def extract_data_type_from_raw(raw):
    pat = r'\s*?typedef\s*?(\w+)?\s*?{'
    data_type = re.match(pat, raw).group(1)

    if data_type not in ['enum', 'struct']:
        raise ValueError('unsupported data type')
    return data_type

def extract_bitsize_from_bitsharp(raw):
    pat = r'Bit#\((\S+)\)'
    return int(re.match(pat, raw).group(1))

def extract_inner_type_from_maybe(raw):
    pat = r'Maybe#\((\S+)\)'
    return re.match(pat, raw).group(1) 

def remove_multi_line_comments(raw):
    pat = r'/\*[\s\S]+?\*/'
    return re.sub(pat, '', raw)

def remove_single_line_comments(raw):
    pat = r'//[\s\S]*?(?=$|\n)'
    return re.sub(pat, '', raw)

def remove_imports(raw):
    pat = r'import [\s\S]*?;'
    return re.sub(pat, '', raw)

def remove_interface(raw):
    pat = r'interface[\s\S]*?endinterface'
    return re.sub(pat, '', raw)

def remove_function(raw):
    pat = r'function[\s\S]*?endfunction'
    return re.sub(pat, '', raw)

def remove_enums(raw):
    pat = r'typedef\s*enum[\s\S]*?;'
    return re.sub(pat, '', raw)

def remove_structs(raw):
    pat = r'typedef\s*?struct\s*?{[\s\S]*?}[\s\S]*?;'
    return re.sub(pat, '', raw)

def remove_type_alias(raw):    
    pat = r'typedef[\s\S]*?;'
    return re.sub(pat, '', raw)

def remove_simple_bit_constants(raw):
    pat = r'Bit#\(\d+?\)[\s\S]*?;'
    return re.sub(pat, '', raw)

def remove_unnecessary_newline(raw):
    pat = r'\s*\n'
    return re.sub(pat, '\n', raw)
