import math
import re_extract as ree
from functools import cached_property

def calculate_expand_bits(total_bits):
    if total_bits <= 8:
        expand_bits = 8
    elif total_bits <= 16:
        expand_bits = 16
    elif total_bits <= 32:
        expand_bits = 32
    else:
        raise ValueError(f'Bit size over 32: {total_bits}')
    return expand_bits

def total_bits_to_int(total_bits, type_mapping=None):
    original = total_bits
    while True:
        try:
            total_bits = int(total_bits)
            return total_bits
        except ValueError:
            if type_mapping is None:
                raise ValueError(f'Type {original} is unknown')
            
            followed_type = type_mapping[total_bits]
            if followed_type.class_type != 'constant':
                raise ValueError(f'Type {original} is unknown')
            
            if followed_type.value == total_bits:
                raise ValueError(f'Type {original} is unknown')
            total_bits = followed_type.value

def get_total_bits_from_type(type, type_mapping):
    found = type_mapping[type]
    if found.class_type == 'constant':
        return get_total_bits_from_type(found.value, type_mapping)
    return found.total_bits

def get_expand_bits_from_type(type, type_mapping):
    found = type_mapping[type]
    if found.class_type == 'constant':
        return get_expand_bits_from_type(found.value, type_mapping)
    return found.expand_bits

def create_missing_type(missing, type_mapping):
    if ree.check_is_common_bit_type(missing):
        if missing.startswith('Maybe'):
            ret = StructData.maybe_data(missing, type_mapping)
        else:
            ret = BasicData.common_bit_data(missing, type_mapping)
    else:
        raise ValueError(f'Invalid type found when creating missing type: {missing}')
    return ret

class Constant:
    def __init__(self, name, value, type_mapping):
        self.name = name
        self.value = value
        self.class_type = 'constant'
        
        self.type_mapping = type_mapping

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"""{self.name}={self.value}"""
    
    @cached_property
    def depth(self):
        return self.type_mapping[self.value].depth

class BasicData:
    def __init__(self, name, xml_name, total_bits, expand_bits):
        self.name = name
        self.xml_name = xml_name
        self.total_bits = total_bits
        self.expand_bits = expand_bits
        self.class_type = 'basic'
        self.depth = 1

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"""{self.name}[{self.total_bits}:{self.expand_bits}]"""
    
    def to_dict(self):
        ret = {
            'name': self.name,
            'xml_name': self.xml_name,
            'total_bits': self.total_bits,
            'expand_bits': self.expand_bits,
            'class_type': self.class_type
        }
        return ret
    
    @classmethod
    def from_dict(cls, dict):
        return cls(dict['name'], dict['xml_name'], dict['total_bits'], dict['expand_bits'])
    
    @classmethod
    def common_bit_data(cls, name, type_mapping=None):
        if name.startswith('Bit'):
            xml_default = 'int'
        elif name.startswith('Int'):
            xml_default = 'int'
        elif name.startswith('UInt'):
            xml_default = 'uint'
        else:
            raise ValueError("Unsupported common bit data. only support bit, int, uint.. ", name)

        total_bits = ree.extract_bitsize_from_common_bit_type(name)

        original = total_bits
        while True:
            try:
                total_bits = int(total_bits)
                break
            except ValueError:
                if type_mapping is None:
                    raise ValueError(f'Type {original} is unknown')
                
                followed_type = type_mapping[total_bits]
                if followed_type.class_type != 'constant':
                    raise ValueError(f'Type {original} is unknown')
                
                if followed_type.value == total_bits:
                    raise ValueError(f'Type {original} is unknown')
                total_bits = followed_type.value

        expand_bits = calculate_expand_bits(total_bits)
        return cls(name, f'{xml_default}{expand_bits}', total_bits, expand_bits)
        
class StructData:
    def __init__(self, name, elems, type_mapping, is_maybe=False):
        self.name = name
        self.xml_name = name
        self.elems = elems

        self.type_mapping = type_mapping

        self.class_type = 'struct'
        self.is_maybe = is_maybe

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"""{self.name}[{self.total_bits}:{self.expand_bits}]= {len(self.elems)}:{self.elems}"""

    @classmethod
    def maybe_data(cls, name, type_mapping):
        return cls(name, [('Bool', 'valid'), (ree.extract_inner_type_from_maybe(name), '')], type_mapping, is_maybe=True)
    
    @cached_property
    def total_bits(self):
        return sum([get_total_bits_from_type(elem, self.type_mapping) for elem, _ in self.elems])
    
    @cached_property
    def expand_bits(self):
        return sum([get_expand_bits_from_type(elem, self.type_mapping) for elem, _ in self.elems])
    
    @cached_property
    def depth(self):
        return (not self.is_maybe) + max([self.type_mapping[elem_type].depth for elem_type, _ in self.elems])
    
    def update_missing(self):
        ret = {}
        for elem_type, elem_name in self.elems:
            if elem_type not in self.type_mapping:
                ret[elem_type] = create_missing_type(elem_type, self.type_mapping)
        return ret
    
class EnumData:
    def __init__(self, name, values, total_bits=None, type_mapping=None):
        self.name = name
        self.xml_name = name
        self.values = values
        self.depth = 1

        if total_bits is None:
            total_bits = math.ceil(math.log2(len(self.values)))
        else:
            total_bits = total_bits_to_int(total_bits, type_mapping)

        self.total_bits = total_bits
        self.expand_bits = calculate_expand_bits(self.total_bits)
        self.class_type = 'enum'

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"""{self.name}[{self.total_bits}:{self.expand_bits}]= {len(self.values)}:{self.values}"""
    
    # def to_dict(self):
    #     ret = {
    #         'name': self.name,
    #         'xml_name': self.xml_name,
    #         'total_bits': self.total_bits,
    #         'expand_bits': self.expand_bits,
    #         'class_type': self.class_type,
    #         'values': self.values
    #     }
    #     return ret
    
    # @classmethod
    # def from_dict(cls, dict):
    #     return cls(dict['name'], dict['xml_name'], dict['total_bits'], dict['expand_bits'])

def default_mapping():
    return {
        'Bool': BasicData('Bool', 'bool', 1, 8),
    }

def update_missing_struct_elements(type_mapping):
    missing_types = {}
    for k, v in type_mapping.items():
        if v.class_type == 'struct':
            missing_types.update(v.update_missing())
    type_mapping.update(missing_types)
