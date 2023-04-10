import signal
import sys
import os
import subprocess
import time

# this parameter defines the minimal grub timeout. suggested value: 10 seconds
minGrubTimeout = 10
# this parameter defines if to verify the grub timeout style is menu. suggested value: True
useGrubMenu = True

tmpMountPath = "/tmp/tmpBootDev"
tmpGrubBootFile = "/tmp/tmpGrubBootFile"
tmpEnvFile = "/tmp/tmpGrubEnvFile"

defaultGrubBootFile = "/boot/grub/grub.cfg"
defaultGrubEnvFile = "/etc/default/grub"

devDiskUUIDPath = "/dev/disk/by-uuid"

# deal with Python 2.x
if hasattr(__builtins__, 'raw_input'):
      input=raw_input

def showInfo():
    print("--------------------------------------------")
    print("GRUB Boot Menu Configuration Tool. 2021/10/13 R1")
    print("Please report issues to GitHub repo at:")
    print("https://github.com/minghungchen/setboot")
    print("--------------------------------------------")

def interruptSignalHandler(sig, frame):
    if os.path.isfile(tmpGrubBootFile):
        cmd = "sudo rm " + tmpGrubBootFile
        ret = os.system(cmd)
        if ret != 0:
            print("Failed to clean up temp file: %s but harmless" % tmpGrubBootFile)
    if os.path.isfile(tmpEnvFile):
        cmd = "sudo rm " + tmpEnvFile
        ret = os.system(cmd)
        if ret != 0:
            print("Failed to clean up temp file: %s but harmless" % tmpEnvFile)
    if os.path.isdir(tmpMountPath):
        if os.path.ismount(tmpMountPath):
            cmd = "sudo umount " + tmpMountPath
            ret = os.system(cmd)
            if ret != 0:
                print("Failed to unmount temp directory: %s but harmless" % tmpMountPath)
        cmd = "sudo rmdir " + tmpMountPath
        ret = os.system(cmd)
        if ret != 0:
             print("Failed to clean up temp directory: %s but harmless" % tmpMountPath)
    print("\n[WARN] Force interrupt detected. Please make sure GRUB is bootable before the next reboot")
    print("Suggestion: check and restore /etc/default/grub, and run update-grub or grub-mkconfig manually")
    sys.exit(1)

def verifyRootPermissionAndCacheSudo():
    ret = 0
    if os.geteuid() != 0:
        ret = 1
        msg = "[sudo] password for %u:"
        ret = subprocess.check_call("sudo -v -p '%s'" % msg, shell=True)
    return ret

def updateBootFile(grubBootFile, grubEnvFile):
    bakGrubEnvFile = defaultGrubEnvFile + ".setBoot.bak"
    if grubEnvFile != defaultGrubEnvFile:
        cmd = "sudo mv " + defaultGrubEnvFile + " " + bakGrubEnvFile
        ret = os.system(cmd)
        if ret != 0:
            sys.exit("Failed to rename %s to %s. Please verify the %s is good." % (defaultGrubEnvFile,bakGrubEnvFile,defaultGrubEnvFile))
        cmd = "sudo cp " + grubEnvFile + " " + defaultGrubEnvFile
        ret = os.system(cmd)
        if ret != 0:
            sys.exit("Failed to copy %s to %s. Please verify the %s and its backup %s are good."% (grubEnvFile,defaultGrubEnvFile,defaultGrubEnvFile,bakGrubEnvFile) )
    cmd = "sudo grub-mkconfig -o " + grubBootFile + " > /dev/null 2>&1"
    ret = os.system(cmd)
    if ret != 0:
        sys.exit("Failed to generating a temporarily grub boot file with grub-mkconfig.")
    if grubEnvFile != defaultGrubEnvFile:
        cmd = "sudo rm " + defaultGrubEnvFile
        ret = os.system(cmd)
        if ret != 0:
            sys.exit("Failed to remove %s. You may want to manually mv %s to %s." % (defaultGrubEnvFile,bakGrubEnvFile,defaultGrubEnvFile))
        cmd = "sudo mv " + bakGrubEnvFile + " " + defaultGrubEnvFile
        ret = os.system(cmd)
        if ret != 0:
            sys.exit("Failed to rename %s to %s. You may want to manually conduct this operation." % (bakGrubEnvFile,defaultGrubEnvFile) )

def parseEnvFile(envFile):
    curGrubCmdLines = []
    curGrubPath = ""
    curGrubTimeoutStyle = ""
    curGrubTimeout = 0
    with open(envFile, 'r') as fid:
        lines = fid.readlines()
        while lines:
            line = lines.pop(0)
            items = line.split('=',1)
            if len(items) > 1:
                if (items[0] == "GRUB_DEFAULT"):
                    curGrubPath = items[1].rstrip()
                elif (items[0] == "GRUB_CMDLINE_LINUX_DEFAULT"):
                    curGrubCmdLines.insert(0,items[1].rstrip())
                elif (items[0] == "#GRUB_CMDLINE_LINUX_DEFAULT"):
                    cmdStr = items[1].rstrip()
                    if cmdStr != "":
                        curGrubCmdLines.append(cmdStr)
                elif (items[0] == "GRUB_CMDLINE_LINUX"):
                    cmdStr = items[1].rstrip()
                    if cmdStr != "":
                        curGrubCmdLines.append(cmdStr)
                elif (items[0] == "#GRUB_CMDLINE_LINUX"):
                    cmdStr = items[1].rstrip()
                    if cmdStr != "":
                        curGrubCmdLines.append(cmdStr)
                elif (items[0] == "GRUB_TIMEOUT_STYLE"):
                    curGrubTimeoutStyle = items[1].rstrip()
                elif (items[0] == "GRUB_TIMEOUT"):
                    curGrubTimeout = int(items[1].rstrip())
    return curGrubPath, curGrubTimeout, curGrubTimeoutStyle, curGrubCmdLines

def parseBootFile(bootFile):
    # Limitation: only support up to 2 level menu
    # grubMenu: ([type:0=submenu;1=entry;2:submenu_entry, menuLoc(from 1), entryLoc(from 1), str, path])
    # menuLoc and entryLoc are currently not used in selectMenuItem
    grubMenu = []
    with open(bootFile, 'r') as fid:
        lines = fid.readlines()
        while lines:
            curMenuCount = 1
            curEntryCount = 0
            line = lines.pop(0)
            if line.startswith("menuentry"):
                # 1st level entry
                curEntryCount+=1
                items = line.split("'")
                if items[1].startswith("Memory test"):
                    print("Ignoring memory test entries...")
                elif items[1].startswith("UEFI"):
                    print("Ignoring UEFI Firmware entries...")
                else:
                    curEntry = [1, curMenuCount, curEntryCount, items[1], items[3]]
                    grubMenu.extend(curEntry)
            elif line.startswith("submenu"):
                # 1st level submenu
                curMenuCount+=1
                curEntryCount=0
                items = line.split("'")
                curEntry = [0, curMenuCount, curEntryCount, items[1], items[3]]
                grubMenu.extend(curEntry)
            elif line.startswith("	menuentry"):
                # 2nd level entry
                curEntryCount+=1
                items = line.split("'")
                curEntry = [2, curMenuCount, curEntryCount, items[1], items[3]]
                grubMenu.extend(curEntry)
    return grubMenu

def selectMenuItem(grubMenu, curGrubPath, curGrubTimeout, curGrubTimeoutStyle, curGrubCmdLines):
    # Limitation: assume the grubMenu is unchanged and did not verify the actual location
    itemCount = 0
    menuStr = "Default"
    menuPathStr = ""
    entryStr = ""
    entryPathStr = ""
    currItemIdex = -1
    grubStrs = ['dummy']
    grubPaths = ['dummy']
    curPathStr = curGrubPath.strip('"')
    print("\nCurrent grub boot menu structure:")
    for curIndex in range(0,len(grubMenu),5):
        if grubMenu[curIndex] == 0:
            #submenu
            menuStr = grubMenu[curIndex+3]
            menuPathStr = grubMenu[curIndex+4]
            print("+ %s" % menuStr)
        else: 
            itemCount+=1
            entryStr = grubMenu[curIndex+3]
            if grubMenu[curIndex] == 1:
                entryPathStr = grubMenu[curIndex+4]
                if entryPathStr == curPathStr:
                    print("[%d] %s  <= Current setting" % (itemCount, entryStr))
                else:
                    print("[%d] %s" % (itemCount, entryStr))                
            else: # grubMenu[curIndex] == 2:
                entryPathStr = menuPathStr + ">" + grubMenu[curIndex+4]
                if entryPathStr == curPathStr:
                    print("|- [%d] %s  <= Current setting" % (itemCount, entryStr))
                    currItemIdex = itemCount
                else:
                    print("|- [%d] %s" % (itemCount, entryStr))
            grubStrs.append(entryStr)
            grubPaths.append(entryPathStr)
    while True:
        if currItemIdex != -1:
            inputData = input("Please select the index of the boot item [" + str(currItemIdex) + "]: ")
        else:
            inputData = input("Please select the index of the boot item: ")
        intVal=0
        try:
            intVal = int(inputData)
        except ValueError:
            if inputData == "" and currItemIdex != -1:
                intVal = currItemIdex
            else:
                print("The selected index is invalid\n")
                continue
        if intVal < 1 or intVal > itemCount:
            print("The selected index is invalid\n")
            continue
        confirm = input("Please enter Y to confirm the next boot will be: %s [Y]: " % grubStrs[intVal])
        if confirm.lower() == "y" or confirm == "":
            grubPath=grubPaths[intVal]
            grubString=grubStrs[intVal]
            break
    
    print ("\nAvailable GRUB_CMDLINE_LINUX_DEFAULT settings:")
    cmdIndex = 0
    currItemIdex = -1
    for curCmdStr in curGrubCmdLines:
        cmdIndex+=1
        if cmdIndex == 1:
            print("[%d] %s  <= Current setting" % (cmdIndex, curCmdStr.strip("\"")))
            currItemIdex = cmdIndex
        else:
            print("[%d] %s" % (cmdIndex, curCmdStr.strip("\"")))
    cmdIndex+=1
    print("[%d] Input a new GRUB_CMDLINE_LINUX_DEFAULT string" % cmdIndex)
    while True:
        if currItemIdex != -1:
            inputData = input("Please select the index of the CMDLINE string [" + str(currItemIdex) + "]: ")
        else:
            inputData = input("Please select the index of the CMDLINE string: ")
        intVal=0
        try:
            intVal = int(inputData)
        except ValueError:
            if inputData == "" and currItemIdex != -1:
                intVal = currItemIdex
            else:
                print("The selected index is invalid\n")
                continue
        if intVal < 1 or intVal > cmdIndex:
            print("The selected index is invalid\n")
            continue
        if intVal != cmdIndex:
            confirm = input("Please enter Y to confirm the CMDLINE will be: %s [Y]: " % curGrubCmdLines[intVal-1])
            if confirm.lower() == "y" or confirm == "":
                grubGrubCmdLine = curGrubCmdLines[intVal-1]
                break
        else:
            newCmdLineStr = input("Please enter the new CMDLINE: ")
            # make sure the string has quotation marks
            newCmdLineStr = newCmdLineStr.strip("'\"")
            newCmdLineStr = '"' + newCmdLineStr + '"'
            confirm = input("Please enter Y to confirm the CMDLINE will be: %s [Y]: " % newCmdLineStr)
            if confirm.lower() == "y" or confirm == "":
                grubGrubCmdLine = newCmdLineStr
                break

    if curGrubTimeout < minGrubTimeout:
        confirm = input("\n[WARN] Small GRUB_TIMEOUT value %d detected. It will be increase to %d. Enter \"No\" to keep it: " % (curGrubTimeout,minGrubTimeout))
        if confirm.lower() != "no":
            curGrubTimeout = minGrubTimeout
            print("Update GRUB_TIMEOUT to %d" % minGrubTimeout)

    if useGrubMenu:
        if curGrubTimeoutStyle != "menu":
            confirm = input("\n[WARN] GRUB_TIMEOUT_STYLE value %s detected. It will be changed to menu. Enter \"No\" to keep it: " % curGrubTimeoutStyle)
            if confirm.lower() != "no":
                curGrubTimeoutStyle = "menu"
                print("Update GRUB_TIMEOUT_STYLE to menu")
    
    return grubPath, curGrubTimeout, curGrubTimeoutStyle, grubGrubCmdLine, grubString

def patchEnvFile(envFile, tmpEnvFile, grubPath, grubTimeout, grubTimeoutStyle, grubGrubCmdLine, curGrubCmdLines):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    envBakFile = envFile + "." + timestr
    cmd = "sudo mv " + envFile + " " + envBakFile
    ret = os.system(cmd)
    if ret != 0:
        sys.exit("Failed to backup the grub environment setting file %s to %s. Please check the output above." % (envFile, envBakFile))
    print("The current grub environment setting file was renamed as %s" % envBakFile)
    with open(envBakFile, 'r') as fid:
        lines = fid.readlines()
        with open(tmpEnvFile, 'w') as wid:
            while lines:
                line = lines.pop(0)
                if line.startswith("GRUB_DEFAULT"):
                    # write out all collected
                    wid.write("GRUB_DEFAULT=\"%s\"\n" % grubPath)
                    wid.write("GRUB_TIMEOUT_STYLE=%s\n" % grubTimeoutStyle)
                    wid.write("GRUB_TIMEOUT=%s\n" % grubTimeout)
                    wid.write("GRUB_CMDLINE_LINUX_DEFAULT=%s\n" % grubGrubCmdLine)
                    for cmdLine in curGrubCmdLines:
                        if cmdLine != grubGrubCmdLine:
                            wid.write("#GRUB_CMDLINE_LINUX_DEFAULT=%s\n" % cmdLine)
                    wid.write("GRUB_CMDLINE_LINUX=\n")
                elif line.startswith("GRUB_CMDLINE_LINUX_DEFAULT"):
                    continue
                elif line.startswith("#GRUB_CMDLINE_LINUX_DEFAULT"):
                    continue
                elif line.startswith("GRUB_CMDLINE_LINUX"):
                    continue
                elif line.startswith("#GRUB_CMDLINE_LINUX"):
                    continue
                elif line.startswith("GRUB_TIMEOUT_STYLE"):
                    continue
                elif line.startswith("GRUB_TIMEOUT"):
                    continue
                else:
                    wid.write(line)
    cmd = "sudo cp " + tmpEnvFile + " " + envFile
    ret = os.system(cmd)
    if ret != 0:
        sys.exit("Failed to apply the new grub environment settings to %s. Please check the output above." % envFile)
    print("The new grub environment settings was applied to %s" % envFile)
   
    return 0

def detectGrubDevice(tmpMount,grubBootFile,targetDev):
    knownDevNames = []
    diskUUIDList=[uuid for uuid in os.listdir(devDiskUUIDPath) if os.path.islink(os.path.join(devDiskUUIDPath, uuid))]
    devNameUUIDMap={}
    UUIDdevNameMap={}
    grubUUIDBootFileMap = {}

    cmd = ["sudo","blkid"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    lines = result.stdout.decode().split('\n')
    for line in lines:
        items = line.split(' ')
        if len(items) < 2:
            break
        devName = items[0][:-1]
        items=items[1:]
        devSkip = False
        devUUID = ""
        devType = ""
        for item in items:
          entries = item.split('=')
          if entries[0] == "UUID":
            devUUID = entries[1].strip('"')
          elif entries[0] == "TYPE":
            devType = entries[1].strip('"')
            # this is to exclude common flash drives, installation media, and swap partitions
            if devType == "iso9660" or devType == "vfat" or devType == "swap":
              devSkip = True
        if devSkip == False and devUUID != "":
          devNameUUIDMap[devName] = devUUID
          UUIDdevNameMap[devUUID] = devName
    # check for root and boot if no tmpMount
    if grubBootFile == defaultGrubBootFile:
        cmd = ["findmnt", "-n", "--raw", "--evaluate", "--output=source", "/"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        if result.returncode == 0:
            knownDevNames.append(result.stdout.decode().rstrip())
        cmd = ["findmnt", "-n", "--raw", "--evaluate", "--output=source", "/boot"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        if result.returncode == 0:
            knownDevNames.append(result.stdout.decode().rstrip())
    elif tmpMount != 0 and targetDev.startswith('/dev/'):
        knownDevNames.append(targetDev)
    else:
        print("The supplied grub boot setting is a file. The device may not be excluded from the list but harmless.")
    # remove known devices by dev name
    for dev in knownDevNames:
        if dev in devNameUUIDMap:
            diskUUIDList.remove(devNameUUIDMap[dev])
    # prepare the tmp mount point
    if tmpMount == 0:
        cmd = "sudo mkdir -p " + tmpMountPath
        ret = os.system(cmd)
        if ret != 0:
            sys.exit("Failed to create temporarily mount point.")
    elif os.path.ismount(tmpMountPath):
        cmd = "sudo umount " + tmpMountPath
        ret = os.system(cmd)
        if ret != 0:
            print("Failed to unmount temp directory: %s but harmless" % tmpMountPath)
    # look for grub boot config file in the rest of devices
    for uuid in diskUUIDList:
        cmd = "sudo mount " + os.path.join(devDiskUUIDPath,uuid) + " " + tmpMountPath
        ret = os.system(cmd)
        if ret != 0:
            print("Failed to mount target device. Skip device: %s" % os.path.join(devDiskUUIDPath,uuid))
            continue
        grubBootFile = tmpMountPath + "/grub/grub.cfg"
        grubBootFileAlt = tmpMountPath + "/boot/grub/grub.cfg"
        if os.path.isfile(grubBootFile):
            grubUUIDBootFileMap[uuid] = "/grub/grub.cfg"
        elif os.path.isfile(grubBootFileAlt):
            grubUUIDBootFileMap[uuid] = "/boot/grub/grub.cfg"
        cmd = "sudo umount " + tmpMountPath
        ret = os.system(cmd)
        if ret != 0:
            print("Failed to unmount temp directory: %s but harmless" % tmpMountPath)
    return grubUUIDBootFileMap, UUIDdevNameMap

def main(grubBootFile, grubEnvFile):
    tmpMount = 0
    targetDev = ""
    showInfo()
    signal.signal(signal.SIGINT, interruptSignalHandler)
    if verifyRootPermissionAndCacheSudo() != 0:
        sys.exit("You must have root permission to use this tool. Please run with account having sudo permission or the root account.")

    # verify grub-mkconfig, findmnt, blkid
    print("Checking dependencies...")
    cmd = "which grub-mkconfig" + " > /dev/null 2>&1"
    ret = os.system(cmd)
    if ret != 0:
        sys.exit("The required dependency grub-mkconfig was not found in the system.")
    cmd = "which findmnt" + " > /dev/null 2>&1"
    ret = os.system(cmd)
    if ret != 0:
        sys.exit("The required dependency findmnt was not found in the system.")
    cmd = "which blkid" + " > /dev/null 2>&1"
    ret = os.system(cmd)
    if ret != 0:
        sys.exit("The required dependency blkid was not found in the system.")
    
    if grubBootFile.startswith('/dev/'):
        tmpMount = 1
        targetDev = grubBootFile
        cmd = "sudo mkdir -p " + tmpMountPath
        ret = os.system(cmd)
        if ret != 0:
            sys.exit("Failed to create temporarily mount point.")
        if os.path.ismount(tmpMountPath):
            cmd = "sudo umount " + tmpMountPath
            ret = os.system(cmd)
            if ret != 0:
                print("Failed to unmount temp directory: %s but harmless" % tmpMountPath)
        cmd = "sudo mount " + grubBootFile + " " + tmpMountPath
        ret = os.system(cmd)
        if ret != 0:
            sys.exit("Failed to mount target device.")
        grubBootFile = tmpMountPath + "/grub/grub.cfg"
        grubBootFileAlt = tmpMountPath + "/boot/grub/grub.cfg"
        if not os.path.isfile(grubBootFile):
            if not os.path.isfile(grubBootFileAlt):
                cmd = "sudo umount " + tmpMountPath
                ret = os.system(cmd)
                if ret != 0:
                    print("Failed to unmount temp directory: %s but harmless" % tmpMountPath)
                cmd = "sudo rmdir " + tmpMountPath
                ret = os.system(cmd)
                if ret != 0:
                    print("Failed to clean up temp directory: %s but harmless" % tmpMountPath)
                sys.exit("Cannot find existing /grub/grub.conf or /boot/grub/grub.conf in the target device.")
            else:
                grubBootFile = grubBootFileAlt
        print("Configuration will be written to device %s, target file will be %s" % (targetDev,grubBootFile) )
        grupEnvFileAlt = tmpMountPath + "/etc/default/grub"
        if os.path.isfile(grupEnvFileAlt):
            grubEnvFile = grupEnvFileAlt
            print("Environment file is detected on device %s, will use %s" % (targetDev,grubEnvFile) )
    print("Use grub files: Boot: %s, Env: %s" % (grubBootFile, grubEnvFile))
    print("Stage 1: Parse grub default environment setting file: %s" % grubEnvFile)
    curGrubPath, curGrubTimeout, curGrubTimeoutStyle, curGrubCmdLines = parseEnvFile(grubEnvFile)
    print("Stage 2: Generate and parse temporarily grub config. Please wait for a while...")
    # generate a bootfile for parsing
    updateBootFile(tmpGrubBootFile, grubEnvFile)
    # parse for the menu entries
    grubMenu = parseBootFile(tmpGrubBootFile)
    print("Stage 3: Select the new boot configuration")
    grubPath, grubTimeout, grubTimeoutStyle, grubGrubCmdLine, grubString = selectMenuItem(grubMenu, curGrubPath, curGrubTimeout, curGrubTimeoutStyle, curGrubCmdLines)
    print("Stage 4: Generate the new environment setting file")
    ret = patchEnvFile(grubEnvFile, tmpEnvFile, grubPath, grubTimeout, grubTimeoutStyle, grubGrubCmdLine, curGrubCmdLines)
    print("Stage 5: Generate the new grub configuration file")
    updateBootFile(grubBootFile, grubEnvFile)
    print("Stage 6: Detect and generate the new grub configuration file for other boot drives")
    cmd = "sudo cp " + grubEnvFile + " /tmp/"
    ret = os.system(cmd)
    if ret != 0:
        sys.exit("Failed to create backup environment setting file in temporarily directory.")
    grubUUIDBootFileMap, UUIDdevNameMap = detectGrubDevice(tmpMount, grubBootFile, targetDev)
    if len(grubUUIDBootFileMap) > 0:
        print("\nThe following alternative grub boot configuration files are detected:")
        for uuid,grubFileLocation in grubUUIDBootFileMap.items():
            print("%s: UUID=%s at %s" % (UUIDdevNameMap[uuid], uuid, grubFileLocation))
        confirm = input("Do you want to update those grub boot configuration files [Y]: ")
        if confirm.lower() == "y" or confirm == "":
            for uuid,grubFileLocation in grubUUIDBootFileMap.items():
                print("Updating %s%s..." % (os.path.join(devDiskUUIDPath,uuid), grubFileLocation))
                cmd = "sudo mount " + os.path.join(devDiskUUIDPath,uuid) + " " + tmpMountPath
                ret = os.system(cmd)
                if ret != 0:
                    sys.exit("Failed to mount target device.")
                grubBootFile = tmpMountPath + grubFileLocation
                updateBootFile(grubBootFile, tmpEnvFile)
                cmd = "sudo umount " + tmpMountPath
                ret = os.system(cmd)
                if ret != 0:
                    print("Failed to unmount temp directory: %s but harmless" % tmpMountPath)
    print("\nOn the next reboot, the default kernel will be: %s with CMDLINE: %s" % (grubString, grubGrubCmdLine))
    # clean up
    cmd = "sudo rm " + tmpGrubBootFile
    ret = os.system(cmd)
    if ret != 0:
        print("Failed to clean up temp file: %s but harmless" % tmpGrubBootFile)
    cmd = "sudo rm " + tmpEnvFile
    ret = os.system(cmd)
    if ret != 0:
        print("Failed to clean up temp file: %s but harmless" % tmpEnvFile)
    if os.path.exists(tmpMountPath):
        if os.path.ismount(tmpMountPath):
            cmd = "sudo umount " + tmpMountPath
            ret = os.system(cmd)
            if ret != 0:
                print("Failed to unmount temp directory: %s but harmless" % tmpMountPath)
        cmd = "sudo rmdir " + tmpMountPath
        ret = os.system(cmd)        
        if ret != 0:
             print("Failed to clean up temp directory: %s but harmless" % tmpMountPath)
    return 0

if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1].endswith(".conf") or sys.argv[1].startswith("/dev/"):
            defaultGrubBootFile = sys.argv[1]
        else:
            defaultGrubEnvFile = sys.argv[1]
        print("Override the default grub files: Boot: %s, Env: %s" % (defaultGrubBootFile, defaultGrubEnvFile))
    if len(sys.argv) == 3:
        defaultGrubBootFile = sys.argv[1]
        defaultGrubEnvFile = sys.argv[2]
        print("Override the default grub files: Boot: %s, Env: %s" % (defaultGrubBootFile, defaultGrubEnvFile))
    if not defaultGrubBootFile.startswith("/dev/") and (not os.path.isfile(defaultGrubBootFile) or not os.path.isfile(defaultGrubEnvFile)):
        sys.stderr.write("Unable to detect the grub setting files: {} {}\n".format(defaultGrubBootFile, defaultGrubEnvFile))
        sys.stderr.write("USAGE: {} <GrubBootSettingFile or BootDevPath or GrubDefaultEnvironmentSettingFile> <GrubDefaultEnvironmentSettingFile>\n".format(sys.argv[0]))
        sys.exit(1)
    main(defaultGrubBootFile, defaultGrubEnvFile)


