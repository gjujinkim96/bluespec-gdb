import types2xml
import re_extract as ree
import xml.etree.ElementTree as ET

def custom_xml_creator(base_xml, output_xml, type_mapping, debug_regs):
    print(f'Reading from base xml from {base_xml}..')    
    with open(base_xml) as f:
        xml = ''.join(f.readlines())


    xml = replace_with_types(xml, type_mapping)
    
    xml = replace_with_custom_regs(xml, type_mapping, debug_regs)

    with open(output_xml, 'w') as f:
        f.write(xml)

    print(f'Reading from modified xml to {output_xml}..')

def find_edges(cur, type_mapping, checks, edges):
    checks[cur] = True

    tp = type_mapping[cur]
    for elem, _ in tp.elems:
        if elem in checks:
            edges[elem].add(cur)

        if not checks.get(elem, True):
            find_edges(elem, type_mapping, checks, edges)

def dfs(cur, type_mapping, checks, touched, edges):
    checks[cur] = True
    
    for edge in edges[cur]:
        if not checks.get(edge, True):
            dfs(edge, type_mapping, checks, touched, edges)
    touched.append(cur)

def find_order(type_mapping):
    order = []
    checks = {}
    edges = {}
    for name, tp in type_mapping.items():
        if types2xml.xml_conversion_needed(tp, type_mapping):
            if tp.class_type == 'enum':
                order.append(name)
            else:
                checks[name] = False
                edges[name] = set()
    
    for name in checks:
        if not checks[name]:
            find_edges(name, type_mapping, checks, edges)
    touched = []
    for name in checks:
        checks[name] = False

    for name in checks:
        if not checks[name]:
            dfs(name, type_mapping, checks, touched, edges)
    
    touched.reverse()
    return order + touched
    

def replace_with_types(xml, type_mapping):
    order = find_order(type_mapping)
    # for ele in order:
    #     print(ele)
    # print()

    type_code = ''
    for name in order:
        tp = type_mapping[name]
        cur_lines = types2xml.make_xml(tp, type_mapping)
        cur_lines = '\n'.join([f'    {line}' for line in cur_lines.split('\n')])
        type_code += f'{cur_lines}\n\n'

    return ree.replace_type_xml(type_code, xml)

def replace_with_custom_regs(xml, type_mapping, debug_regs):
    regs_xml = ''
    is_first = True
    for gdb_name, bluespec_name, bluespec_type in debug_regs:
        attrib = {
            'name': gdb_name,
            'bitsize': '32',
            'type': type_mapping[bluespec_type].xml_name,
            'group': 'pipe',
        }

        if is_first:
            attrib['regnum'] = '0x51'

        root = ET.Element('reg', attrib=attrib)

        is_first = False

        reg_xml = ET.tostring(root, encoding='UTF-8').decode()
        regs_xml += f'    {reg_xml}\n'
        
    return ree.replace_custom_regs(regs_xml, xml)