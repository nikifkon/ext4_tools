from os import path

import pytest

from ext4.cat import travers_extent_tree
from ext4.core import open_img
from ext4.inode import get_inode, format_inode_stat


@pytest.mark.parametrize('img, expected_content_file, inode_no', [
    # small images: 8 MiB
    (path.join('tests', 'images', 'small_1.img'),
     path.join('tests', 'outputs', 'stat__small_1__Test1.txt'),
     12),
    (path.join('tests', 'images', 'small_1.img'),
     path.join('tests', 'outputs', 'stat__small_1__TestDir1_Test1_1.txt'),
     17),
    (path.join('tests', 'images', 'small_1.img'),
     path.join('tests', 'outputs', 'stat__small_1__TestDir1_TestDir1_1.txt'),
     19),
])
def test_stat(img: str, expected_content_file: str, inode_no: int):
    with open(expected_content_file, 'r') as f:
        expected_content = f.read()
        with open_img(img) as image_data:
            inode_data = get_inode(*image_data, inode_no)
            assert format_inode_stat(inode_data, inode_no, travers_extent_tree(img, inode_data.i_block)) == expected_content


@pytest.mark.skipif(not path.exists(path.join('tests', 'images', 'big_1.img')), reason='require big image')
@pytest.mark.parametrize('img, expected_content_file, inode_no', [
    # large images: 16 GiB
    (path.join('tests', 'images', 'big_1.img'),
     path.join('tests', 'outputs', 'stat__big_1__etc_passwd.txt'),
     540745),
    (path.join('tests', 'images', 'big_1.img'),
     path.join('tests', 'outputs', 'stat__big_1__usr_lib_firefox-esr_libxul.so.txt'),
     399798),
])
def test_stat__big(img: str, expected_content_file: str, inode_no: int):
    with open(expected_content_file, 'r') as f:
        expected_content = f.read()
        with open_img(img) as image_data:
            inode_data = get_inode(*image_data, inode_no)
            assert format_inode_stat(inode_data, inode_no, travers_extent_tree(img, inode_data.i_block)) == expected_content
