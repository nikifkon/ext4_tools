from collections import defaultdict
from itertools import chain
from struct import pack
from typing import Iterator

from crc32c import crc32c

from ext4.block_group_descriptor import calc_bitmap_checksum, read_block_bitmap, read_inode_bitmap
from ext4.cat import travers_extent_tree
from ext4.core import Image
from ext4.exceptions import WrongSuperBlockChecksum, WrongBlockGroupDescriptorChecksum, WrongBlockBitmapChecksum, \
    WrongInodeBitmapChecksum, WrongInodeChecksum, SharedBlock, Coincidences, FsckException, UnconnectedInode
from ext4.inode import calc_checksum
from ext4.ls import ls
from ext4.structures import superblock_struct, repack_struct, block_group_descriptor_struct, parse_struct, \
    ext4_inode_struct, ext4_inode_extra_struct
from ext4.utils import zero_range, merge_hi_lo, get_block_size, iter_used_values_in_bitmap, iter_blocks_in_leaf, \
    get_groups_count


class SharedBlocksExcFactory:
    def __init__(self):
        self.block_to_inode = defaultdict(lambda: set())  # need optimization
        self.inodes_to_coincidences = defaultdict(lambda: Coincidences(set(), set()))

    def record_inode(self, inode: int, blocks: Iterator[int]):
        blocks = list(blocks)
        assert len(blocks) == len(set(blocks)), blocks
        for block in blocks:
            if block not in self.block_to_inode:
                self.block_to_inode[block].add(inode)
                continue
            other_inodes = self.block_to_inode[block]
            self.inodes_to_coincidences[inode].blocks.add(block)
            self.inodes_to_coincidences[inode].inodes.update(other_inodes)
            for other_inode in other_inodes:
                self.inodes_to_coincidences[other_inode].blocks.add(block)
                self.inodes_to_coincidences[other_inode].inodes.add(inode)

    def create(self) -> Iterator[SharedBlock]:
        for inode, coincidence in self.inodes_to_coincidences.items():
            yield SharedBlock(inode, coincidence)


class UnconnectedInodeExcFactory:
    def __init__(self):
        self.used_inode = set()

    def record_inode(self, inode_num: int):
        self.used_inode.add(inode_num)

    def record_connected_inode(self, inode_num: int):
        self.used_inode.discard(inode_num)

    def create(self) -> Iterator[SharedBlock]:
        for inode_num in self.used_inode:
            if inode_num > 12:  # isn't special?
                yield UnconnectedInode(inode_num)


# global
unconnected_factory = UnconnectedInodeExcFactory()


def fsck(img) -> Iterator[FsckException]:
    print("pass 0 IN PROGRESS")
    yield from pass_0(img)
    print("pass 0 COMPLETED")
    print("pass 1 IN PROGRESS")
    yield from pass_1(img)
    print("pass 1 COMPLETED")
    print("pass 3")
    yield from pass_3(img)
    print("pass 3 COMPLETED")


def pass_0(img: Image) -> Iterator[FsckException]:
    superblock_raw = repack_struct(img.sb, superblock_struct)
    if crc32c(superblock_raw) != 0xff_ff_ff_ff:
        yield WrongSuperBlockChecksum()

    if img.sb.s_feature_incompat & 0x2000 == 0:
        for bg_num, bg in enumerate(img.bg_descriptors):
            actual_csum = bg.bg_checksum
            bg_to_checksum = pack('<16s', img.sb.s_uuid) + \
                             pack('<L', bg_num) + \
                             zero_range(repack_struct(bg, block_group_descriptor_struct), 0x1E, 2)
            expected_csum = (~crc32c(bg_to_checksum) & 0xff_ff)
            if actual_csum != expected_csum:
                yield WrongBlockGroupDescriptorChecksum(bg_num, expected_csum, actual_csum)
    else:
        print('Checksum validating skipped due unsupported feature: uninit_bg')


def pass_1(img: Image) -> Iterator[FsckException]:
    global unconnected_factory
    shared_blocks_factory = SharedBlocksExcFactory()

    for bg_num, bg in enumerate(img.bg_descriptors):
        print('Checking group {}/{}'.format(bg_num + 1, get_groups_count(img)))
        actual_block_bitmap_csum = merge_hi_lo(bg.bg_block_bitmap_csum_hi, bg.bg_block_bitmap_csum_lo, lo_size=16)
        actual_inode_bitmap_csum = merge_hi_lo(bg.bg_inode_bitmap_csum_hi, bg.bg_inode_bitmap_csum_lo, lo_size=16)

        sb_block_size = get_block_size(img)

        if not bg.bg_flags & 0x2:  # is block bitmap initialized?
            block_bitmap_raw = read_block_bitmap(img, bg)
            expected_csum = calc_bitmap_checksum(img, block_bitmap_raw)
            if actual_block_bitmap_csum != expected_csum:
                yield WrongBlockBitmapChecksum(bg_num, expected_csum, actual_block_bitmap_csum)

        if not bg.bg_flags & 0xf1:
            inode_bitmap_raw = read_inode_bitmap(img, bg)
            expected_csum = calc_bitmap_checksum(img, inode_bitmap_raw)
            if actual_inode_bitmap_csum != expected_csum:
                yield WrongInodeBitmapChecksum(bg_num, expected_csum, actual_inode_bitmap_csum)

            bg_inode_table = merge_hi_lo(bg.bg_inode_table_hi, bg.bg_inode_table_lo)
            img.buffer.seek(bg_inode_table * sb_block_size)
            prev_offset = 0
            for offset in iter_used_values_in_bitmap(inode_bitmap_raw):
                img.buffer.seek((offset - prev_offset) * img.sb.s_inode_size, 1)
                inode_raw = img.buffer.read(img.sb.s_inode_size)
                prev_offset = offset + 1
                inode = parse_struct(ext4_inode_struct, inode_raw[:0x80])

                has_hi = False
                if img.sb.s_inode_size > 128:
                    inode_extra_raw = inode_raw[0x80:0xA0]
                    inode_extra = parse_struct(ext4_inode_extra_struct, inode_extra_raw)
                    has_hi = bool(inode_extra.i_extra_isize)
                if has_hi:
                    actual_csum = merge_hi_lo(inode_extra.i_checksum_hi, inode.i_checksum_lo, lo_size=16)
                else:
                    actual_csum = inode.i_checksum_lo

                inode_no = img.sb.s_inodes_per_group * bg_num + offset + 1
                expected_csum = calc_checksum(img, inode_no, inode.i_generation, inode_raw, has_hi)

                if actual_csum != expected_csum:
                    yield WrongInodeChecksum(inode_no, expected_csum, actual_csum, fmt='<L' if has_hi else '<H')
                current = img.buffer.tell()
                try:
                    shared_blocks_factory.record_inode(inode_no,
                                                       chain(*[iter_blocks_in_leaf(leaf) for leaf in
                                                               travers_extent_tree(img.buffer, inode.i_block, sb_block_size)]))
                except NotImplementedError:
                    pass
                finally:
                    img.buffer.seek(current)
                unconnected_factory.record_inode(inode_no)

    yield from shared_blocks_factory.create()


def traverse_whole_tree(entries):
    for dir_entry, _, children in entries:
        unconnected_factory.record_connected_inode(dir_entry.inode)
        traverse_whole_tree(children)


def pass_3(img: Image) -> Iterator[FsckException]:
    traverse_whole_tree(ls(*img, 2, recursively=True))
    yield from unconnected_factory.create()
