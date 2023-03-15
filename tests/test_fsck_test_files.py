import platform
from os import path
import subprocess

import pytest

from tests.conftest import TEST_IMAGES_FOLDER


@pytest.mark.skipif(platform.system() == 'Windows', reason='require fsck.ext4 utils')
@pytest.mark.parametrize('test_file, expected_errors', [
    (
        # patch 7FC from 64 to FF
        path.join(TEST_IMAGES_FOLDER, 'superblock_wrong_checksum.img'),
        ('Superblock checksum does not match superblock',),
    ),
    (
        # patch 81E from C1 to 21
        path.join(TEST_IMAGES_FOLDER, 'block_group_descriptor_wrong_checksum.img'),
        ('One or more block group descriptor checksums are invalid.',),
    ),
    (
        # patch 83A from D9 to 76, 81E from C1 CD to 28 88
        path.join(TEST_IMAGES_FOLDER, 'inode_bitmap_wrong_checksum.img'),
        ('Group 0 inode bitmap does not match checksum.',),
    ),
    (
        # patch 839 from FA to 00, 81E from C1 CD to 97 19
        path.join(TEST_IMAGES_FOLDER, 'block_bitmap_wrong_checksum.img'),
        ('Group 0 block bitmap does not match checksum.',),
    ),
    (
        # patch 18DE4 from 28 to 11
        path.join(TEST_IMAGES_FOLDER, 'inode_12_wrong_checksum.img'),
        ('Inode 12 passes checks, but checksum does not match inode.',),
    ),
    (
        # debugfs: eo Test2.txt
        # debugfs (extent ino 13): last_leaf
        # extent: lblk 0--0, len 1, pblk 1365, flags: LEAF
        # debugfs (extent ino 13): set_bmap 0 1366
        # extent: lblk 0--0, len 1, pblk 1366, flags: LEAF
        # debugfs (extent ino 13): ec
        # debugfs:  cat Test2.txt
        # This is Test3.txt
        path.join(TEST_IMAGES_FOLDER, 'shared_blocks.img'),
        ('Multiply-claimed block(s) in inode 13: 1366', 'Multiply-claimed block(s) in inode 14: 1366')
    ),
    (
        # debugfs:  unlink TestDir1
        path.join(TEST_IMAGES_FOLDER, 'unconnected_inode.img'),
        ('Unconnected directory inode 15 (/???)',)
    )

])
def test_test_files(test_file: str, expected_errors: str):
    bashCommand = 'fsck.ext4 -n -f %s' % test_file
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()
    output = output.decode('utf-8')
    for expected_error in expected_errors:
        assert expected_error in output
