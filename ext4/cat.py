from typing import List, Iterator

from ext4.inode import get_inode, parse_inode_mode
from ext4.structures import ext4_extent_header_struct, parse_struct, ext4_extent_struct, ext4_extent_idx_struct


def cat_by_blocks(buffer, sb, bg_descriptors, inode_no: int) -> Iterator[bytes]:
    """

    Args:
        inode_no: Inode number

    Returns:
        Iterator over inode blocks

    Notes:
        - only extents (no indirect)
        - no inline_data
    """
    sb_block_size = (1024 << sb.s_log_block_size)
    inode = get_inode(buffer, sb, bg_descriptors, inode_no)
    _, filetype = parse_inode_mode(inode.i_mode)
    if filetype.SYMBOLIC_LINK and inode.i_flags == 0x10000000:
        yield inode.i_block[:inode.i_size_lo]
        return

    extents = travers_extent_tree(buffer, inode.i_block, sb_block_size)

    to_read_bytes = inode.i_size_lo
    for extent in extents:
        phys_block_no = (extent.ee_start_hi << 32) + extent.ee_start_lo
        buffer.seek(phys_block_no * sb_block_size)
        new_content = buffer.read(sb_block_size * extent.ee_len)
        to_read_bytes -= sb_block_size * extent.ee_len
        if to_read_bytes < 0:
            yield new_content[:to_read_bytes + sb_block_size * extent.ee_len]
        else:
            yield new_content


def travers_extent_tree(buffer, i_block: bytes, sb_block_size=4096) -> List:
    extent_header = parse_struct(ext4_extent_header_struct, i_block[:12])

    if extent_header.eh_magic != bytes.fromhex('0A F3'):
        return []

    extents = []
    for entry_idx in range(extent_header.eh_entries):
        if extent_header.eh_depth == 0:
            extents.append(
                parse_struct(ext4_extent_struct, i_block[12 * (entry_idx + 1):12 * (entry_idx + 2)])
            )
        else:
            idx = parse_struct(ext4_extent_idx_struct, i_block[12 * (entry_idx + 1):12 * (entry_idx + 2)])
            phys_block_no = (idx.ei_leaf_hi << 32) + idx.ei_leaf_lo
            buffer.seek(phys_block_no * sb_block_size)
            extents.extend(travers_extent_tree(buffer, buffer.read(sb_block_size)))
    return extents
