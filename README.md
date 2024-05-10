# setboot
- A tiny tool for configuring the GRUB menu in Ubuntu systems
- Support Ubuntu 18.04, 20.04, and 22.04, with both Legacy and UEFI mode
    - Please note RHEL experimental support is not fully functional yet
- Theoretically this tool also works with many other Linux distribution running GRUB, but you may want to change the location of default grub environment file (`defaultGrubEnvFile`) in setboot.py to make it work without extra parameters

# Prerequirement
- GRUB / grub-mkconfig, which comes with most OS distribution
- Python 2.x or 3.x, which comes with most OS distribution
- blkid and findmnt, which comes with most OS distribution
- os-prober if you need dual boot, which comes with Ubuntu
- An account with sudo permission for installing and running this tool

# Installation
- clone this repo or download setboot and setboot.py
- chmod 755 setboot and setboot.py if they are not executable.
- (optional) copy setboot and setboot.py to `/usr/local/sbin` for everyone to use (or other places you preferred)

# Usage
- setboot will not actually do anything before you confirm the GRUB_CMDLINE_LINUX_DEFAULT option. It is safe to press ctrl-c to interrupt anytime before that.
- For the system with single boot drive:
    - Simply run `setboot`

- For the system with multiple boot drives. Note you may need to manually add `GRUB_DISABLE_OS_PROBER=false` to `/etc/default/grub`:
    - Method 1:
        1. Simply run `setboot` and let grub detect the available boot options (suggested)
    - Method 2:
        1. Locate the boot device the BIOS will use, e.g., /dev/sdb2, assuming that /boot and /etc are all in this device
        2. Run `setboot /dev/sdb2`
    - Method 3:
        1. Locate the boot device the BIOS will use, assuming that /boot and /etc are all in this device
        2. Mount the device, e.g., /tmp/bootDev
        3. Run `setboot /tmp/bootDev/boot/grub.conf /tmp/bootDev/etc/default/grub`
    - Method 4:
        1. Locate the boot device the BIOS will use, and the root device if it is different
        2. Mount the devices, e.g., /tmp/bootDev and /tmp/rootDev
        3. Run `setboot /tmp/bootDev/boot/grub.conf /tmp/rootDev/etc/default/grub`

# Advanced usage
- The default location for grub.conf is /boot/grub/grub.conf
- The default location for grub environment file is /etc/default/grub
- Both files must exist when running setboot
- When running setboot, you may specify the location of grub.conf with the first parameter, and also the location for grub environment file with the second parameter
    - e.g., `setboot /home/mhchen/dryrun/grub.conf`
    - e.g., `setboot /home/mhchen/dryrun/grub.conf /home/mhchen/dryrun/grub`

# Known issues
- For dual-boot systems, setboot relies on os-prober to detect alternative boot options on other drives, but os-probe is default to disabled on some OS distributions
    - If you have security concerns on os-prober but need dual-boot, please consider to use EFI based boot manager for dual-boot management and you can continue to use setboot for managing grub config
    - If you want to manage dual-boot with grub and setboot, please manually add GRUB_DISABLE_OS_PROBER=false to /etc/default/grub and make sure os-prober is available in the system. Some OS may fully ignore os-prober, in that case, setboot may not work as expected with multiple boot drives
- May not be able to detect the drive for booting the current system, if the drive is specified in the kernel parameter. This appears to be a limitation of grub-mkconfig, but it can be resolved by os-prober as a kind of dual boot scenarios in some cases
- Boot items from LVM volumes may not show correctly. This appears to be an issue from os-prober
- The sequence of boot menu items could be changed or incorrect when switching among OS on different devices
- The backup grub environment files will not be automatically removed
    - They are small files, but you can clean them up by `rm /etc/default/grub.*`
- Cannot delete GRUB_CMDLINE_LINUX_DEFAULT options
    - No plan to add the feature of deleting options
    - Please delete them by editing your grub environment file, e.g., /etc/default/grub
- Cannot add an empty GRUB_CMDLINE_LINUX_DEFAULT string
    - If you need one but you don't have one, please editing your grub environment file, e.g., /etc/default/grub
