from pathlib import PurePosixPath

from ext4.inode import get_inode, FileType, parse_inode_mode
from ext4.cat import cat_by_blocks
from ext4.structures import parse_struct, ext4_dir_entry_2
from ext4.utils import say_when_last


def ls(buffer, sb, bg_descriptors, inode_no, recursively=False):
    """

    Args:
        buffer:
        sb:
        bg_descriptors:
        inode_no:

    Returns:
        List of tuples (dir_entry, entry_name, children_entries)
    """
    inode = get_inode(buffer, sb, bg_descriptors, inode_no)
    _, file_type = parse_inode_mode(inode.i_mode)
    if file_type != FileType.DIRECTORY:
        raise ValueError('inode {} should be directory (not {})'.format(inode_no, str(file_type)))
    data = b''.join(cat_by_blocks(buffer, sb, bg_descriptors, inode_no))
    offset = 0
    while offset < len(data):
        entry_part1_raw = data[offset:offset + 8]
        entry_part1 = parse_struct(ext4_dir_entry_2, entry_part1_raw)

        if entry_part1.inode != 0:
            name_raw = data[offset + 8:offset + 8 + entry_part1.name_len]
            name = name_raw.decode('utf-8')

            if recursively and entry_part1.file_type == 2:  # if directory
                if name != '.' and name != '..':
                    yield entry_part1, name, ls(buffer, sb, bg_descriptors, entry_part1.inode, True)
            else:
                yield entry_part1, name, []
        offset += entry_part1.rec_len


def path_to_inode(buffer, sb, bg_descriptors, path: PurePosixPath):
    if path == '/':
        return 2
    cwd_inode_no = 2
    cwd = '/'
    if path.root == '/':
        path = path.relative_to('/')

    for part in path.parts:
        for dir_entry_2, name, _ in ls(buffer, sb, bg_descriptors, cwd_inode_no):
            if name == part:
                cwd_inode_no = dir_entry_2.inode
                cwd = name
                break
        else:
            raise FileNotFoundError("Directory '{}' has no file '{}'".format(cwd, part))
    return cwd_inode_no


def ls_by_path(buffer, sb, bg_descriptors, path):
    inode_no = path_to_inode(buffer, sb, bg_descriptors, path)
    return ls(buffer, sb, bg_descriptors, inode_no)


def format_ls_output_by_lines(entries, is_layers_end=None):
    if not is_layers_end:
        is_layers_end = []
    for is_last, (dir_entry_2, name, children_entries) in say_when_last(entries):
        sep = '└' if is_last else '├'
        yield ''.join(
            '{}   '.format(' ' if is_layer_end else '│') for is_layer_end in is_layers_end) + '{}── {}'.format(sep,
                                                                                                               name)
        if children_entries:
            yield from format_ls_output_by_lines(children_entries, is_layers_end + [is_last])

