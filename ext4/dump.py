from ext4.cat import cat_by_blocks


def dump(buffer, sb, bg_descriptors, inode_no, dest):
    """

    Args:
        inode_no: Inode number to dump
        dest: dump destination
    """
    with open(dest, 'wb') as dest_buffer:
        for block in cat_by_blocks(buffer, sb, bg_descriptors, inode_no):
            dest_buffer.write(block)
