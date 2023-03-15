import pytest

from ext4.inode import parse_inode_mode, FileType


@pytest.mark.parametrize('raw, mode, filetype', [
    (bytes.fromhex('81 FF'), '0777', FileType.REGULAR),
    (bytes.fromhex('A1 ED'), '0755', FileType.SYMBOLIC_LINK),
])
def test_parse_inode_mode__valid(raw: bytes, mode: str, filetype: FileType):
    actual_mode, actual_filetype = parse_inode_mode(int(raw.hex(), 16))
    assert actual_mode == mode
    assert actual_filetype == filetype


@pytest.mark.parametrize('raw', [
    bytes.fromhex('91 FF'),
])
def test_parse_inode_mode__invalid(raw: bytes):
    with pytest.raises(ValueError):
        parse_inode_mode(int(raw.hex()))
