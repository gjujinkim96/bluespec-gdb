import math
import re_extract as ree

class BasicData:
    def __init__(self, name, xml_name, total_bits, expand_bits):
        self.name = name
        self.xml_name = xml_name
        self.total_bits = total_bits
        self.expand_bits = expand_bits
        self.class_type = 'basic'

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"""{self.name}[{self.total_bits}:{self.expand_bits}]"""

    @classmethod
    def bit_data(cls, name):
        total_bits = ree.extract_bitsize_from_bitsharp(name)
        if total_bits <= 8:
            expand_bits = 8
        elif total_bits <= 16:
            expand_bits = 16
        elif total_bits <= 32:
            expand_bits = 32
        else:
            raise ValueError(f'Bit# over 32: {total_bits}')
            
        return cls(name, f'int{expand_bits}', total_bits, expand_bits)
        
class StructData:
    def __init__(self, name, elems, type_mapping):
        self.name = name
        self.xml_name = name
        self.elems = elems
        self.total_bits = sum([type_mapping[elem].total_bits for elem, elem_name in self.elems])
        self.expand_bits = sum([type_mapping[elem].expand_bits for elem, elem_name in self.elems])
        self.class_type = 'struct'

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"""{self.name}[{self.total_bits}:{self.expand_bits}]= {len(self.elems)}:{self.elems}"""

    @classmethod
    def maybe_data(cls, name, type_mapping):
        return cls(name, [('Bool', 'is_valid'), (ree.extract_inner_type_from_maybe(name), 'value')], type_mapping)

class EnumData:
    def __init__(self, name, values):
        self.name = name
        self.xml_name = name
        self.values = values
        self.total_bits = math.ceil(math.log2(len(self.values)))
        self.expand_bits = (len(self.values) + 256 - 1) // 256 * 8
        self.class_type = 'enum'

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"""{self.name}[{self.total_bits}:{self.expand_bits}]= {len(self.values)}:{self.values}"""

def default_mapping():
    return {
        'Instruction': BasicData('Instruction', 'int32', 32, 32),
        'Addr': BasicData('Addr', 'code_ptr', 32, 32),
        'code_ptr': BasicData('code_ptr', 'code_ptr', 32, 32),
        'Data': BasicData('Data', 'data_ptr', 32, 32),
        'data_ptr': BasicData('data_ptr', 'data_ptr', 32, 32),

        'Bool': BasicData('Bool', 'bool', 1, 8),
        'bool': BasicData('bool', 'bool', 1, 8),

        'int8': BasicData('int8', 'int8', 8, 8),
        'int16': BasicData('int16', 'int16', 16, 16),
        'int24': BasicData('int24', 'int24', 24, 24),
        'int32': BasicData('int32', 'int32', 32, 32),
        'uint8': BasicData('uint8', 'uint8', 8, 8),
        'uint16': BasicData('uint16', 'uint16', 16, 16),
        'uint24': BasicData('uint24', 'uint24', 24, 24),
        'uint32': BasicData('uint32', 'uint32', 32, 32),
        'Bit#(8)': BasicData.bit_data('Bit#(8)'),
        'Bit#(16)': BasicData.bit_data('Bit#(16)'),
        'Bit#(32)': BasicData.bit_data('Bit#(32)'),
    }
