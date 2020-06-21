from pypn5180.iso_iec_15693 import iso_iec_15693
import time
import os
import errno
import binascii
import argparse
import datetime
import struct
import progressbar


class pbar():
    def __init__(self):
        self.pb = progressbar.ProgressBar().start()

    def updatepb(self, current_block, max_block):
        k = int(100*current_block/max_block)
        self.pb.update(k)

    def finish(self):
        self.pb.finish()


def dumpFRAM(binFile):
    with open(binFile, 'wb') as fid:
        pb = pbar()
        print("destination file: %s" %binFile)
        for k in range(255):
            pb.updatepb(k, 255)
            data, errStr = isoIec15693.readSingleBlockCmd(k)
            if 'OK' in errStr:
                hexdata = bytes(data)
                fid.write(hexdata)
        pb.finish()


def getBlockSecurityStatus():
    for k in range(255):
        status = isoIec15693.getMultipleBlockSecurityStatusCmd(k, 1)
        print("Status: %r" %status)


def displayHelp():
    print("\npypn5180_15693 compatible for RASPBERRY (python2) or on Linux x86 (python3)")
    print("Use NXP 5180 board to implement ISO IEC-15693 RF norm")
    print("\nSupported commands :")
    print("Maintain RF Power On                                                 :  'pypn5180.py POWER'")
    print("Dump a complete FRAM (output file: UUID-Date.dat)                    :  'pypn5180.py DUMP'")
    print("Read NFC block(x)                                                    :  'pypn5180.py READBLK -o x'")
    print("Write NFC block(x) 8 bits data=A1A2A3B4B5B6C7C8                      :  'pypn5180.py WRITEBLK -o x -d A1A2A3B4B5B6C7C8'")
    print("Read Security status block(x)                                        :  'pypn5180.py BLOCKSECURITY -o x'")
    print("Send NFC Proprietary command x, 8 bits data=A1A2A3B4B5B6C7C8         :  'pypn5180.py CUSTOM -c x -d A1A2A3B4B5B6C7C8'\n")


def parseInputs():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=str, default="POWER", help="give test mode: {'DUMP', 'FREEDUMP','CUSTOM', 'POWER', 'READBLK', 'WRITEBLK', 'BLOCKSECURITY'}")
    parser.add_argument("-o", "--blockOffset", type=int, default=0, help="Block offset required for READBLK, WRITEBLK")
    parser.add_argument("-d","--data", type=str, default="", help="Hexlified datablock to write (8 bytes, requred for WRITEBLK, CUSTOM)")
    parser.add_argument("-c", "--custom", type=str, default="A0", help="One hex byte for CUSTOM command code ex: A0")
    parser.add_argument("-m", "--mfCode", type=str, default="07", help="Manufacturer Code ID")
    parser.add_argument("-f", "--ftdi_port", type=str, default="PORT_A", help="FTDI 2232 port 'PORT_A, PORT_B'")
    return parser.parse_args()


if __name__ == "__main__":

    args = parseInputs()

    isoIec15693 = iso_iec_15693(args.ftdi_port)
    sys_info, errStr = isoIec15693.getSystemInformationCmd()
    serial = binascii.hexlify(bytes(sys_info[1:9])).decode('utf-8')
    print('[%s] SysInfo - chip serial: %r' %(errStr, serial))

    if args.mode == "POWER":
        # Maintain RF power on until 'CTRL+C' pressed
        while True:
            time.sleep(1)

    elif args.mode == "DUMP":
        date = ("%s" %datetime.datetime.now()).replace(" ", "-")
        dumpFRAM(serial + date + ".dat")

    elif args.mode == "FREEDUMP":
        date = ("FREE-%s" %datetime.datetime.now()).replace(" ", "-")
        dumpFREE(serial + date + ".dat")

    elif args.mode == "CUSTOM":
        if args.data is not "":
            dataIn = list(binascii.unhexlify(args.data))
        else:
            dataIn = []
        cmdCode = ord(binascii.unhexlify(args.custom))
        mfCode = ord(binascii.unhexlify(args.mfCode))
        print("Sending Code 0x%x with %r" %(cmdCode,dataIn))
        data, errStr  = isoIec15693.customCommand(cmdCode, mfCode, dataIn)
        if "No Answer from tag" not in errStr: 
            print("CMD %x: [%s] Data: [%r] - [%s]" %(cmdCode, errStr, data, binascii.hexlify(data)))
        else:
            print("%s" %errStr)

    elif args.mode == "READBLK":
        data, errStr = isoIec15693.readSingleBlockCmd(args.blockOffset)
        if 'OK' in errStr:
            print("Block: %r / %s" %(data, binascii.hexlify(data)))

    elif args.mode == "WRITEBLK":
        dataToSend = list(binascii.unhexlify(args.data))
        data, errStr = isoIec15693.writeSingleBlockCmd(args.blockOffset, dataToSend)
        print("Write Block: %s" %errStr)

    elif args.mode == "BLOCKSECURITY":
        dataToSend = list(binascii.unhexlify(args.data))
        data, errStr = isoIec15693.getMultipleBlockSecurityStatusCmd(args.blockOffset, 1)
        print("Write Block: %s" %errStr)


    else:
        print("Unknown command")

    isoIec15693.disconnect()
