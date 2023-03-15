import argparse
import sys
import traceback
from functools import partial
from pathlib import PurePosixPath

from ext4.core import open_img
from ext4.dump import dump
from ext4.inode import get_inode, format_inode_stat
from ext4.cat import cat_by_blocks, travers_extent_tree
from ext4.ls import ls, path_to_inode, format_ls_output_by_lines
from ext4.mv import mv
from ext4.rm import rm
from ext4.fsck import fsck
from ext4.utils import print_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image_path')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    subparsers = parser.add_subparsers(dest='command')

    stat_parser = subparsers.add_parser('stat', help='Show inode information')
    stat_parser.add_argument('file_path', type=PurePosixPath)

    cat_parser = subparsers.add_parser('cat', help='Dump an inode out to stdout')
    cat_parser.add_argument('file_path', type=PurePosixPath)

    ls_parser = subparsers.add_parser('ls', help='List directory')
    ls_parser.add_argument('file_path', type=PurePosixPath, default=PurePosixPath('/'), nargs='?')
    ls_parser.add_argument('-r', action='store_true', help='Do it recursively')

    path_to_inode_parser = subparsers.add_parser('path_to_inode', help='Print inode number of file')
    path_to_inode_parser.add_argument('file_path', type=PurePosixPath)

    dump_parser = subparsers.add_parser('dump', help='Dump an inode out to a file')
    dump_parser.add_argument('file_path', type=PurePosixPath)
    dump_parser.add_argument('dest', help='Destination file path')

    mv_parser = subparsers.add_parser('mv', help='Move file', aliases=['rename'])
    mv_parser.add_argument('source', type=PurePosixPath)
    mv_parser.add_argument('dest', type=PurePosixPath)

    rm_parser = subparsers.add_parser('rm', help='Remove file')
    rm_parser.add_argument('file_path', type=PurePosixPath)

    subparsers.add_parser('fsck', help='Check file system')

    args = parser.parse_args()
    sys.excepthook = partial(general_excepthook, args.debug)

    if not args.command:
        parser.print_help()
    write = args.command in ('mv', 'rm')
    with open_img(args.image_path, write) as img:
        if args.command == 'stat':
            inode_no = path_to_inode(*img, args.file_path) if args.file_path else args.inode_number
            inode = get_inode(*img, inode_no)
            print(format_inode_stat(inode, inode_no, travers_extent_tree(img, inode.i_block)))
        elif args.command == 'cat':
            inode_no = path_to_inode(*img, args.file_path) if args.file_path else args.inode_number
            for block in cat_by_blocks(*img, inode_no):
                print(block.decode('utf-8', errors='ignore'), end='')
        elif args.command == 'ls':
            inode_no = path_to_inode(*img, args.file_path) if args.file_path else args.inode_number
            for line in format_ls_output_by_lines(ls(*img, inode_no, recursively=args.r)):
                print(line)
        elif args.command == 'tree_parser':
            pass
        elif args.command == 'dump':
            inode_no = path_to_inode(*img, args.file_path) if args.file_path else args.inode_number
            dump(*img, inode_no, args.dest)
        elif args.command == 'path_to_inode':
            print(path_to_inode(*img, args.file_path))
        elif args.command == 'mv':
            mv(img, args.source, args.dest)
        elif args.command == 'rm':
            rm(img, args.file_path)
        elif args.command == 'fsck':
            for exc in fsck(img):
                msg = '{}'.format(str(exc))
                print_error(msg)


def general_excepthook(is_debug_mode, errtype, value, tb):
    """
    Handle unexpected exceptions
    """
    if is_debug_mode:
        print(''.join(traceback.format_exception(errtype, value, tb)))
    else:
        msg = '{}: {}.'.format(errtype.__name__, value)
        print_error(msg)


if __name__ == '__main__':
    main()
