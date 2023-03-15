from pathlib import PurePosixPath
from struct import pack

from ext4.cat import cat_by_blocks
from ext4.core import Image
from ext4.inode import get_inode, locate_inode
from ext4.ls import path_to_inode, ls as ls_by_inode
from ext4.structures import get_struct_format, ext4_dir_entry_2
from ext4.utils import get_value_from_bitmap, set_value_in_bitmap


def cat(buffer, sb, bg_descriptors, path: PurePosixPath) -> bytes:
    inode_no = path_to_inode(buffer, sb, bg_descriptors, path)
    return b''.join(cat_by_blocks(buffer, sb, bg_descriptors, inode_no))


def ls(buffer, sb, bg_descriptors, path: PurePosixPath, recursively=False):
    inode_no = path_to_inode(buffer, sb, bg_descriptors, path)
    return ls_by_inode(buffer, sb, bg_descriptors, inode_no, recursively)


def stat(buffer, sb, bg_descriptors, path: PurePosixPath):
    inode_no = path_to_inode(buffer, sb, bg_descriptors, path)
    inode = get_inode(buffer, sb, bg_descriptors, inode_no)
    return inode, inode_no


def occupy_block_if_free(img: Image, block_no: int) -> bool:
    sb_block_size = 1024 << img.sb.s_log_block_size
    bg_no = block_no // img.sb.s_blocks_per_group
    bg = img.bg_descriptors[bg_no]
    bitmap_blk_no = (bg.bg_block_bitmap_hi << 32) + bg.bg_block_bitmap_lo
    img.buffer.seek(bitmap_blk_no * sb_block_size)

    bitmap = img.buffer.read(sb_block_size)
    offset = block_no % img.sb.s_blocks_per_group
    if get_value_from_bitmap(bitmap, offset):
        img.buffer.seek(-sb_block_size, 1)
        set_value_in_bitmap(img.buffer, offset, True)
        return True
    return False


def free_inode(img: Image, inode_no: int) -> bool:
    sb_block_size = 1024 << img.sb.s_log_block_size
    bg_no, idx = locate_inode(*img, inode_no)
    # TODO checksums!!!
    bg = img.bg_descriptors[bg_no]
    bitmap_blk_no = (bg.bg_inode_bitmap_hi << 32) + bg.bg_inode_bitmap_lo
    img.buffer.seek(bitmap_blk_no * sb_block_size)
    bitmap_raw = img.buffer.read(sb_block_size)
    img.buffer.seek(-sb_block_size, 1)
    set_value_in_bitmap(img.buffer, idx, False)
    # TODO set new checksum
    # new_cs = calc_bitmap_checksum(img, bitmap_raw)
    # locate_block_group_descriptor(img, bg_no)
    # img.buffer.seek(0x1A, 1)
    # img.buffer.write(pack('<H', new_cs & 0xffff))
    # img.buffer.seek(4, 1)
    # img.buffer.write(pack('<L', new_cs >> 32))
    # locate_block_group_descriptor(img, bg_no)
    # new_bg = parse_struct(block_group_descriptor_struct, img.buffer.read(img.sb.s_desc_size))
    # img.bg_descriptors[bg_no] = new_bg



def update_file(img: Image, inode_no: int, offset: int, data: bytes):
    sb_block_size = (1024 << img.sb.s_log_block_size)
    left = 0
    for _ in cat_by_blocks(*img, inode_no):
        offset -= sb_block_size
        if offset < 0:
            img.buffer.seek(offset, 1)
            img.buffer.write(data[left:min(-offset, len(data))])
            left = -offset
        if left >= len(data):
            return


def unlink(img: Image, path: PurePosixPath):
    if path.name == '' and path.parent == PurePosixPath('/'):
        raise ValueError("Can't unlink root directory!")
    offset = 0

    prev_dir_entry = None
    prev_name = None
    for dir_entry_2, name, _ in ls(*img, path.parent):
        if name == path.name:
            offset -= prev_dir_entry.rec_len

            format = get_struct_format(ext4_dir_entry_2)
            overall_length = prev_dir_entry.rec_len + dir_entry_2.rec_len
            data = pack(format, prev_dir_entry.inode, overall_length,
                        prev_dir_entry.name_len, prev_dir_entry.file_type)
            data += prev_name.encode('utf-8')
            data += b'\x00' * (overall_length - len(data))
            break
        offset += dir_entry_2.rec_len
        prev_dir_entry = dir_entry_2
        prev_name = name
    else:
        raise FileNotFoundError(f"File {path.name} not found in directory {path.parent}")
    dir_inode = path_to_inode(*img, path.parent)
    update_file(img, dir_inode, offset, data)
