#!/usr/bin/env python3
# Copyright (c) 2017 Oskar Hladky 
# Copyright (c) 2018 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""
    Helper file to perform encoding and decoding of cashaddresses
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

    Usages:

    from cashaddress import convert

    # Exampe 1: using regtest
    # Note: supply the 2nd argument when using regtest
    bitcoinAddress =  'mxdyGMESdXzVNyiZM4UnSKQRQsXxD8HfXp'
    regtest = 1
    convert.to_legacy_address(bitcoinAddress, regtest)

    # Example 2: using testnet
    legacy_p2pkh_testnet =
                convert.to_legacy_address('mqp7vM7eU7Vu9NPH1V7s7pPg5FFBMo6SWK')
    cash_p2sh_testnet =
                convert.to_cash_address('2MwikwR6hoVijCmr1u8UgzFMHFP6rpQyRvP')

    # Example 3: using mainnet
    legacy_p2pkh = convert.to_legacy_address('155fzsEBHy9Ri2bMQ8uuuR3tv1YzcDywd4')
    cash_p2sh = convert.to_cash_address('3CWFddi6m4ndiGyKqzYvsFYagqDLPVMTzC')

    References:
    1. List of address prefixes - https://en.bitcoin.it/wiki/List_of_address_prefixes
    2. Base58Check encoding - https://en.bitcoin.it/wiki/Base58Check_encoding
"""
from base58 import b58decode_check, b58encode_check
import sys
import os
sourcePath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(sourcePath)
from crypto import *

class InvalidAddress(Exception):
    pass

class Address:
    VERSION_MAP = {
        'legacy': [
            ('P2SH', 5, False),
            ('P2PKH', 0, False),
            ('P2SH-TESTNET', 196, True),
            ('P2PKH-TESTNET', 111, True)
        ],
        'cash': [
            ('P2SH', 8, False),
            ('P2PKH', 0, False),
            ('P2SH-TESTNET', 8, True),
            ('P2PKH-TESTNET', 0, True)
        ],
        'legacy_regtest': [
            ('P2SH', 5, False),
            ('P2PKH', 0, False),
            ('P2SH-REGTEST', 196, True),
            ('P2PKH-REGTEST', 111, True)
        ],
        'cash_regtest': [
            ('P2SH', 8, False),
            ('P2PKH', 0, False),
            ('P2SH-REGTEST', 8, True),
            ('P2PKH-REGTEST', 0, True)
        ]
    }
    MAINNET_PREFIX = 'bitcoincash'
    TESTNET_PREFIX = 'bchtest'
    REGTEST_PREFIX = "bchreg"

    def __init__(self, version, payload, prefix=None):
        self.version = version
        self.payload = payload
        #print(">> version, payload, prefix = ", version, payload, prefix)
        if prefix:
            self.prefix = prefix
        else:
            addr_type = 'cash'
            if "REGTEST" in self.version:
                addr_type = 'cash_regtest'

            if Address._address_type(addr_type, self.version)[2]:
                if addr_type == 'cash_regtest':
                    self.prefix = self.REGTEST_PREFIX
                else:
                    self.prefix = self.TESTNET_PREFIX
            else:
                self.prefix = self.MAINNET_PREFIX

    def __str__(self):
        return 'version: {}\npayload: {}\nprefix: {}'.format(self.version, self.payload, self.prefix)

    def legacy_address(self, regtest=0):
        if regtest:
            version_int = Address._address_type('legacy_regtest', self.version)[1]
        else:
            version_int = Address._address_type('legacy', self.version)[1]
        return b58encode_check(Address.code_list_to_string([version_int] + self.payload))

    def cash_address(self, regtest=0):
        if regtest:
            version_int = Address._address_type('cash_regtest', self.version)[1]
        else:
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
    def from_string(address_string, regtest=0):
        try:
            address_string = str(address_string)
        except Exception:
            raise InvalidAddress('Expected string as input')
        if ':' not in address_string:
            return Address._legacy_string(address_string, regtest)
        else:
            return Address._cash_string(address_string, regtest)

    @staticmethod
    def _legacy_string(address_string, regtest=0):
        try:
            decoded = bytearray(b58decode_check(address_string))
        except ValueError:
            raise InvalidAddress('Could not decode legacy address')
        if regtest:
            version = Address._address_type('legacy_regtest', decoded[0])[0]
        else:
            version = Address._address_type('legacy', decoded[0])[0]
        payload = list()
        for letter in decoded[1:]:
            payload.append(letter)
        return Address(version, payload)

    @staticmethod
    def _cash_string(address_string, regtest=0):
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
        if prefix == Address.TESTNET_PREFIX:
            version += '-TESTNET'
        if prefix == Address.REGTEST_PREFIX:
            version += '-REGTEST'
        payload = converted[1:-6]
        return Address(version, payload, prefix)

def to_cash_address(address, regtest=0):
    return Address.from_string(address, regtest).cash_address(regtest)

def to_legacy_address(address, regtest=0):
    return Address.from_string(address, regtest).legacy_address(regtest)

def is_valid(address):
    try:
        Address.from_string(address)
        return True
    except InvalidAddress:
        return False
