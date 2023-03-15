from struct import unpack, pack
from collections import namedtuple
from typing import List, Tuple

# Describe structures. None means field don't use in this program
superblock_struct = (
    ('<L', None),  # ('<L', 's_inodes_count'),
    ('L', 's_blocks_count_lo'),
    ('L', None),  # ('L', 's_r_blocks_count_lo'),
    ('L', None),  # ('L', 's_free_blocks_count_lo'),
    ('L', None),  # ('L', 's_free_inodes_count'),
    ('L', 's_first_data_block'),
    ('L', 's_log_block_size'),
    ('L', None),  # ('L', 's_log_cluster_size'),
    ('L', 's_blocks_per_group'),
    ('L', None),  # ('L', 's_clusters_per_group'),

    # used in inode addressing algorithm: inode_number -> (group_number, index)
    # inode_number |-> ([inode_number - 1] / sb.s_inodes_per_group, [inode_number - 1] % sb.s_inodes_per_group)
    ('L', 's_inodes_per_group'),

    ('L', None),  # ('L', 's_mtime'),
    ('L', None),  # ('L', 's_wtime'),
    ('H', None),  # ('H', 's_mnt_count'),
    ('H', None),  # ('H', 's_max_mnt_count'),
    ('H', None),  # ('H', 's_magic'),
    ('H', None),  # ('H', 's_state'),
    ('H', None),  # ('H', 's_errors'),
    ('H', None),  # ('H', 's_minor_rev_level'),
    ('L', None),  # ('L', 's_lastcheck'),
    ('L', None),  # ('L', 's_checkinterval'),
    ('L', None),  # ('L', 's_creator_os'),
    ('L', None),  # ('L', 's_rev_level'),
    ('H', None),  # ('H', 's_def_resuid'),
    ('H', None),  # ('H', 's_def_resgid'),
    ('L', None),  # ('L', None),  # ('L', 's_first_ino'),

    # used in inode addressing algorithm: to locate inode in specific group's inode_table with given index
    # offset_in_group_table |-> offset_in_group_table * sb.s_inode_size
    ('H', 's_inode_size'),

    ('H', None),  # ('H', 's_block_group_nr'),

    ('L', None),  # ('L', None),  # ('L', 's_feature_compat'),

    ('L', 's_feature_incompat'),
    ('L', None),  # ('L', None),  # ('L', 's_feature_ro_compat'),

    ('16s', 's_uuid'),
    ('16s', None),  # ('16s', 's_volume_name'),
    ('64s', None),  # ('64s', 's_last_mounted'),
    ('L', None),  # ('L', None),  # ('L', 's_algorithm_usage_bitmap'),
    ('B', None),  # ('B', 's_prealloc_blocks'),
    ('B', None),  # ('B', 's_prealloc_dir_blocks'),
    ('H', None),  # ('H', 's_reserved_gdt_blocks'),
    ('16s', None),  # ('16s', 's_journal_uuid'),
    ('L', None),  # ('L', 's_journal_inum'),
    ('L', None),  # ('L', 's_journal_dev'),
    ('L', None),  # ('L', 's_last_orphan'),
    ('16s', None),  # ('16s', 's_hash_seed'),
    ('B', None),  # ('B', 's_def_hash_version'),
    ('B', None),  # ('B', 's_jnl_backup_type'),
    ('H', 's_desc_size'),
    ('L', None),  # ('L', 's_default_mount_opts'),
    ('L', None),  # ('L', 's_first_meta_bg'),
    ('L', None),  # ('L', 's_mkfs_time'),
    ('68s', None),  # ('68s', 's_jnl_blocks'),
    ('L', 's_blocks_count_hi'),
    ('L', None),  # ('L', 's_r_blocks_count_hi'),
    ('L', None),  # ('L', 's_free_blocks_count_hi'),
    ('H', None),  # ('H', 's_min_extra_isize'),
    ('H', None),  # ('H', 's_want_extra_isize'),
    ('L', None),  # ('L', 's_flags', ''),
    ('H', None),  # ('H', 's_raid_stride'),
    ('H', None),  # ('H', 's_mmp_interval'),
    ('Q', None),  # ('Q', 's_mmp_block'),
    ('L', None),  # ('L', 's_raid_stripe_width'),
    ('B', None),  # ('B', 's_log_groups_per_flex'),
    ('B', None),  # ('B', 's_checksum_type'),
    ('H', None),  # ('H', 's_reserved_pad'),
    ('Q', None),  # ('Q', 's_kbytes_written'),
    ('L', None),  # ('L', 's_snapshot_inum'),
    ('L', None),  # ('L', 's_snapshot_id'),
    ('Q', None),  # ('Q', 's_snapshot_r_blocks_count'),
    ('L', None),  # ('L', 's_snapshot_list'),
    ('L', None),  # ('L', 's_error_count'),
    ('L', None),  # ('L', 's_first_error_time'),
    ('L', None),  # ('L', 's_first_error_ino'),
    ('Q', None),  # ('Q', 's_first_error_block'),
    ('32s', None),  # ('32s', 's_first_error_func'),
    ('L', None),  # ('L', 's_first_error_line'),
    ('L', None),  # ('L', 's_last_error_time'),
    ('L', None),  # ('L', 's_last_error_ino'),
    ('L', None),  # ('L', 's_last_error_line'),
    ('Q', None),  # ('Q', 's_last_error_block'),
    ('32s', None),  # ('32s', 's_last_error_func'),
    ('64s', None),  # ('64s', 's_mount_opts'),
    ('L', None),  # ('L', 's_usr_quota_inum'),
    ('L', None),  # ('L', 's_grp_quota_inum'),
    ('L', None),  # ('L', 's_overhead_blocks'),
    ('8s', None),  # ('8s', 's_backup_bgs'),
    ('4s', None),  # ('4s', 's_encrypt_algos'),
    ('16s', None),  # ('16s', 's_encrypt_pw_salt'),
    ('L', None),  # ('L', 's_lpf_ino'),
    ('L', None),  # ('L', 's_prj_quota_inum'),
    ('L', None),  # ('L', 's_checksum_seed'),
    ('392s', None),  # ('392s', 's_reserved'),
    ('L', 's_checksum'),
)

block_group_descriptor_struct = (
    ('<L', 'bg_block_bitmap_lo'),
    ('L', 'bg_inode_bitmap_lo'),
    ('L', 'bg_inode_table_lo'),
    ('H', None),  # ('H', 'bg_free_blocks_count_lo'),
    ('H', None),  # ('H', 'bg_free_inodes_count_lo'),
    ('H', None),  # ('H', 'bg_used_dirs_count_lo'),
    ('H', 'bg_flags'),
    ('L', None),  # ('L', 'bg_exclude_bitmap_lo'),
    ('H', 'bg_block_bitmap_csum_lo'),
    ('H', 'bg_inode_bitmap_csum_lo'),
    ('H', None),  # ('H', 'bg_itable_unused_lo'),
    ('H', 'bg_checksum'),
    ('L', 'bg_block_bitmap_hi'),
    ('L', 'bg_inode_bitmap_hi'),
    ('L', 'bg_inode_table_hi'),
    ('H', None),  # ('H', 'bg_free_blocks_count_hi'),
    ('H', None),  # ('H', 'bg_free_inodes_count_hi'),
    ('H', None),  # ('H', 'bg_used_dirs_count_hi'),
    ('H', None),  # ('H', 'bg_itable_unused_hi'),
    ('L', None),  # ('L', 'bg_exclude_bitmap_hi'),
    ('H', 'bg_block_bitmap_csum_hi'),
    ('H', 'bg_inode_bitmap_csum_hi'),
    ('L', None),  # ('L', 'bg_reserved'),
)

ext4_inode_struct = (
    ('<H', 'i_mode'),  # 0x0:0x2
    ('H', 'i_uid'),  # 0x2:0x4

    # used to get end of file
    ('L', 'i_size_lo'),  # 0x4:0x8

    ('L', 'i_atime'),  # 0x8:0xc
    ('L', 'i_ctime'),  # 0xc:10
    ('L', 'i_mtime'),  # 0x10:0x14
    ('L', 'i_dtime'),  # 0x14:0x18
    ('H', 'i_gid'),  # 0x18:0x1a
    ('H', 'i_links_count'),  # 0x1a:0x1c
    ('L', 'i_blocks_lo'),  # 0x1c:0x20
    ('L', 'i_flags'),  # 0x20:0x24
    ('4s', None),  # ('4s', 'osd1'),  # 0x24:0x28
    ('60s', 'i_block'),  # 0x28:0x64
    ('L', 'i_generation'),  #
    ('L', None),  # ('L', 'i_file_acl_lo'),
    ('L', None),  # ('L', 'i_size_high / i_dir_acl'),
    ('L', None),  # ('L', 'i_obso_faddr'),
    ('8s', None),
    ('H', 'i_checksum_lo'),
    ('H', None)
)

ext4_inode_extra_struct = (
    ('<H', 'i_extra_isize'),
    ('H', 'i_checksum_hi'),
    ('L', None),
    ('L', None),
    ('L', None),
    ('L', None),
    ('L', None),
    ('L', None),
    ('L', None),
)

ext4_extent_header_struct = (
    ('<2s', 'eh_magic'),
    ('H', 'eh_entries'),
    ('H', None),  # ('H', 'eh_max'),
    ('H', 'eh_depth'),
    ('L', None),  # ('L', 'eh_generation'),
)

ext4_extent_idx_struct = (
    ('<L', None),  # ('L', 'ei_block'),
    ('L', 'ei_leaf_lo'),
    ('H', 'ei_leaf_hi'),
    ('2s', None),  # ('16B', 'ei_unused'),
)

ext4_extent_struct = (
    ('<L', 'ee_block'),
    ('H', 'ee_len'),
    ('H', 'ee_start_hi'),
    ('L', 'ee_start_lo'),
)

ext4_dir_entry_2 = (
    ('<L', 'inode',),
    ('H', 'rec_len',),
    ('B', 'name_len',),
    ('B', 'file_type'),
)


def get_struct_fields(struct: Tuple[Tuple[str, str]]) -> List[str]:
    return [field[1] if field[1] else f'c_{i}' for i, field in enumerate(struct)]


def get_struct_format(struct: Tuple[Tuple[str, str]]) -> str:
    return ''.join([field[0] for field in struct])


cached_namedtuples = {}


def parse_struct(struct: Tuple[Tuple[str, str]], raw: bytes) -> namedtuple:
    if struct not in cached_namedtuples:
        cached_namedtuples[struct] = namedtuple('Struct', get_struct_fields(struct))
    unpacked = unpack(get_struct_format(struct), raw)
    return cached_namedtuples[struct](*unpacked)


def repack_struct(data: namedtuple, struct: Tuple[Tuple[str, str]]) -> bytes:
    return pack(get_struct_format(struct), *data)
