from os import path
from pathlib import PurePosixPath

from ext4.ls import path_to_inode
from ext4.tools import cat, update_file
from tests.conftest import TEST_IMAGES_FOLDER, open_temp_img, assert_file_exists


def test_update_basic():
    test_file = path.join(TEST_IMAGES_FOLDER, 'small_1.img')
    with open_temp_img(test_file, write=True) as img:
        filepath = PurePosixPath('/Test2.txt')
        inode_no = path_to_inode(*img, filepath)
        source_content = cat(*img, filepath)
        assert source_content[3:] != b'new', "Test must be correct"

        update_file(img, inode_no, 0, b'new')

        actual_content = cat(*img, filepath)
        assert actual_content == b'new' + source_content[3:]
