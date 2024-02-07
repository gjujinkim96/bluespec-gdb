import xml.etree.ElementTree as ET
import converter as cv

def xml_conversion_needed(tp):
    handler = {
        'struct': True,
        'enum': True,
        'basic': False,
    }

    return handler[tp.class_type]

def make_struct_xml(tp, type_mapping):
    root = ET.Element('struct', attrib={'id': tp.name})
    
    for element in tp.elems:
        if element[0] in type_mapping:
            field_type = type_mapping[element[0]]
        else:
            raise ValueError(f'type not found: {element[0]}')
            
        attr = {
            'name': element[1],
            'type': field_type.xml_name
        }
        
        ET.SubElement(root, 'field', attrib=attr)
    
    ET.indent(root)
    xml = ET.tostring(root, encoding='UTF-8').decode()
    
    return xml

def make_enum_xml(tp, type_mapping):
    root = ET.Element('enum', attrib={'id': tp.name, 'size': str(tp.expand_bits//8)})

    given_index = 0
    comment_needed = False
    for element, raw_num in tp.values:
        if raw_num:
            given_index = cv.convert_num(raw_num)
            comment_needed = True

        attr = {
            'name': element,
            'value': str(given_index)
        }

        child = ET.SubElement(root, 'evalue', attrib=attr)
        
        given_index += 1

    ET.indent(root)

    xml_without_comments = ET.tostring(root, encoding='UTF-8').decode()

    if comment_needed:
        lines = xml_without_comments.split('\n')
        max_len = max([len(lines[1+idx]) for idx, (element, raw_num) in enumerate(tp.values) if raw_num])
        
        for idx, (element, raw_num) in enumerate(tp.values):
            if raw_num:
                comment = ET.Comment(f' from: {raw_num} ')
                space_rep = max_len - len(lines[1+idx]) + 4
                lines[1 + idx] = f'{lines[1 + idx]}{space_rep * " "}{ET.tostring(comment, encoding="UTF-8").decode()}'
        xml = '\n'.join(lines)
    else:
        xml = xml_without_comments

    return xml

def make_xml(tp, type_mapping):
    handler = {
        'struct': make_struct_xml,
        'enum': make_enum_xml
    }

    return handler[tp.class_type](tp, type_mapping)
