from os import path

import pytest

from ext4.core import open_img
from ext4.cat import cat_by_blocks


@pytest.mark.parametrize('img, expected_content_file, inode', [
    # small images: 8 MiB
    (path.join('tests', 'images', 'small_1.img'),
     path.join('tests', 'outputs', 'cat__small_1__Test1'),
     12),
    (path.join('tests', 'images', 'small_1.img'),
     path.join('tests', 'outputs', 'cat__small_1__TestDir1_Test1_1'),
     17),
])
def test_read_file(img: str, expected_content_file: str, inode: int):
    with open(expected_content_file, 'rb') as f:
        with open_img(img) as image_tuple:
            for block in cat_by_blocks(*image_tuple, inode):
                assert block == f.read(len(block))


@pytest.mark.skipif(not path.exists(path.join('tests', 'images', 'big_1.img')), reason='require big image')
@pytest.mark.parametrize('img, expected_content_file, inode', [
    (path.join('tests', 'images', 'big_1.img'),
     path.join('tests', 'outputs', 'cat__big_1__initrd_img'),
     25),
    (path.join('tests', 'images', 'big_1.img'),
     path.join('tests', 'outputs', 'cat__big_1__etc_passwd'),
     540745),
    (path.join('tests', 'images', 'big_1.img'),
     path.join('tests', 'outputs', 'cat__big_1__usr_lib_firefox-esr_libxul.so'),
     399798),
])
def test_read_file__big(img: str, expected_content_file: str, inode: int):
    with open(expected_content_file, 'rb') as f:
        with open_img(img) as image_tuple:
            for block in cat_by_blocks(*image_tuple, inode):
                assert block == f.read(len(block))
