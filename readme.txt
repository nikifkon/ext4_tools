usage: app.py [-h] [--debug]
              image_path {stat,cat,ls,path_to_inode,dump,mv,rename,rm,fsck}
              ...

positional arguments:
  image_path
  {stat,cat,ls,path_to_inode,dump,mv,rename,rm,fsck}
    stat                Show inode information
    cat                 Dump an inode out to stdout
    ls                  List directory
    path_to_inode       Print inode number of file
    dump                Dump an inode out to a file
    mv (rename)         Move file
    rm                  Remove file
    fsck                Check file system

optional arguments:
  -h, --help            show this help message and exit
  --debug, -d           Enable debug mode


Resources:
- [Format](https://ext4.wiki.kernel.org/index.php/Ext4_Disk_Layout)
- [About fsck](http://web.mit.edu/tytso/www/linux/ext2intro.html)
- [About deletion](https://www.sciencedirect.com/science/article/pii/S1742287612000357)
- [Intro to preallocation and explanation of ext4_extent.ee_len field](http://web.archive.org/web/20220630125537/https://www.sans.org/blog/understanding-ext4-part-5-large-extents/)

Useful tools:
- debugfs


Videos:
- [about old direct-indirect mapping](https://youtu.be/tMVj22EWg6A)
