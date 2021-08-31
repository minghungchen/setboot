# setboot
- A tiny tool for configuring the GRUB menu in Ubuntu systems
- Tested with Ubuntu 18.04 and 20.04, Legacy and UEFI mode
- Theoretically this tool also works with other Linux distribution running GRUB, but you may want to change the location of default grub environment file (`defaultGrubEnvFile`) in setboot.py to make it work without extra parameters

# Prerequirement
- GRUB
- grub-mkconfig (should come with Ubuntu)
- python 2.x or 3.x
- An account with sudo permission for installing and running this tool

# Installation
- clone this repo or download setboot and setboot.py
- chmod 755 setboot and setboot.py
- copy setboot and setboot.py to `/usr/local/sbin` for everyone to use (or other places you preferred)

# Usage
- setboot will not actually do anything before you confirm the GRUB_CMDLINE_LINUX_DEFAULT option. It is safe to press ctrl-c to interrupt anytime before that.
- For the system with single boot drive:
    - Simply run setboot

- For the system with multiple boot drives:
    - Method 1:
        1. Locate the boot device the BIOS will use, e.g., /dev/sdb2, assuming that /boot and /etc are all in this device
        2. Run `setboot /dev/sdb2`
    - Method 2:
        1. Locate the boot device the BIOS will use, assuming that /boot and /etc are all in this device
        2. Mount the device, e.g., /tmp/bootDev
        2. Run `setboot /tmp/bootDev/boot/grub.conf /tmp/bootDev/etc/default/grub`
    - Method 3:
        1. Locate the boot device the BIOS will use, and the root device if it is differerent
        2. Mount the devices, e.g., /tmp/bootDev and /tmp/rootDev
        2. Run `setboot /tmp/bootDev/boot/grub.conf /tmp/rootDev/etc/default/grub`

# Advanced usage
- The default location for grub.conf is /boot/grub/grub.conf
- The default location for grub environment file is /etc/default/grub
- Both files must exist when running setboot
- When running setboot, you may specify the location of grub.conf with the first parameter, and also the location for grub environment file with the second parameter
    - e.g., `setboot /home/mhchen/dryrun/grub.conf`
    - e.g., `setboot /home/mhchen/dryrun/grub.conf /home/mhchen/dryrun/grub`

# Known issues
- Does not be able to detect the drive for booting the current system (please let me know if you know how to figure it out)
- The sequence of boot ment items could be changed or incorrect when switching among OS on different devices
- The backup grub environment files will not be automatically removed
    - They are small files, but you can clean them up by `rm /etc/default/grub.*`
- Cannot delete GRUB_CMDLINE_LINUX_DEFAULT options
    - Please delete them by editing your grub environment file, e.g., /etc/default/grub
- Cannot add an empty GRUB_CMDLINE_LINUX_DEFAULT string
    - If you need one but you don't have one, please editing your grub environment file, e.g., /etc/default/grub
