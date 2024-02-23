

def unpack(tp_name, type_mapping):
    tp = type_mapping[tp_name]
    if tp.class_type == 'constant':
        return unpack(tp.value, type_mapping)
    elif tp.class_type == 'basic':
        return [tp.total_bits], [tp.expand_bits]
    elif tp.class_type == 'enum':
        return [tp.total_bits], [tp.expand_bits]
    elif tp.class_type == 'struct':
        total_ret = []
        expand_ret = []

        for elem_type, _ in tp.elems:
            elem_total, elem_expand = unpack(elem_type, type_mapping)
            total_ret.extend(elem_total)
            expand_ret.extend(elem_expand)
        return total_ret, expand_ret
    else:
        raise ValueError(f'invalid type: {tp.class_type}')


def create_custom_reg_order_file(debug_regs, type_mapping, output_file):
    all_bits_info = [unpack(tp, type_mapping) for _, _, tp in debug_regs]

    ret = ''
    ret += f'{len(debug_regs)}\n'
    ret += f'{max([len(x[0]) for x in all_bits_info])}\n'
    for total_ret, expand_ret in all_bits_info:
        for ele in total_ret:
            ret += f'{ele} '
        ret += '\n'
        for ele in expand_ret:
            ret += f'{ele} '
        ret += '\n'

    with open(output_file, 'w') as f:
        f.write(ret)

    print(f'Write custom bit information to {output_file}..')
