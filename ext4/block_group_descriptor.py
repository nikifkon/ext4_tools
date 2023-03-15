from struct import pack
from typing import NamedTuple

from crc32c import crc32c

from ext4.core import Image
from ext4.utils import get_block_size, merge_hi_lo


def calc_bitmap_checksum(img, bitmap_raw: bytes):
    return ~crc32c(pack('<16s', img.sb.s_uuid) + bitmap_raw) & 0xff_ff_ff_ff


def read_block_bitmap(img: Image, bg: NamedTuple) -> bytes:
    sb_block_size = get_block_size(img)
    block_bitmap_start = merge_hi_lo(bg.bg_block_bitmap_hi, bg.bg_block_bitmap_lo)
    block_bitmap_length = img.sb.s_blocks_per_group // 8
    img.buffer.seek(block_bitmap_start * sb_block_size)
    return img.buffer.read(block_bitmap_length)


def read_inode_bitmap(img: Image, bg: NamedTuple) -> bytes:
    sb_block_size = get_block_size(img)
    inode_bitmap_start = merge_hi_lo(bg.bg_inode_bitmap_hi, bg.bg_inode_bitmap_lo)
    inode_bitmap_length = img.sb.s_inodes_per_group // 8
    img.buffer.seek(inode_bitmap_start * sb_block_size)
    return img.buffer.read(inode_bitmap_length)


def locate_block_group_descriptor(img: Image, bg_no: int):
    sb_block_size = get_block_size(img)
    img.buffer.seek(sb_block_size)
    img.buffer.seek(img.sb.s_desc_size * bg_no, 1)

