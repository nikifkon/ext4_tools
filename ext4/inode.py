import struct
from enum import Enum
from typing import Tuple, NamedTuple, List
import time

from crc32c import crc32c

from ext4.core import Image
from ext4.structures import parse_struct, ext4_inode_struct
from ext4.utils import zero_range


def locate_inode(buffer, sb, bg_descriptors, inode_no: int) -> Tuple[int, int]:
    """
    Returns:
        Block group number and offset in inode table
    """
    bg_num = (inode_no - 1) // sb.s_inodes_per_group
    inode_table_idx = (inode_no - 1) % sb.s_inodes_per_group
    return bg_num, inode_table_idx


def get_inode(buffer, sb, bg_descriptors, inode_no: int) -> NamedTuple:
    if inode_no == 0:
        raise ValueError(
            "There is no inode 0 (proof: https://ext4.wiki.kernel.org/index.php/Ext4_Disk_Layout#Finding_an_Inode")
    s_block_size = 1024 << sb.s_log_block_size

    bg_num, inode_table_idx = locate_inode(buffer, sb, bg_descriptors, inode_no)

    buffer.seek(bg_num * sb.s_blocks_per_group * s_block_size)
    if bg_num == 0:
        buffer.seek(sb.s_first_data_block * s_block_size, 1)
    buffer.seek(s_block_size, 1)

    bg_desc = bg_descriptors[bg_num]
    bg_inode_table = (bg_desc.bg_inode_table_hi << struct.calcsize('L') * 8) + bg_desc.bg_inode_table_lo
    buffer.seek(bg_inode_table * s_block_size, 0)

    offset_in_inode_table = sb.s_inode_size * inode_table_idx
    buffer.seek(offset_in_inode_table, 1)

    inode_raw = buffer.read(0x80)
    inode = parse_struct(ext4_inode_struct, inode_raw)

    return inode


def format_inode_stat(inode, inode_number: int, leaf_extend_nodes: List = None) -> str:
    mode, filetype = parse_inode_mode(inode.i_mode)
    res = f'''Inode: {inode_number}   Type: {str(filetype)}    Mode:  {mode}   Flags: 0x{inode.i_flags:x}
User:  {inode.i_uid}   Group:  {inode.i_gid}   Size: {inode.i_size_lo}
ctime: 0x{inode.i_ctime:08x} -- {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(inode.i_ctime))}
atime: 0x{inode.i_atime:08x} -- {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(inode.i_atime))}
mtime: 0x{inode.i_mtime:08x} -- {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(inode.i_mtime))}
Inode checksum: 0x0000{inode.i_checksum_lo:x}
'''
    if leaf_extend_nodes:
        res += '{: <20}  {}\n'.format("Logical block", "Physical blocks")
        for node in leaf_extend_nodes:
            start = (node.ee_start_hi << 32) + node.ee_start_lo
            res += '{: <20}: {}\n'.format(f"{node.ee_block}-{node.ee_block + node.ee_len}",
                                          f"{start}-{start + node.ee_len}")
    return res


def parse_inode_mode(i_mode: int) -> Tuple[str, 'FileType']:
    """
    Args:
        i_mode: ext4_inode.i_mode (16 bytes number)
    Returns:
        A tuple `(mode, filetype)`, where `mode` is File mode in Numeric notation and filetype is enum `FileType`
    """
    right_part = i_mode & 0xfff
    left_part = i_mode >> 12

    mode = '{:04o}'.format(right_part)
    filetype = FileType(left_part)

    return mode, filetype


class FileType(Enum):
    FIFO = 0b1
    CHARACTER_DEVICE = 0b10
    DIRECTORY = 0b100
    BLOCK_DEVICE = 0b110
    REGULAR = 0b1000
    SYMBOLIC_LINK = 0b1010
    SOCKET = 0b1100

    def __str__(self) -> str:
        return self.name.lower().replace('_', ' ')

    def to_dir_entry_code(self) -> int:
        if self == FileType.DIRECTORY:
            return 0x2
        elif self == FileType.REGULAR:
            return 0x1
        elif self == FileType.CHARACTER_DEVICE:
            return 0x3
        elif self == FileType.BLOCK_DEVICE:
            return 0x4
        elif self == FileType.SYMBOLIC_LINK:
            return 0x7
        elif self == FileType.FIFO:
            return 0x5
        elif self == FileType.SOCKET:
            return 0x6


def calc_checksum(img: Image, inode_no: int, i_generation, raw, has_hi):
    inode_to_checksum = struct.pack('<16s', img.sb.s_uuid)
    inode_to_checksum += struct.pack('<L', inode_no)
    inode_to_checksum += struct.pack('<L', i_generation)
    inode_raw_zeros = zero_range(raw, 0x7c, 2)
    if has_hi:
        inode_raw_zeros = zero_range(inode_raw_zeros, 0x82, 2)
    inode_to_checksum += inode_raw_zeros
    return ~crc32c(inode_to_checksum) & (0xff_ff_ff_ff if has_hi else 0xff_ff)
