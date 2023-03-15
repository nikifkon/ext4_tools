from struct import pack
from typing import NamedTuple, Set


class FsckException(BaseException):
    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.args == other.args
        return False

    def __hash__(self):
        return hash(self.args)


class Pass0Exception(FsckException):
    pass


class WrongSuperBlockChecksum(Pass0Exception):
    pass


class WrongBlockGroupDescriptorChecksum(Pass0Exception):
    def __init__(self, bg_num: int, expected_csum: int, actual_csum: int):
        super().__init__('[Group {}] expected/actual csum: 0x{}/0x{}'.format(
            bg_num, pack('<H', expected_csum).hex(), pack('<H', actual_csum).hex()
        ))


class Pass1Exception(FsckException):
    pass


class WrongInodeChecksum(Pass1Exception):
    def __init__(self, inode_num: int, expected_csum: int, actual_csum: int, fmt='<L'):
        super().__init__('[Inode {}] expected/actual csum: 0x{}/0x{}'.format(
            inode_num, pack(fmt, expected_csum).hex(), pack(fmt, actual_csum).hex()
        ))


class WrongInodeBitmapChecksum(Pass1Exception):
    def __init__(self, bg_num: int, expected_csum: int, actual_csum: int):
        super().__init__('[Group {}] expected/actual csum: 0x{}/0x{}'.format(
            bg_num, pack('<L', expected_csum).hex(), pack('<L', actual_csum).hex()
        ))


class WrongBlockBitmapChecksum(Pass1Exception):
    def __init__(self, bg_num: int, expected_csum: int, actual_csum: int):
        super().__init__('[Group {}] expected/actual csum: 0x{}/0x{}'.format(
            bg_num, pack('<L', expected_csum).hex(), pack('<L', actual_csum).hex()
        ))


Coincidences = NamedTuple('Coincidences', [('blocks', Set[int]), ('inodes', Set[int])])


class SharedBlock(Pass1Exception):
    """
    Problem:
        Some block is claimed by more than one inode.
    Possible solutions:
        1. cloning the shared blocks
        2. deallocating one or more of the inodes
    """

    def __init__(self, inode_num: int, coincidence: Coincidences):
        super().__init__('[Inode {}] shared blocks below with inodes [{}]\n{}'.format(
            inode_num, ', '.join(map(str, coincidence.inodes)), '\t'.join(map(str, coincidence.blocks))
        ))


class Pass3Exception(FsckException):
    pass


class UnconnectedInode(Pass3Exception):
    """
    Problem:
        Some inode not indexed (not belong to root tree)
    Possible solutions:
        1. connect to lost+found
    """

    def __init__(self, inode_num: int):
        super().__init__('[Inode {}] unconnected!'.format(inode_num))


class Pass4Exception(FsckException):
    pass


class InvalidReferenceCount(Pass4Exception):
    """
    Problem:
        Links counter in inode not valid
    Possible solutions:
        1. correct
    """
    pass
