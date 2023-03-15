from os import path
from pathlib import PurePosixPath

import pytest

from ext4.rm import rm
from tests.conftest import TEST_IMAGES_FOLDER, open_temp_img, assert_file_exists, open_temp_img_with_assert_consistent


# recursive

@pytest.mark.parametrize('filepath', [
    PurePosixPath('/Test2.txt'),
    PurePosixPath('/TestDir1')
])
def test_rm_basic(filepath: PurePosixPath):
    test_file = path.join(TEST_IMAGES_FOLDER, 'small_1.img')

    with open_temp_img_with_assert_consistent(test_file, write=True) as img:
        rm(img, filepath)
        assert_file_exists(img, filepath, expect_to_exists=False)
