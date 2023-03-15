import contextlib
from typing import Iterator, BinaryIO

from ext4.core import Image


def iter_used_values_in_bitmap(bitmap: bytes) -> Iterator[int]:
    i = 0
    for b in bitmap:
        mask = 0b0000_0001
        for _ in range(8):
            if mask & b:
                yield i
            mask <<= 1
            i += 1


def get_value_from_bitmap(bitmap: bytes, idx: int) -> bool:
    byte_idx = idx // 8
    bit_idx = idx % 8
    mask = 0b0000_0001 << bit_idx
    return bool(mask & bitmap[byte_idx])


def set_value_in_bitmap(bitmap: BinaryIO, idx: int, value: bool) -> None:
    byte_idx = idx // 8
    bitmap.seek(byte_idx, 1)
    byte = bitmap.read(1)
    bitmap.seek(-1, 1)
    bit_idx = idx % 8
    mask = 0b0000_0001 << bit_idx
    if value:
        bitmap.write(bytes([byte[0] | mask]))
    else:
        bitmap.write(bytes([byte[0] & ~mask]))


@contextlib.contextmanager
def brb(buffer):
    before = buffer.tell()
    yield buffer
    buffer.seek(before)


def say_when_last(iterator):
    prev = None
    for element in iterator:
        if prev:
            yield False, prev
        prev = element
    if prev:
        yield True, prev


def zero_range(raw: bytes, start: int, length: int) -> bytes:
    return raw[:start] + bytes.fromhex('00' * length) + raw[start + length:]


def merge_hi_lo(hi: int, lo: int, lo_size=32) -> int:
    return (hi << lo_size) + lo


def get_block_size(img: Image) -> int:
    return 1024 << img.sb.s_log_block_size


def seek_to_block(img: Image, block_no: int):
    img.buffer.seek(get_block_size(img) * block_no)


def read_next_block(img: Image) -> bytes:
    return img.buffer.read(get_block_size(img))


def iter_blocks_in_leaf(leaf) -> Iterator[int]:
    if leaf.ee_len > 32768:
        return []
    start = merge_hi_lo(leaf.ee_start_hi, leaf.ee_start_lo)
    return list(range(start, start + leaf.ee_len))


def get_groups_count(img: Image) -> int:
    return merge_hi_lo(img.sb.s_blocks_count_hi, img.sb.s_blocks_count_lo) // img.sb.s_blocks_per_group


def colored(r, g, b, text):
    return "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(r, g, b, text)


def print_error(msg: str):
    print(colored(255, 0, 0, msg))
