from os import path
from typing import Set

import pytest

from ext4.core import open_img
from ext4.fsck import fsck
from ext4.exceptions import WrongSuperBlockChecksum, WrongBlockGroupDescriptorChecksum, WrongInodeBitmapChecksum, \
    WrongBlockBitmapChecksum, WrongInodeChecksum, FsckException, SharedBlock, Coincidences, UnconnectedInode
from tests.conftest import TEST_IMAGES_FOLDER


@pytest.mark.parametrize('test_file, exc_list', [
    (path.join(TEST_IMAGES_FOLDER, 'superblock_wrong_checksum.img'),
     {WrongSuperBlockChecksum()}),
    (path.join(TEST_IMAGES_FOLDER, 'block_group_descriptor_wrong_checksum.img'),
     {WrongBlockGroupDescriptorChecksum(0, 0xcdc1, 0xcd21)}),
    (path.join(TEST_IMAGES_FOLDER, 'inode_bitmap_wrong_checksum.img'),
     {WrongInodeBitmapChecksum(0, 0x0fd97df6, 0x0f767df6)}),
    (path.join(TEST_IMAGES_FOLDER, 'block_bitmap_wrong_checksum.img'),
     {WrongBlockBitmapChecksum(0, 0xfa91794d, 0x0091794d)}),
    (path.join(TEST_IMAGES_FOLDER, 'inode_12_wrong_checksum.img'),
     {WrongInodeChecksum(12, 0xadf1, 0x64ca, fmt='<H')}),
    (path.join(TEST_IMAGES_FOLDER, 'shared_blocks.img'),
     {SharedBlock(13, Coincidences({1366}, {14})), SharedBlock(14, Coincidences({1366}, {13}))}),
    (path.join(TEST_IMAGES_FOLDER, 'unconnected_inode.img'),
     {UnconnectedInode(15), *{UnconnectedInode(i) for i in range(17, 22)}}),
    (path.join(TEST_IMAGES_FOLDER, 'small_1.img'),
     set())
])
def test_checksums(test_file, exc_list: Set[FsckException]):
    with open_img(test_file) as img:
        assert set(fsck(img)) == exc_list
