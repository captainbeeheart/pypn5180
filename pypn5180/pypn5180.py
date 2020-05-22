import time
import struct
import binascii
from . import pypn5180hal


"""
PN5180 main class providing NFC functions to initialise the chip and send/receive NFC frames.
"""
class PN5180(pypn5180hal.PN5180_HIL):

    RF_ON_MODE={
        'STANDARD':0x00,
        'IEC_18092_COLLISION_DISABLE':0x1,     # disable collision avoidance according to ISO/IEC 18092
        'IEC_18092_ACVTIVE_COMMUNICATION':0x2  # Use Active Communication mode according to ISO/IEC 18092
    }

    MAX_REGISTER_ADDR = 0x29

    """
    getFirmwareVersion(self)
    response : 2 bytes 
    """
    def getFirmwareVersion(self):
        firmwareVersion = self.readEeprom(self.EEPROM_ADDR['FIRMWARE_VERSION'], 2)
        return self._toInt16(firmwareVersion)


    """
    getProductVersion(self)
    response : 2 bytes
    """
    def getProductVersion(self):
        productVersion = self.readEeprom(self.EEPROM_ADDR['PRODUCT_VERSION'], 2)
        return self._toInt16(productVersion)


    """
    getEepromVersion(self)
    response : 2 bytes 
    """
    def getEepromVersion(self):
        eepromVersion = self.readEeprom(self.EEPROM_ADDR['EEPROM_VERSION'], 2)
        return self._toInt16(eepromVersion)

    """
    getDieIdentifier(self)
    response : 2 bytes 
    """
    def getDieIdentifier(self):
        dieIdentifier = self.readEeprom(self.EEPROM_ADDR['DIE_IDENTIFIER'], 16)
        return self._toHex(dieIdentifier)

    """
    selfTest(self)
    Display PN5180 chip versions (HW, SW)
    """
    def selfTest(self):
        # Get firmware version from EEPROM
        firmwareVersion = self.getFirmwareVersion()
        productVersion  = self.getProductVersion()
        eepromVersion   = self.getEepromVersion()
        dieIdentifier   = self.getDieIdentifier()
        print(" Firmware version: %#x" % firmwareVersion)
        print(" Product Version : %#x" % productVersion)
        print(" EEPROM version  : %#x" % eepromVersion)
        print(" Die identifier  : %#r" % dieIdentifier)


    """
    dumpRegisters(self)
    Dumps and display all PN5180 registers
    """
    def dumpRegisters(self):
        print("======= Register Dump =======")
        for addr in range(0, self.MAX_REGISTER_ADDR):
            registerValue = self.readRegister(addr)
            print("%s %#x = %#x (%r)" %(self.REGISTER_NAME[addr], addr, registerValue, bin(registerValue)))
        registerValue = self.readRegister(0x39)
        print("%s %#x = %#x (%r)" %(self.REGISTER_NAME[0x39], 0x39, registerValue, bin(registerValue)))
        print("=============================")


    """
    configureIsoIec15693Mode(self)
    Soft reset, configure default parameters for Iso IEC 15693 and enable RF
    """
    def configureIsoIec15693Mode(self):
        # TODO :
        #   - do a clean interface selector, not hard coded
        #   - Configure CRC registers
        self.softwareReset()

        # RF_CFG = {        
        # 'TX_ISO_15693_ASK100':0x0D, # 26 kbps
        # 'RX_ISO_15693_26KBPS':0x8D, # 26 kbps
        # 'TX_ISO_15693_ASK10':0x0E,  # 26 kbps
        # 'RX_ISO_15693_53KBPS':0x8E  # 53 kbps
        #  }
        self.loadRfConfig(self.RF_CFG['TX_ISO_15693_ASK100'], self.RF_CFG['RX_ISO_15693_26KBPS'])
        self.rfOn(self.RF_ON_MODE["STANDARD"])

        # Set SYSTEM regsiter state machine to transceive
        self.setSystemCommand("COMMAND_IDLE_SET")

    """
    transactionIsoIec15693(cmd)
    Perform RF transaction. Send command to the RFiD device and read device result.
    """
    def transactionIsoIec15693(self, command):
        self.setSystemCommand("COMMAND_TRANSCEIVE_SET")

        # Check RF_STATUS TRANSCEIVE_STATE value
        # must be WAIT_TRANSMIT
        if self.getRfStatusTransceiveState() is not "WAIT_TRANSMIT":
            print("transactionIsoIec15693 Error in RF state: %s" %self.getRfStatusTransceiveState())
            return -1 
        
        self.sendData(8,command)
        self._usDelay(50000) # 50 ms
        nbBytes = self.getRxStatusNbBytesReceived()
        response = self.readData(nbBytes)
        if response:
            flags = response[0]
            data = response[1:]
            # print("Received %d bytes from sensor: [flags]: %x, [data]: %r" %(nbBytes, flags, [hex(x) for x in data]))
        else:
            flags = 0xFF
            data = []

        self.setSystemCommand("COMMAND_IDLE_SET")

        return flags, data


    def getRfStatusTransceiveState(self):
        regvalue = self.readRegister(self.REG_ADDR['RF_STATUS'])
        transceiveState = (regvalue >> 24) & 0x3
        return self.RF_STATUS_TRANSCEIVE_STATE[transceiveState] 


    def getRxStatusNbBytesReceived(self):
        regvalue = self.readRegister(self.REG_ADDR['RX_STATUS'])
        return regvalue & 0x1FF


    def setSystemCommand(self, mode):
        self.writeRegisterAndMask(self.REG_ADDR["SYSTEM_CONFIG"],self.SYSTEM_CONFIG["COMMAND_CLR"])
        self.writeRegisterOrMask(self.REG_ADDR["SYSTEM_CONFIG"],self.SYSTEM_CONFIG[mode])


    def softwareReset(self):
        self.writeRegisterOrMask(self.REG_ADDR["SYSTEM_CONFIG"],self.SYSTEM_CONFIG["RESET_SET"])
        self._usDelay(50000) # 50ms
        self.writeRegisterAndMask(self.REG_ADDR["SYSTEM_CONFIG"],self.SYSTEM_CONFIG["RESET_CLR"])
        self._usDelay(50000) # 50ms
