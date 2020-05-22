import time
import struct
import binascii
from os import sys

if sys.version_info[0] < 3:
    PY_VERSION = 2
else:
    PY_VERSION = 3

try:
    from pyftdi import spi
    SPI_DEVICE = "FTDI"
    # Configure FTDI PORT A or PORT B here:
    # Port A: ftdi://ftdi:2232h/1
    # Port B: ftdi://ftdi:2232h/2
    FTDI_ID = 'ftdi://ftdi:2232h/2'
except:
    try:
        import spidev
        SPI_DEVICE = "RASPI"
    except :
        print("** Error importing SPI interface. Need spidev on RASPI (python 2.7) or pyftdi (python 3) on X86 **")
        SPI_DEVICE = "ERROR"
        sys.exit()



class _spi():

    def __init__(self, bus=0, device=0, speed=1e6):
        if SPI_DEVICE is "RASPI":
            self.device = spidev.SpiDev()
            self.device.open(bus, device)
            self.device.max_speed_hz = speed
            self.xfer = self.device.xfer

        elif SPI_DEVICE is "FTDI":
            self.device = spi.SpiController()
            self.device.configure(FTDI_ID)
            self.slave = self.device.get_port(cs=0, freq=speed, mode=0)
            self.xfer = self.ftdi_xfer
            print("Conected to FTDI SPI %s" %FTDI_ID)
        else:
            self.device = None            
            self.xfer = None

    def ftdi_xfer(self, xfert_data):
        data = bytearray(bytes(xfert_data))
        # print('TxData: %r' %data)
        read_buf = self.slave.exchange(data, duplex=True)
        # print('RxData: %r' %read_buf)
        return read_buf


"""
Hardware interface layer:
This class defines basic access commands to the PN5180 as specified 
in the NXP-PN5180A0xx/C1/C2 Datasheet
"""
class PN5180_HIL(object):
    # Commands Details
    # NXP-PN5180A0xx/C1/C2 Datasheet
    CMD = {
        'WRITE_REGISTER':0x00,           # Write one 32bit register value
        'WRITE_REGISTER_OR_MASK':0x01,   # Sets one 32bit register value using a 32 bit OR mask
        'WRITE_REGISTER_AND_MASK':0x02,  # Sets one 32bit register value using a 32 bit AND mask
        'WRITE_REGISTER_MULTIPLE':0x03,  # Processes an array of register addresses in random order and performs the defined action on these addresses.
        'READ_REGISTER':0x04,            # Reads one 32bit register value
        'READ_REGISTER_MULTIPLE':0x05,   # Reads from an array of max.18 register addresses in random order
        'WRITE_EEPROM':0x06,             # Processes an array of EEPROM addresses in random order and writes the value to these addresses
        'READ_EEPROM':0x07,              # Processes an array of EEPROM addresses from a start address and reads the values from these addresses
        'WRITE_TX_DATA':0x08,            # This instruction is used to write data into the transmission buffer
        'SEND_DATA':0x09,                # This instruction is used to write data into the transmission buffer, the START_SEND bit is automatically set.
        'READ_DATA':0x0A,                # This instruction is used to read data from reception buffer, after successful reception.
        'SWITCH_MODE':0x0B,              # This instruction is used to switch the mode. It is only possible to switch from NormalMode to standby, LPCD or Autocoll
        'MIFARE_AUTHENTICATE':0x0C,      # This instruction is used to perform a MIFARE Classic Authentication on an activated card.
        'EPC_INVENTORY':0x0D,            # This instruction is used to perform an inventory of ISO18000-3M3 tags.
        'EPC_RESUME_INVENTORY':0x0E,     # This instruction is used to resume the inventory algorithm in case it is paused.
        'EPC_RETRIEVE_INVENTORY_RESULT_SIZE':0x0F, # This instruction is used to retrieve the size of the inventory result. 'EPC_RETRIEVE_INVENTORY_RESULT':0x10, This instruction is used to retrieve the result of a preceding EPC_INVENTORY or EPC_RESUME_INVENTORY instruction.
        'LOAD_RF_CONFIG':0x11,           # This instruction is used to load the RF configuration from EEPROM into the configuration registers.
        'UPDATE_RF_CONFIG':0x12,         # This instruction is used to update the RF configuration within EEPROM.
        'RETRIEVE_RF_CONFIG_SIZE':0x13,  # This instruction is used to retrieve the number of registers for a selected RF configuration
        'RETRIEVE_RF_CONFIG':0x14,       # This instruction is used to read out an RF configuration. The register address-value-pairs are available in the response
        'RF_ON':0x16,                    # This instruction switch on the RF Field
        'RF_OFF':0x17,                   # This instruction switch off the RF Field
        'CONFIGURE_TESTBUS_DIGITAL':0x18,# Enables the Digital test bus
        'CONFIGURE_TESTBUS_ANALOG':0x19, # Enables the Analog test bus
    }

    REG_ADDR = {
        'SYSTEM_CONFIG': 0x00,
        'RX_STATUS': 0x13,
        'CRC_TX_CONFIG': 0x19,
        'RF_STATUS': 0x1D
    }

    REGISTER_NAME = {
        0x0: "SYSTEM_CONFIG",
        0x1: "IRQ_ENABLE",
        0x2: "IRQ_STATUS",
        0x3: "IRQ_CLEAR",
        0x4: "TRANSCEIVER_CONFIG",
        0x5: "PADCONFIG",
        0x6: "RFU",
        0x7: "PADOUT",
        0x8: "TIMER0_STATUS",
        0x9: "TIMER1_STATUS",
        0xA: "TIMER2_STATUS",
        0xB: "TIMER0_RELOAD",
        0xC: "TIMER1_RELOAD",
        0xD: "TIMER2_RELOAD",
        0xE: "TIMER0_CONFIG",
        0xF: "TIMER1_CONFIG",
        0x10: "TIMER2_CONFIG",
        0x11: "RX_WAIT_CONFIG",
        0x12: "CRC_RX_CONFIG",
        0x13: "RX_STATUS",
        0x14: "TX_UNDERSHOOT_CONFIG",
        0x15: "TX_OVERSHOOT_CONFIG",
        0x16: "TX_DATA_MOD",
        0x17: "TX_WAIT_CONFIG",
        0x18: "TX_CONFIG",
        0x19: "CRC_TX_CONFIG",
        0x1A: "SIGPRO_CONFIG",
        0x1B: "SIGPRO_CM_CONFIG",
        0x1C: "SIGPRO_RM_CONFIG",
        0x1D: "RF_STATUS",
        0x1E: "AGC_CONFIG",
        0x1F: "AGC_VALUE",
        0x20: "RF_CONTROL_TX",
        0x21: "RF_CONTROL_TX_CLK",
        0x22: "RF_CONTROL_RX",
        0x23: "LD_CONTROL",
        0x24: "SYSTEM_STATUS",
        0x25: "TEMP_CONTROL",
        0x26: "CECK_CARD_RESULT",
        0x27: "DPC_CONFIG",
        0x28: "EMD_CONTROL",
        0x29: "ANT_CONTROL",
        0x39: "SIGPRO_RM_CONFIG_EXTENSION"
    }
    
    SYSTEM_CONFIG = {
        'RESET_SET':0x00000100,
        'RESET_CLR':0xFFFFFEFF,
        'START_SEND_SET':0x00000008,
        'START_SEND_CLR':0xFFFFFFF7,
        'COMMAND_CLR':0xFFFFFFF8,
        'COMMAND_IDLE_SET':0x00000000,
        'COMMAND_TRANSCEIVE_SET':0x00000003,
        'COMMAND_KEEP_COMMAND_SET':0x00000004,
        'COMMAND_LOOPBACK_COMMAND_SET':0x00000005,
        'COMMAND_PRBS_SET':0x00000006
    }

    RF_STATUS_TRANSCEIVE_STATE = {
        0 : "IDLE",
        1 : "WAIT_TRANSMIT",
        2 : "TRANSMITTING",
        3 : "WAIT_RECEIVE",
        4 : "WAIT_FOR_DATA",
        5 : "RECEIVING",
        6 : "LOOPBACK",
        7 : "RESERVED"
    }

    RF_CFG = {        
        'TX_ISO_15693_ASK100':0x0D, # 26 kbps
        'RX_ISO_15693_26KBPS':0x8D, # 26 kbps
        'TX_ISO_15693_ASK10':0x0E,  # 26 kbps
        'RX_ISO_15693_53KBPS':0x8E  # 53 kbps
    }

    EEPROM_ADDR = {
        'DIE_IDENTIFIER':0x00,      # Size: 16 bytes
        'PRODUCT_VERSION':0x10,     # Size: 2 bytes
        'FIRMWARE_VERSION':0x12,    # Size: 2 bytes
        'EEPROM_VERSION':0x14       # Size: 2 bytes
    }

    """
    Debug values : PN5180_HIL, PN5180
    """
    def __init__(self, bus=0, device=0, speed=50000, debug="PN5180_HIL"):
        try:
            self.debug = debug
            self.spi = _spi(bus, device, speed)

        except IOError as exc:
            print("Error opening SPI device : %r" %exc)
            sys.exit()


    def _usDelay(self, useconds):
        time.sleep(useconds / 1000000.0)


    def _getResponse(self, responseLen):
        # Send 0xFF bytes to get response bytes if any
        if responseLen != 0:
            return self.spi.xfer([0xff]*responseLen)
        else:
            return []


    def _sendCommand(self, cmd, parameters, responseLen=0):
        # Send [cmd][parametes]
        # print('Sending parameters %r' %parameters)
        parameters.insert(0, cmd)
        dir(self.spi)
        self.spi.xfer(parameters)
        if self.debug is 'PN5180_HIL':
            print("SPI send frame: %r" %(parameters))
        self._usDelay(5000) # TODO : Manage busy signal instead of hard sleep
        return self._getResponse(responseLen)


    # FIXME: python2/3 support, better way ?   
    def _toList(self, num32):
        if PY_VERSION == 2:
            return map(ord,list(struct.pack("<I", num32)))
        else:
            return list(struct.pack("<I", num32))


    # FIXME: python2/3 support, better way ?
    def _toInt32(self, byte_list):
        if PY_VERSION == 2:
            return struct.unpack("<I","".join(map(chr,byte_list)))[0]
        else :
            return struct.unpack("<I",bytes(byte_list))[0]


    # FIXME: python2/3 support, better way ?
    def _toInt16(self, byte_list):
        if PY_VERSION == 2:
            return struct.unpack("<H","".join(map(chr,byte_list)))[0]
        else :
            return struct.unpack("<H",bytes(byte_list))[0]


    # FIXME: python2/3 support, better way ?
    def _toHex(self, byte_list):
        if PY_VERSION == 2:
            return binascii.hexlify("".join(map(chr,byte_list)))
        else :
            return binascii.hexlify(bytes(byte_list))


    """
    writeRegister(self, address, content)
    address  : 1 byte, Register address 
    content  : 4 bytes, write a 32-bit value (little endian) to a configuration register.
    response : -
    """
    def writeRegister(self, address, content):
        parameters = []
        parameters.insert(0, address)
        if type(content) is str:
            contentList = list(binascii.unhexlify(content))
            parameters.extend(contentList.reverse())
        elif type(content) is int:
            listBytes = list(struct.pack("<I", content))
            parameters.extend(map(ord,listBytes))
        if self.debug is "PN5180_HIL":
            print("WriteReg: %r <=> %r" %(parameters, content))
        return self._sendCommand(self.CMD['WRITE_REGISTER'], parameters, 0)


    """
    writeRegisterOrMask(self, address, orMask)
    address  : 1 byte, Register address 
    orMask   : 4 bytes, 32-bit OR mask (little endian).
    response : -
    """
    def writeRegisterOrMask(self, address, orMask):
        parameters = []
        parameters.insert(0, address)
        parameters = parameters + self._toList(orMask)
        return self._sendCommand(self.CMD['WRITE_REGISTER_OR_MASK'], parameters, 0)


    """
    writeRegisterAndMask(self, address, andMask)
    address  : 1 byte, Register address 
    andMask  : 4 bytes, 32-bit AND mask (little endian).
    response : -
    """
    def writeRegisterAndMask(self, address, andMask):
        parameters = []
        parameters.insert(0, address)
        parameters = parameters + self._toList(andMask)
        return self._sendCommand(self.CMD['WRITE_REGISTER_AND_MASK'], parameters, 0)


    """
    writeRegisterMultiple(self, address, parameter)
    address  : 1 byte, Register address 
    parameter: Array of up to 42 elements [address, action, content]    
                address: 1 byte
                action : 1 byte (0x01 WRITE_REGISTER, 0x02 WRITE_REGISTER_OR_MASK, 0x03 WRITE_REGISTER_AND_MASK)
                content: 4 bytes, register content
    response : -
    """
    def writeRegisterMultiple(self, address, parameterList):
        parameters = []
        parameters.insert(0, address)
        for param in parameterList:
            parameters.extend(param[0])
            parameters.extend(param[1])
            parameters.extend(self._toList(param[2]))

        return self._sendCommand(self.CMD['WRITE_REGISTER_AND_MASK'], parameters, 0)

    """
    readRegister(self, address)
    address  : 1 byte, Register address 
    response : 4 bytes, register content 32-bit value (little endian).
    """
    def readRegister(self, address):
        parameters = []
        parameters.insert(0, address)
        regList = self._sendCommand(self.CMD['READ_REGISTER'], parameters, 4)
        return self._toInt32(regList)


    """
    readRegisterMultiple(self, addressList)
    addressList : 1 to 18 bytes, Register address list
    response : 4 to 72 bytes, register content 32-bit value (little endian).
    """
    def readRegisterMultiple(self, addressList):
        parameters = []
        for param in addressList:
            parameters.extend(param)
        return self._sendCommand(self.CMD['READ_REGISTER_MULTIPLE'], parameters, 4*len(addressList))


    """
    TODO
    writeEeprom(self)
    """
    # def readEeprom(self, address, length):
    #     parameters = []
    #     parameters.insert(0, address)
    #     parameters.insert(1, length)
    #     return self._sendCommand(self.CMD['READ_EEPROM'], parameters, length)


    """
    readEeprom(self, address, length)
    After this instruction has been executed, an RF transmission can be started by configuring the corresponding registers
    Address: 1 byte, Address in EEPROM from which read operation starts (EEPROM Address) 
    length : 1 byte, Number of bytes to read from EEPROM
    """
    def readEeprom(self, address, length):
        parameters = []
        parameters.insert(0, address)
        parameters.insert(1, length)
        return self._sendCommand(self.CMD['READ_EEPROM'], parameters, length)


    """
    writeData(self, parameterList)
    parameterList: 1 to 260 bytes, data to transmit (written to transmit buffer)
    response : -
    """
    def writeData(self, parameterList):
        parameters = []
        for param in parameterList:
            parameters.extend(param)
        return self._sendCommand(self.CMD['WRITE_DATA'], parameters, 0)


    """
    sendData(self, numberOfValidBits, parameterList)
    numberOfValidBits : 1 byte, Number of valid bits in last Byte
    parameterList: 1 to 260 bytes, data to transmit (written to transmit buffer)
    response : -
    """
    def sendData(self, numberOfValidBits, parameterList):
        parameters = []
        parameters.insert(0, numberOfValidBits)
        for param in parameterList:
            parameters.append(param)
        return self._sendCommand(self.CMD['SEND_DATA'], parameters, 0)


    """
    readData(self, len)
    len : 1 to 508 bytes
    response : 1 to 508 bytes read from Rx buffer
    """
    def readData(self, len):
        parameters = []
        parameters.insert(0, 0)
        return self._sendCommand(self.CMD['READ_DATA'], parameters, len)


    """
    switchMode(self)
    TODO 
    response : -
    """
    # def switchMode(self):
    #     parameters = []
    #     parameters.insert(0, 0)
    #     return self._sendCommand(self.CMD['READ_DATA'], parameters, 0)


    """
    loadRfConfig(self, txCfg, rxCfg)
    This instruction is used to load the RF configuration from EEPROM into the configuration registers.
    txCfg : 1 byte, Transmitter configuration byte
    rxCfg : 1 byte, receiver configuration byte
    response : -
    """
    def loadRfConfig(self, txCfg, rxCfg):
        parameters = []
        parameters.insert(0, txCfg)
        parameters.insert(1, rxCfg)
        return self._sendCommand(self.CMD['LOAD_RF_CONFIG'], parameters, 0)


    """
    rfOn(self, ctrl)
    ctrl : 1 byte, 
        Bit0 == 1: disable collision avoidance according to ISO/IEC 18092
        Bit1 == 1: Use Active Communication mode according to ISO/IEC 18092
    response : -
    """
    def rfOn(self, ctrl):
        parameters = []
        parameters.insert(0, ctrl)
        return self._sendCommand(self.CMD['RF_ON'], parameters, 0)


    """
    rfOff(self)
    response : -
    """
    def rfOff(self):
        parameters = []
        parameters.insert(0, 0)
        return self._sendCommand(self.CMD['RF_OFF'], parameters, 0)

