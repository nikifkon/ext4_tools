from pathlib import PurePosixPath
from struct import pack

from ext4.core import Image
from ext4.inode import parse_inode_mode, FileType, get_inode
from ext4.ls import path_to_inode, ls
from ext4.rm import rm
from ext4.structures import get_struct_format, ext4_dir_entry_2
from ext4.tools import stat, update_file, unlink


def mv(img: Image, source: PurePosixPath, dest: PurePosixPath):
    if not img.buffer.writable():
        raise ValueError("Image must be writable!")

    source_inode_no = path_to_inode(*img, source)
    source_inode = get_inode(*img, source_inode_no)
    _, file_type = parse_inode_mode(source_inode.i_mode)

    dest_directory = None
    dest_directory_inode = None
    dest_name = None

    try:
        inode, inode_no = stat(*img, dest)
        mode, filetype = parse_inode_mode(inode.i_mode)
        if filetype == FileType.DIRECTORY:
            dest_directory = dest
            dest_name = source.name
            dest_directory_inode = inode_no
        elif filetype == FileType.REGULAR:
            dest_directory = dest.parent
            dest_name = dest.name
            dest_directory_inode = path_to_inode(*img, dest_directory)
            rm(img, dest)
        else:
            raise ValueError("Can't move to: {}!".format(filetype))
    except FileNotFoundError:
        inode, inode_no = stat(*img, dest.parent)  # may raise FileNotFoundError, don't care
        dest_directory = dest.parent
        dest_name = dest.name
        dest_directory_inode = inode_no

    dest_name_raw = dest_name.encode('utf-8')
    if len(dest_name_raw) > 255:
        raise ValueError('File name too long (max: 255 bytes)')

    unlink(img, source)

    dir_entry = pack(get_struct_format(ext4_dir_entry_2), source_inode_no, len(dest_name_raw) + 8,
                     len(dest_name_raw),
                     file_type.to_dir_entry_code()) + dest_name_raw
    if try_insert_into_space(img, dir_entry, dest_directory_inode):
        return
    # if try_append_to_end(img, dir_entry, dest_directory_inode):
    #     return
    # block space is over, need to allocate new block
    # if try_allocate_block_continiously(img, dest_directory_inode):
    #     return
    # next block is in use or max extent.ee_len reached, need to allocate new extent
    # if try_append_extent(img, dest_directory_inode):
    #     return
    # no space in extent block, need to change extent tree.
    raise NotImplementedError('Not enough space to move file')


def try_insert_into_space(img: Image, dir_entry: bytes, dest_directory_inode: int):
    size = len(dir_entry)
    offset = 0
    data = b''

    for dir_entry_2, name, _ in ls(*img, dest_directory_inode):
        entry_size = dir_entry_2.rec_len
        space = entry_size - (8 + dir_entry_2.name_len)
        if space > size:
            format = get_struct_format(ext4_dir_entry_2)
            data += pack(format, dir_entry_2.inode, entry_size - space, dir_entry_2.name_len,
                         dir_entry_2.file_type)
            data += name.encode('utf-8')
            dir_entry = dir_entry[:4] + pack('<H', space) + dir_entry[6:]
            data += dir_entry
            break
        offset += entry_size
    else:
        return False
    update_file(img, dest_directory_inode, offset, data)
    return True


# def try_append_to_end(img: Image, dir_entry: bytes, dest_directory_inode: int):
#     size = len(dir_entry)
#     sb_block_size = (1024 << img.sb.s_log_block_size)
#     for block in cat_by_blocks(*img, dest_directory_inode):
#         if len(block) % sb_block_size < (sb_block_size - size):
#             pass
#         next_blk_no = img.buffer.tell() // sb_block_size + (1 if len(block) != sb_block_size else 0)
#         with brb(img.buffer):
#             if occupy_block_if_free(img, next_blk_no):
#                 return True
#     return False
