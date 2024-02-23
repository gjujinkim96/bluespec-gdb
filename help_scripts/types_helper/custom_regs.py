from dataclasses import dataclass
import re
import data_types as dt



@dataclass
class CustomReg:
    name: str
    type: str
    reg_group: str
    num: str

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'{self.name}: {self.type}'
    
def select_parsing_part_from_raw(raw):
    pat = r'<!-- parsing start -->([\s\S]*?)<!-- parsing end -->'
    return re.search(pat, raw).group(0)
    
def remove_xml_comments_from_raw(raw):
    pat = r'<!--[\s\S]+?-->'
    return re.sub(pat, '', raw)

def process_custom_regs_from_raw(raw):
    pat = r'<reg\s+?name\s*?=\s*?"([\s\S]*?)"\s+?bitsize\s*?=\s*?"\S+?"\s+?type\s*?=\s*?"(\S+?)"\s+?group\s*?=\s*?"(\S+?)"(?:\s+?regnum\s*?=\s*?"(\S+?)"\s*?)?\s*?/>'
    return re.findall(pat, raw)

def check_type_maybe(tp):
    pat = r'Maybe#\(\S+\)'
    return re.match(pat, tp) is not None

def extract_custom_regs_from_xml(xml):
    output = xml
    output = select_parsing_part_from_raw(output)
    output = remove_xml_comments_from_raw(output)
    raw_custom_regs = process_custom_regs_from_raw(output)

    return [CustomReg(*raw_reg) for raw_reg in raw_custom_regs]

def update_type_mapping_from_custom_regs(custom_regs, type_mapping):
    for custom_reg in custom_regs:
        if not custom_reg.type in type_mapping:
            if check_type_maybe(custom_reg.type):
                new_data = dt.StructData.maybe_data(custom_reg.type, type_mapping)
                type_mapping[new_data.name] = new_data
            else:
                raise ValueError(f'{custom_reg.type} not found')
            