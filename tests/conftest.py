import contextlib
import shutil
import tempfile
from os import path
from pathlib import PurePosixPath
from typing import ContextManager

from ext4.fsck import fsck
from ext4.tools import ls
from ext4.core import Image, open_img

TEST_IMAGES_FOLDER = path.join('tests', 'images')
TEST_OUTPUT_FOLDER = path.join('tests', 'outputs')


def create_temporary_copy(source):
    temp_dir = tempfile.gettempdir()
    temp_path = path.join(temp_dir, 'temp_file_name')
    shutil.copy2(source, temp_path)
    return temp_path


@contextlib.contextmanager
def open_temp_img(img_path, write=False) -> ContextManager[Image]:
    temp_img_path = create_temporary_copy(img_path)
    with open_img(temp_img_path, write) as img:
        yield img


@contextlib.contextmanager
def open_temp_img_with_assert_consistent(img_path, write=False) -> ContextManager[Image]:
    with open_temp_img(img_path, write) as img:
        assert list(fsck(img)) == [], "Inconsistent state before test!"
        yield img
        assert list(fsck(img)) == [], "Inconsistent state after test!"


def assert_file_exists(img: Image, filepath: PurePosixPath, expect_to_exists: bool):
    """
    Assert that the file exists.
    """
    parent_list = list([name for _, name, _ in ls(*img, filepath.parent)])
    if expect_to_exists:
        assert filepath.name in parent_list, "File {} must exist!".format(filepath)
    else:
        assert filepath.name not in parent_list, "File {} must not exist!".format(filepath)
