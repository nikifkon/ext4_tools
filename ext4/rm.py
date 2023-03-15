from pathlib import PurePosixPath

from ext4.core import Image
from ext4.inode import get_inode, parse_inode_mode, FileType
from ext4.ls import path_to_inode
from ext4.tools import free_inode, ls, unlink


def rm(img: Image, filepath: PurePosixPath):
    inode_no = path_to_inode(*img, filepath)
    free_inode(img, inode_no)

    inode = get_inode(*img, inode_no)
    _, filetype = parse_inode_mode(inode.i_mode)
    if filetype == FileType.DIRECTORY:
        for dir_entry, name, children in ls(*img, filepath):
            if name == '.' or name == '..':
                continue
            rm(img, filepath / name)
    free_inode(img, inode_no)
    unlink(img, filepath)
