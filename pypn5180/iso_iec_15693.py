from . import pypn5180
import binascii
import collections
"""
Implementation of ISO-IEC-15693 norm for PN5180 chipset
"""
class iso_iec_15693(object):

    CMD_CODE= {
        'INVENTORY':0x01,
        'STAY_QUIET':0x02,
        'READ_SINGLE_BLOCK':0x20,
        'WRITE_SINGLE_BLOCK':0x21,
        'LOCK_BLOCK':0x22,
        'READ_MULTIPLE_BLOCK':0x23,
        'WRITE_MULTIPLE_BLOCK':0x24,
        'SELECT':0x25,
        'RESET_READY':0x26,
        'WRITE_AFI':0x27,
        'LOCK_AFI':0x28,
        'WRITE_DSFID':0x29,
        'LOCK_DSFID':0x2A,
        'GET_SYSTEM_INFORMATION':0x2B,
        'GET_MULTIPLE_BLOCK_SECURITY_STATUS':0x2C,
        'CUSTOM_READ_SINGLE':0xC0,
        'CUSTOM_WRITE_SINGLE':0xC1,
        'CUSTOM_LOCK_BLOCK':0xC2,
        'CUSTOM_READ_MULTIPLE':0xC3,
        'CUSTOM_WRITE_MULTIPLE':0xC4,
    }

    ERROR_CODE = {
        0x00:'ERROR CODE ZERO',
        0x01:'The command is not supported, i.e. the request code is not recognised.',
        0x02:'The command is not recognised, for example: a format error occurred.',
        0x03:'The option is not supported.',
        0x0F:'Unknown error.',
        0x10:'The specified block is not available (doesn t exist).',
        0x11:'The specified block is already -locked and thus cannot be locked again',
        0x12:'The specified block is locked and its content cannot be changed.',
        0x13:'The specified block was not successfully programmed.',
        0x14:'The specified block was not successfully locked',
        0xA7:'CUSTOM ERROR 0xA7'
    }
    # Avoid unhandled error codes crash:
    ERROR_CODE = collections.defaultdict(lambda:0,ERROR_CODE)

    def __init__(self):
        print("Connecting to PN5180 device...")
        self.pn5180 = pypn5180.PN5180(debug="PN5180")
        print("PN5180 Self test:")
        self.pn5180.selfTest()
        print("\nConfiguring device for ISO IEC 15693")
        self.pn5180.configureIsoIec15693Mode()

        # Set default frame flags byte:
        # [Extract From ISO_IEC_15693]
        # Bit 1 Sub-carrier_flag  0 A single sub-carrier frequency shall be used by the VICC
        #                         1 Two sub-carriers shall be used by the VICC
        # Bit 2 Data_rate_flag    0 Low data rate shall be used
        #                         1 High data rate shall be used
        # Bit 3 Inventory_flag    0 Flags 5 to 8 meaning is according to table 4
        #                         1 Flags 5 to 8 meaning is according to table 5
        # Bit 4 Protocol          0 No protocol format extension
        #       Extension_flag    1 Protocol format is extended. Reserved for future use
        self.flags = 0x02

    """
    configureFlags(self, flags)
    Configure the flags byte to be used for next transmissions
    flags: 1 byte, following ISO_IEC_15693 requirements
    """
    def configureFlags(self, flags):
        self.flags = flags

    """
    getError(self, flags, data)
    analyse error code returned by the RFID chip
    """    
    def getError(self, flags, data):
        
        if flags == 0xFF:
            return "Transaction ERROR: No Answer from tag"
        elif flags != 0:
            return "Transaction ERROR: %s" %self.ERROR_CODE[data[0]]
        return "Transaction OK"

    def inventoryCmd(self):
        pass
        # 01h


    def stayQuietCmd(self, uid):
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['STAY_QUIET'])
        frame.extend(uid)


    def readSingleBlockCmd(self, blockNumber, uid=[]):
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['READ_SINGLE_BLOCK'])
        if uid is not []:
            frame.extend(uid)
            # TODO : Add uid bit in flags
        frame.append(blockNumber)
        print("Send frame: %r" %binascii.hexlify(bytes(frame)))
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def disconnect(self):
        self.pn5180.rfOff()


    def writeSingleBlockCmd(self, blockNumber, data, uid=[]):
        #'21'

        if len(data) is not 8:
            print("WARNING, data block length must be 8 bytes")

        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['WRITE_SINGLE_BLOCK'])
        if uid is not []:
            frame.extend(uid)
            # TODO : Add uid bit in flags
        frame.append(blockNumber)
        frame.extend(data)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def lockBlockCmd(self, numberOfBlocks, uid=[]):
        #'22'
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['LOCK_BLOCK'])
        if uid is not []:
            frame.extend(uid)
        frame.extend(numberOfBlocks)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def readMultipleBlocksCmd(self, firstBlockNumber, numberOfBlocks, uid=[]):
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['READ_MULTIPLE_BLOCKS'])
        if uid is not []:
            frame.extend(uid)
        frame.extend(firstBlockNumber)
        frame.extend(numberOfBlocks)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error

    def writeMultipleBlocksCmd(self):
        pass
        #'24'

    def selectCmd(self, uid):
        #'25'
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['SELECT'])
        frame.extend(uid)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def resetToReadyCmd(self, uid=[]):
        #'26'
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['RESET_READY'])
        if uid is not []:
            frame.extend(uid)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def writeAfiCmd(self, afi, uid=[]):
        #27'
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['WRITE_AFI'])
        if uid is not []:
            frame.extend(uid)
        frame.extend(afi)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def lockAfiCmd(self, uid=[]):
        #'28'
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['LOCK_AFI'])
        if uid is not []:
            frame.extend(uid)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def writeDsfidCmd(self, dsfid, uid=[]):
        #'29'
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['WRITE_DSFID'])
        if uid is not []:
            frame.extend(uid)
        frame.extend(dsfid)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def locckDsfidCmd(self, uid=[]):
        #'2A'
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['LOCK_DSFID'])
        if uid is not []:
            frame.extend(uid)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def getSystemInformationCmd(self, uid=[]):
        #'2B'
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['GET_SYSTEM_INFORMATION'])
        if uid is not []:
            frame.extend(uid)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def getMultipleBlockSecurityStatusCmd(self, firstBlockNumber, numberOfBlocks, uid=[]):
        #'2C'
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['GET_MULTIPLE_BLOCK_SECURITY_STATUS'])
        if uid is not []:
            frame.extend(uid)
        frame.append(firstBlockNumber)
        frame.append(numberOfBlocks)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error


    def customCommand(self, cmdCode, mfCode, data):
        # 'A0' - 'DF' Custom IC Mfg dependent
        # 'E0' - 'FF' Proprietary IC Mfg dependent
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, cmdCode)
        frame.insert(2, mfCode)
        if data is not []:
            frame.extend(data)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error

    """
    Note: firstBlockNumber: 2 bytes, LSB first
    """
    def customReadSinlge(self, mfCode, firstBlockNumber, uid=[]):
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, self.CMD_CODE['CUSTOM_READ_SINGLE'])
        frame.insert(2, mfCode)
        if uid is not []:
            frame.extend(uid)
        if len(firstBlockNumber) == 1:
            frame.extend(0)
        frame.extend(firstBlockNumber)
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error

    """
    Note: firstBlockNumber: 2 bytes, LSB first
    """
    def customWriteSinlge(self, cmdCode, mfCode, firstBlockNumber, data, uid=[]):
        pass


    def rfuCommand(self, cmdCode, data, uid=[]):
        frame = []
        frame.insert(0, self.flags)
        frame.insert(1, cmdCode)
        frame.extend(map(ord,data))
        flags, data = self.pn5180.transactionIsoIec15693(frame)
        error = self.getError(flags, data)
        return data, error
