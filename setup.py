from setuptools import setup, find_packages
setup(
    name="pypn5180",
    version="1.0",
    description="NXP PN5180 python interface using FTDI2232, or directly  connected to a raspberry. This python3 module gives an abstraction layer to control NXP PN8180 and implements the NFC ISO-IEC-15693 specification",
    url="https://github.com/captainbeeheart",
    author = "Captainbeeheart",
    author_email = "captainbeehart@protonmail.com",
    license="GPL v3.0",
    platform="Linux",
    packages=find_packages(),
)
