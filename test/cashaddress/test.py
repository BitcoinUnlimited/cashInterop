#!/usr/bin/env python3
# Copyright (c) 2018 oskyk/cashaddress
# Copyright (c) 2015-2018 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
try:
    import convert
except ImportError:
    raise ImportError("\nPlease download and pip3 install package base58-0.2.5-py3-none-any.whl (see steps from cachaddress/convert.py)")

import unittest

class TestConversion(unittest.TestCase):
    def test_to_legacy_p2sh(self):
        self.assertEqual(convert.to_legacy_address('3CWFddi6m4ndiGyKqzYvsFYagqDLPVMTzC'),
                         '3CWFddi6m4ndiGyKqzYvsFYagqDLPVMTzC')
        self.assertEqual(convert.to_legacy_address('bitcoincash:ppm2qsznhks23z7629mms6s4cwef74vcwvn0h829pq'),
                         '3CWFddi6m4ndiGyKqzYvsFYagqDLPVMTzC')

    def test_to_legacy_p2pkh(self):
        self.assertEqual(convert.to_legacy_address('155fzsEBHy9Ri2bMQ8uuuR3tv1YzcDywd4'),
                         '155fzsEBHy9Ri2bMQ8uuuR3tv1YzcDywd4')
        self.assertEqual(convert.to_legacy_address('bitcoincash:qqkv9wr69ry2p9l53lxp635va4h86wv435995w8p2h'),
                         '155fzsEBHy9Ri2bMQ8uuuR3tv1YzcDywd4')

    def test_to_cash_p2sh(self):
        self.assertEqual(convert.to_cash_address('3CWFddi6m4ndiGyKqzYvsFYagqDLPVMTzC'),
                         'bitcoincash:ppm2qsznhks23z7629mms6s4cwef74vcwvn0h829pq')
        self.assertEqual(convert.to_cash_address('bitcoincash:ppm2qsznhks23z7629mms6s4cwef74vcwvn0h829pq'),
                         'bitcoincash:ppm2qsznhks23z7629mms6s4cwef74vcwvn0h829pq')

    def test_to_cash_p2pkh(self):
        self.assertEqual(convert.to_cash_address('155fzsEBHy9Ri2bMQ8uuuR3tv1YzcDywd4'),
                         'bitcoincash:qqkv9wr69ry2p9l53lxp635va4h86wv435995w8p2h')
        self.assertEqual(convert.to_cash_address('bitcoincash:qqkv9wr69ry2p9l53lxp635va4h86wv435995w8p2h'),
                         'bitcoincash:qqkv9wr69ry2p9l53lxp635va4h86wv435995w8p2h')

    def test_to_legacy_p2sh_regtest(self):
        self.assertEqual(convert.to_legacy_address('mxdyGMESdXzVNyiZM4UnSKQRQsXxD8HfXp'),
                         'mxdyGMESdXzVNyiZM4UnSKQRQsXxD8HfXp')
        self.assertEqual(convert.to_legacy_address('bchreg:qzaumhpmnjuwq8kjcp866jmvj9zal7tpcsrcj8gsat'),
                         'mxdyGMESdXzVNyiZM4UnSKQRQsXxD8HfXp')

    def test_to_legacy_p2pkh_regtest(self):
        self.assertEqual(convert.to_legacy_address('msZxBtBX9v9KtrUFQvbQKgxTzfNhcPzhuK'),
                         'msZxBtBX9v9KtrUFQvbQKgxTzfNhcPzhuK')
        self.assertEqual(convert.to_legacy_address('bchreg:qzzr92epddgg5m8pu8strq32ek7aj50rsuvx2rejf9'),
                         'msZxBtBX9v9KtrUFQvbQKgxTzfNhcPzhuK')

    def test_to_cash_p2sh_regtest(self):
        self.assertEqual(convert.to_cash_address('mfobxivZQPZ675fzd25VWU2JEM6w8yFUyn'),
                         'bchreg:qqpjvxg4gagz7j9mczyj2cvm0tsw4hdg5yjpu7jx08')
        self.assertEqual(convert.to_cash_address('bchreg:qqpjvxg4gagz7j9mczyj2cvm0tsw4hdg5yjpu7jx08'),
                         'bchreg:qqpjvxg4gagz7j9mczyj2cvm0tsw4hdg5yjpu7jx08')

    def test_to_cash_p2pkh_regtest(self):
        self.assertEqual(convert.to_cash_address('myBLa9Fc8oPpr3f2sVrBgt54oJmpJgzNRj'),
                         'bchreg:qrqmez5xq2eflsemd3davcn33jqa3er7vsu49r2qvf')
        self.assertEqual(convert.to_cash_address('bchreg:qrqmez5xq2eflsemd3davcn33jqa3er7vsu49r2qvf'),
                         'bchreg:qrqmez5xq2eflsemd3davcn33jqa3er7vsu49r2qvf')

if __name__ == '__main__':
    unittest.main()
