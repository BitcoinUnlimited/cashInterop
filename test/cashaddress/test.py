#!/usr/bin/env python3
# Copyright (c) 2017 Oskar Hladky 
# Copyright (c) 2018 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
import convert
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

    def test_to_legacy_p2sh_testnet(self):
        self.assertEqual(convert.to_legacy_address('2MwikwR6hoVijCmr1u8UgzFMHFP6rpQyRvP'),
                         '2MwikwR6hoVijCmr1u8UgzFMHFP6rpQyRvP')
        self.assertEqual(convert.to_legacy_address('bchtest:pqc3tyspqwn95retv5k3c5w4fdq0cxvv95u36gfk00'),
                         '2MwikwR6hoVijCmr1u8UgzFMHFP6rpQyRvP')

    def test_to_legacy_p2pkh_testnet(self):
        self.assertEqual(convert.to_legacy_address('mqp7vM7eU7Vu9NPH1V7s7pPg5FFBMo6SWK'),
                         'mqp7vM7eU7Vu9NPH1V7s7pPg5FFBMo6SWK')
        self.assertEqual(convert.to_legacy_address('bchtest:qpc0qh2xc3tfzsljq79w37zx02kwvzm4gydm222qg8'),
                         'mqp7vM7eU7Vu9NPH1V7s7pPg5FFBMo6SWK')

    def test_to_cash_p2sh_testnet(self):
        self.assertEqual(convert.to_cash_address('2MwikwR6hoVijCmr1u8UgzFMHFP6rpQyRvP'),
                         'bchtest:pqc3tyspqwn95retv5k3c5w4fdq0cxvv95u36gfk00')
        self.assertEqual(convert.to_cash_address('bchtest:pqc3tyspqwn95retv5k3c5w4fdq0cxvv95u36gfk00'),
                         'bchtest:pqc3tyspqwn95retv5k3c5w4fdq0cxvv95u36gfk00')

    def test_to_cash_p2pkh_testnet(self):
        self.assertEqual(convert.to_cash_address('mqp7vM7eU7Vu9NPH1V7s7pPg5FFBMo6SWK'),
                         'bchtest:qpc0qh2xc3tfzsljq79w37zx02kwvzm4gydm222qg8')
        self.assertEqual(convert.to_cash_address('bchtest:qpc0qh2xc3tfzsljq79w37zx02kwvzm4gydm222qg8'),
                         'bchtest:qpc0qh2xc3tfzsljq79w37zx02kwvzm4gydm222qg8')

    def test_to_legacy_p2sh_regtest(self):
        self.assertEqual(convert.to_legacy_address('mxdyGMESdXzVNyiZM4UnSKQRQsXxD8HfXp', 1),
                         'mxdyGMESdXzVNyiZM4UnSKQRQsXxD8HfXp')
        self.assertEqual(convert.to_legacy_address('bchreg:qzaumhpmnjuwq8kjcp866jmvj9zal7tpcsrcj8gsat', 1),
                         'mxdyGMESdXzVNyiZM4UnSKQRQsXxD8HfXp')

    def test_to_legacy_p2pkh_regtest(self):
        self.assertEqual(convert.to_legacy_address('msZxBtBX9v9KtrUFQvbQKgxTzfNhcPzhuK', 1),
                         'msZxBtBX9v9KtrUFQvbQKgxTzfNhcPzhuK')
        self.assertEqual(convert.to_legacy_address('bchreg:qzzr92epddgg5m8pu8strq32ek7aj50rsuvx2rejf9', 1),
                         'msZxBtBX9v9KtrUFQvbQKgxTzfNhcPzhuK')

    def test_to_cash_p2sh_regtest(self):
        self.assertEqual(convert.to_cash_address('mfobxivZQPZ675fzd25VWU2JEM6w8yFUyn', 1),
                         'bchreg:qqpjvxg4gagz7j9mczyj2cvm0tsw4hdg5yjpu7jx08')
        self.assertEqual(convert.to_cash_address('bchreg:qqpjvxg4gagz7j9mczyj2cvm0tsw4hdg5yjpu7jx08', 1),
                         'bchreg:qqpjvxg4gagz7j9mczyj2cvm0tsw4hdg5yjpu7jx08')

    def test_to_cash_p2pkh_regtest(self):
        self.assertEqual(convert.to_cash_address('myBLa9Fc8oPpr3f2sVrBgt54oJmpJgzNRj', 1),
                         'bchreg:qrqmez5xq2eflsemd3davcn33jqa3er7vsu49r2qvf')
        self.assertEqual(convert.to_cash_address('bchreg:qrqmez5xq2eflsemd3davcn33jqa3er7vsu49r2qvf', 1),
                         'bchreg:qrqmez5xq2eflsemd3davcn33jqa3er7vsu49r2qvf')

if __name__ == '__main__':
    unittest.main()
