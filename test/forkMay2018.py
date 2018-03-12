#!/usr/bin/env python3
# Copyright (c) 2018 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
import os
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(dir_path, "..")

import pdb
import binascii
import time
import math
import json
import logging
logging.basicConfig(format='%(asctime)s.%(levelname)s: %(message)s', level=logging.INFO)

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from test_framework.blocktools import *
from interopUtils import *
import interopNodes

def verify_chain_tip(self, nodeId):
    """
    Verify the main chain of all know tips in the block tree
        branchlen = 0  (numeric) zero for main chain
        status = active
    Input:
        nodeId - index of the client in the self.nodes[] list
    """
    tips = self.nodes[nodeId].getchaintips()
    logging.info(len(tips))
    logging.info(tips)
    assert_equal(tips[0]['branchlen'], 0)
    assert_equal(tips[0]['status'], 'active')


class ForkMay2018(BitcoinTestFramework):
    def __init__(self, build_variant, client_dirs, bitcoinConfDict):
        BitcoinTestFramework.__init__(self)
        self.buildVariant = build_variant
        self.clientDirs = client_dirs
        self.bins = [ os.path.join(base_dir, x, self.buildVariant, "src","bitcoind") for x in clientDirs]
        self.forkTime = int(time.time())
        self.conf = { "forkMay2018time": self.forkTime, "acceptnonstdtxn": 0, "relaypriority": 0 }
        self.conf.update(bitcoinConfDict)
        logging.info(self.bins)

    def setup_network(self, split=False):
        logging.info(self.bins)

        self.nodes = interopNodes.start(self.options.tmpdir, clientDirs, self.bins, self.conf)

        for n in self.nodes:
            n.setmocktime(self.forkTime-10)

        # Connect each node to the other
        connect_nodes_bi(self.nodes,0,1)
        connect_nodes_bi(self.nodes,0,2)
        connect_nodes_bi(self.nodes,0,3)
        connect_nodes_bi(self.nodes,1,2)
        connect_nodes_bi(self.nodes,1,3)
        connect_nodes_bi(self.nodes,2,3)

        self.is_network_split=False
        self.sync_all()

    def run_test(self):
        self.preTestOpReturn()
        self.initiateFork()
        self.testOpReturn()
        reporter.display_report()

    def initiateFork(self):
        for n in self.nodes:
            n.setmocktime(self.forkTime+10)
        self.nodes[0].generate(20)
        self.sync_blocks()


    def generateTx(self, node, addrs, data=None):
        FEE = decimal.Decimal("0.0001")
        wallet = node.listunspent()
        wallet.sort(key=lambda x: x["amount"], reverse=False)

        size = 0
        count = 0
        decContext = decimal.getcontext().prec
        decimal.getcontext().prec = 8 + 8  # 8 digits to get to 21million, and each bitcoin is 100 million satoshis

        count += 1
        utxo = wallet.pop()
        outp = {}
        if 1:
            payamt = satoshi_round((utxo["amount"]-FEE) / decimal.Decimal(len(addrs)))
            for x in range(0, len(addrs)):
                # its test code, I don't care if rounding error is folded into the fee
                outp[addrs[x]] = payamt
            if data:
                outp["data"] = data
            txn = createrawtransaction([utxo], outp, p2pkh)
            #txn = createrawtransaction([utxo], outp, createWastefulOutput)
            signedtxn = node.signrawtransaction(txn)
            size += len(binascii.unhexlify(signedtxn["hex"]))
            node.sendrawtransaction(signedtxn["hex"])
        decimal.getcontext().prec = decContext
        return signedtxn

    @assert_capture()
    def preTestOpReturn(self):
        cnxns = [ x.getconnectioncount() for x in self.nodes]
        addrsbch = [ x.getnewaddress() for x in self.nodes]
        addrs = [ self.nodes[0].getaddressforms(x)["legacy"] for x in addrsbch]  # TODO handle bitcoincash addrs in python
        for n in self.nodes:
            try:
                tx = self.generateTx(n, addrs, hexlify(("*"*200).encode("utf-8")))
                assert 0, "%s: 200 byte OP_RETURN accepted before the fork" % n.clientName
            except JSONRPCException as e:
                pass
        time.sleep(5) # wait for tx to sync
        mp = [ x.getmempoolinfo()["size"] for x in self.nodes]
        print("memory pools are %s" % str(mp))
        assert mp == [0,0,0,0]
        assert [ x.getconnectioncount() for x in self.nodes] == cnxns # make sure nobody dropped or banned

    @assert_capture()
    def testOpReturn(self):
        cnxns = [ x.getconnectioncount() for x in self.nodes]
        addrsbch = [ x.getnewaddress() for x in self.nodes]
        addrs = [ self.nodes[0].getaddressforms(x)["legacy"] for x in addrsbch]  # TODO handle bitcoincash addrs in python
        count=1
        for n in self.nodes:
            # tx = self.generateTx(n, addrs, hexlify(("*"*2).encode("utf-8")))
            tx = self.generateTx(n, addrs)
            mp = [0]*4
            tries = 10
            while mp != [count]*4 and tries > 0:
                tries -= 1
                time.sleep(1) # wait for tx to sync
                mp = [ x.getmempoolinfo()["size"] for x in self.nodes]
            print("memory pools are %s" % str(mp))
            assert mp == [count]*4, "transaction was not relayed to all nodes %s" % str(mp)
            assert [ x.getconnectioncount() for x in self.nodes] == cnxns # make sure nobody dropped or banned
            count += 1


def Test():
    bitcoinConf = {
        "debug": ["all"],
        "blockprioritysize": 2000000  # we don't want any transactions rejected due to insufficient fees...
    }
    t = ForkMay2018("debug", clientDirs, bitcoinConf)
    t.drop_to_pdb = True
    # folder to store bitcoin runtime data and logs
    tmpdir = "--tmpdir=/ramdisk/cashInterop"

    for arg in sys.argv[1:]:
        if "--tmpdir=" in arg:
            tmpdir = str(arg)
            logging.info("# User input : %s" %tmpdir)

    t.main([tmpdir])

if __name__ == "__main__":
    Test()
