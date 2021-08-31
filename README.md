# setboot
- A tiny tool for configuring the GRUB menu in Ubuntu systems
- Tested with Ubuntu 18.04 and 20.04, Legacy and UEFI mode

# Prerequirement
- Ubuntu
- grub-mkconfig
- python 2.x or 3.x
- An account with sudo permission for installing and running this tool

# Installation
- clone this repo or download setboot and setboot.py
- chmod 755 setboot and setboot.py
- copy setboot and setboot.py to /usr/local/sbin (or other places you preferred)

# Usage
- For the system with single boot drive:
    - Simply run setboot

- For the system with multiple boot drive:
    - Method 1:
        1. Locate the boot drive the BIOS will use, e.g., /dev/sdb2
        2. Run setboot /dev/sdb2
    - Method 2:
        1. Locate the boot drive the BIOS will use
        2. Mount the drive to a point, e.g., /tmp/bootDev
        2. Run setboot /tmp/bootDev/boot/grub.conf /tmp/bootDev/etc/default/grub

# Advanced usage
- The default location for grub.conf is /boot/grub/grub.conf
- The default location for grub environment file is /etc/default/grub
- Both files must exist when running setboot
- When running setboot, you may specify the location of grub.conf with the first argument, and also the location for grub environment file with the second argument
    - e.g., setboot /home/mhchen/dryrun/grub.conf
    - e.g., setboot /home/mhchen/dryrun/grub.conf /home/mhchen/dryrun/grub

# Known issues
- Does not be able to detect the drive for booting the current system
