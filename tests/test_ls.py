from os import path
from pathlib import PurePosixPath

import pytest

from ext4.core import open_img
from ext4.ls import ls, path_to_inode, format_ls_output_by_lines


@pytest.mark.parametrize('img, expected_content_file, inode, recursively', [
    # small images: 8 MiB
    (path.join('tests', 'images', 'small_1.img'),
     path.join('tests', 'outputs', 'ls__small_1__root'),
     2,
     False),
    (path.join('tests', 'images', 'small_1.img'),
     path.join('tests', 'outputs', 'tree__small_1__TestDir1.TestDir1_1.txt'),
     19,
     True),
    (path.join('tests', 'images', 'small_1.img'),
     path.join('tests', 'outputs', 'tree__small_1__root.txt'),
     2,
     True),
])
def test_ls(img: str, expected_content_file: str, inode: int, recursively: bool):
    with open(expected_content_file, 'r', encoding='utf-8') as f:
        expected_content = f.read()
        with open_img(img) as image_tuple:
            ls_res = ls(*image_tuple, inode, recursively=recursively)
            assert '\n'.join(format_ls_output_by_lines(ls_res)) + '\n' == expected_content


@pytest.mark.parametrize('img, path, expected_inode', [
    (path.join('tests', 'images', 'small_1.img'), PurePosixPath('/Test1.txt'), 12),
    (path.join('tests', 'images', 'small_1.img'), PurePosixPath('TestDir1/Test1_1.txt'), 17),
])
def test_path_to_inode(img: str, path: str, expected_inode: int):
    with open_img(img) as image_tuple:
        actual_inode = path_to_inode(*image_tuple, path)
        assert actual_inode == expected_inode


@pytest.mark.skipif(not path.exists(path.join('tests', 'images', 'big_1.img')), reason='require big image')
@pytest.mark.parametrize('img, path, expected_inode', [
    (path.join('tests', 'images', 'big_1.img'), PurePosixPath('/etc/passwd'), 540745),
    (path.join('tests', 'images', 'big_1.img'), PurePosixPath('/usr/lib/firefox-esr/libxul.so'), 399798),
])
def test_path_to_inode__big(img: str, path: str, expected_inode: int):
    with open_img(img) as image_tuple:
        actual_inode = path_to_inode(*image_tuple, path)
        assert actual_inode == expected_inode
