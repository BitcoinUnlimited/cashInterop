#!/usr/bin/env python3
# Copyright (c) 2015-2018 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""
    Helper file to perform encoding and decoding of cashaddresses
    Implementation is borrowed from github project
    See Reference:
    https://github.com/oskyk/cashaddress
    
    Dependencies:
    - base58
    
    Installations: 
    
    For python3, the steps required are:
    1. download package "base58-0.2.5-py3-none-any.whl" from https://pypi.python.org/pypi/base58
    
    2. If Python pip package manager is not available in your environment, install it with 

        > sudo apt install python3-pip

    3. Install the base58 built-package by

        > pip3 install base58-0.2.5-py3-none-any.whl
"""

from cashaddress.crypto import *
from base58 import b58decode_check, b58encode_check
import sys


class InvalidAddress(Exception):
    pass


class Address:
    VERSION_MAP = {
        'legacy': [
            ('P2SH', 5, False),
            ('P2PKH', 0, False),
            ('P2SH-REGTEST', 196, True),
            ('P2PKH-REGTEST', 111, True)
        ],
        'cash': [
            ('P2SH', 8, False),
            ('P2PKH', 0, False),
            ('P2SH-REGTEST', 8, True),
            ('P2PKH-REGTEST', 0, True)
        ]
    }
    MAINNET_PREFIX = 'bitcoincash'
    REGTEST_PREFIX = "bchreg"

    def __init__(self, version, payload, prefix=None):
        self.version = version
        self.payload = payload
        if prefix:
            self.prefix = prefix
        else:
            if Address._address_type('cash', self.version)[2]:
                self.prefix = self.REGTEST_PREFIX
            else:
                self.prefix = self.MAINNET_PREFIX

    def __str__(self):
        return 'version: {}\npayload: {}\nprefix: {}'.format(self.version, self.payload, self.prefix)

    def legacy_address(self):
        version_int = Address._address_type('legacy', self.version)[1]
        return b58encode_check(Address.code_list_to_string([version_int] + self.payload))

    def cash_address(self):
        version_int = Address._address_type('cash', self.version)[1]
        payload = [version_int] + self.payload
        payload = convertbits(payload, 8, 5)
        checksum = calculate_checksum(self.prefix, payload)
        return self.prefix + ':' + b32encode(payload + checksum)

    @staticmethod
    def code_list_to_string(code_list):
        if sys.version_info > (3, 0):
            output = bytes()
            for code in code_list:
                output += bytes([code])
        else:
            output = ''
            for code in code_list:
                output += chr(code)
        return output

    @staticmethod
    def _address_type(address_type, version):
        for mapping in Address.VERSION_MAP[address_type]:
            if mapping[0] == version or mapping[1] == version:
                return mapping
        raise InvalidAddress('Could not determine address version')

    @staticmethod
    def from_string(address_string):
        try:
            address_string = str(address_string)
        except Exception:
            raise InvalidAddress('Expected string as input')
        if ':' not in address_string:
            return Address._legacy_string(address_string)
        else:
            return Address._cash_string(address_string)

    @staticmethod
    def _legacy_string(address_string):
        try:
            decoded = bytearray(b58decode_check(address_string))
        except ValueError:
            raise InvalidAddress('Could not decode legacy address')
        version = Address._address_type('legacy', decoded[0])[0]
        payload = list()
        for letter in decoded[1:]:
            payload.append(letter)
        return Address(version, payload)

    @staticmethod
    def _cash_string(address_string):
        if address_string.upper() != address_string and address_string.lower() != address_string:
            raise InvalidAddress('Cash address contains uppercase and lowercase characters')
        address_string = address_string.lower()
        if ':' not in address_string:
            address_string = Address.MAINNET_PREFIX + ':' + address_string
        prefix, base32string = address_string.split(':')
        decoded = b32decode(base32string)
        if not verify_checksum(prefix, decoded):
            raise InvalidAddress('Bad cash address checksum')
        converted = convertbits(decoded, 5, 8)
        version = Address._address_type('cash', converted[0])[0]
        if prefix == Address.REGTEST_PREFIX:
            version += '-REGTEST'
        payload = converted[1:-6]
        return Address(version, payload, prefix)

def to_cash_address(address):
    return Address.from_string(address).cash_address()

def to_legacy_address(address):
    return Address.from_string(address).legacy_address()

def is_valid(address):
    try:
        Address.from_string(address)
        return True
    except InvalidAddress:
        return False