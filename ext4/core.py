import contextlib
from typing import NamedTuple, BinaryIO, List, ContextManager

from ext4.structures import parse_struct, superblock_struct, block_group_descriptor_struct


Image = NamedTuple('Image', [('buffer', BinaryIO), ('sb', NamedTuple), ('bg_descriptors', List[NamedTuple])])


@contextlib.contextmanager
def open_img(img_path, write=False) -> ContextManager[Image]:
    mode = 'rb' if not write else 'r+b'
    with open(img_path, mode) as f:
        sb, bg_descriptors = parse_static(f)
        yield Image(f, sb, bg_descriptors)


def parse_static(buffer):
    buffer.seek(0x400)
    superblock_raw = buffer.read(0x400)
    sb = parse_struct(superblock_struct, superblock_raw)

    # validate
    if not sb.s_feature_incompat & 0x40:
        raise NotImplementedError("This program support only ext3/4 filesystem with EXTENTS (missing INCOMPAT_EXTENTS in sb.s_feature_incompat)")
    if not sb.s_feature_incompat & 0x2:
        raise NotImplementedError("This program support only ext4_dir_entry_2 (missing INCOMPAT_FILETYPE in sb.s_feature_incompat)")
    # if sb.s_feature_incompat & 0x80:
    #     raise NotImplementedError("This program don't support 64bit feature\nConsider to disable it by command: resize2fs -s <img>")

    s_block_size = 1024 << sb.s_log_block_size

    if s_block_size != 1024:
        buffer.seek(s_block_size - 0x800, 1)

    bg_descriptors = []
    bg_desc_count = ((sb.s_blocks_count_hi << 32) + sb.s_blocks_count_lo) // sb.s_blocks_per_group
    for bg_desc_idx in range(bg_desc_count):
        bg_desc_raw = buffer.read(sb.s_desc_size)
        bg_descriptors.append(
            parse_struct(block_group_descriptor_struct, bg_desc_raw)
        )
    return sb, bg_descriptors
