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
from test_framework.key import CECKey
from test_framework.script import *
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

def p2sh(btcAddress):
    """ create a pay-to-script-hash script"""
    private_key = CECKey()
    private_key.set_secretbytes(b"helloworld")
    public_key = private_key.get_pubkey()
    redeem_script = CScript([public_key] + [ OP_2DUP, OP_CHECKSIGVERIFY] * 5 + [OP_CHECKSIG])
    redeem_script_hash = hash160(redeem_script)
    p2sh_script = CScript([OP_HASH160, redeem_script_hash, OP_EQUAL])
    return p2sh_script

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

# Comment out setup_chain() to use FW setup, which will build up cache if it does not exist. 
# But Hub is launched using port 8332.
# Have to restart to continue. Hub will be launched using correct port as long as there is a cache folder

#    def setup_chain(self,bitcoinConfDict=None, wallets=None):
#        logging.info("Initializing test directory "+self.options.tmpdir)
#        initialize_chain_clean(self.options.tmpdir, len(self.clientDirs), bitcoinConfDict, wallets)
        

    def setup_network(self, split=False):
        logging.info(self.bins)
        # clean up any running bitcoind
        kill_running_process("bitcoind")
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

        if [i for i in range(len(self.bins)) if BCD_HUB_PATH in self.bins[i]]:
            for n in self.nodes:
                if ("hub" not in n.clientName):
                    n.generate(200)
                    sync_blocks(self.nodes)
            # When Hub is used in clientDirs = ["bucash", "abc", "xt", "hub"] from interopUtils.py
            self.TestHub()

        self.testOpP2SH()
            
        reporter.display_report()

    def initiateFork(self):
        for n in self.nodes:
            n.setmocktime(self.forkTime+10)
        self.nodes[0].generate(20)
        self.sync_blocks()

    def emptyMemPool(self):
        self.nodes[0].generate(1)
        # mempool should be empty, all txns confirmed
        assert_equal(set(self.nodes[0].getrawmempool()), set())

    def verifyExistingTxnMempool(self, n, addrsbch, name="hub", count=4):
        """
        Check the existing txns from sent from other clients
        Call generate on Hub which required public addr as a second argument
        Input:
            n : client that does not have txn sent yet
            addrsbch : bch addresses of all 4 clients
            name : client name is not being verified here
            count : number of txns should be in the mempool from other clients
        """
        if (name in n.clientName):
            # validate txns in mempool from other clients
            mp = [ x.getmempoolinfo()["size"] for x in self.nodes]
            print("memory pools are %s" % str(mp))
            txn_count = count-1
            assert mp == [txn_count, txn_count, txn_count, txn_count], "transaction was not relayed to all nodes %s" % str(mp)

            # only pick up hub addr to use the generate interface which requires public key
            coinbase0 = [x for x in addrsbch if len(x.split(':'))==1]
            pubkey = n.validateaddress(coinbase0[0])['pubkey']
            # generate enough blocks so that hub client node has a balance
            n.generate(200, pubkey) # hub need blocks and public addr
            self.sync_blocks()

            # after mined block and mempool should be cleared
            mp = [ x.getmempoolinfo()["size"] for x in self.nodes]
            print("memory pools are %s" % str(mp))
            assert mp == [0, 0, 0, 0], "transaction was not relayed to all nodes %s" % str(mp)

    def generateTx(self, node, addrs, data=None, script=p2pkh):
        FEE = decimal.Decimal("0.0001")
        wallet = node.listunspent()
        #print("\n wallet = ", wallet[0])
        wallet.sort(key=lambda x: x["amount"], reverse=False)
        size = 0
        count = 0
        decContext = decimal.getcontext().prec
        decimal.getcontext().prec = 8 + 8  # 8 digits to get to 21million, and each bitcoin is 100 million satoshis
        count += 1
        utxo = wallet.pop()
        outp = {}
        payamt = satoshi_round((utxo["amount"]-FEE) / decimal.Decimal(len(addrs)))
        for x in range(0, len(addrs)):
            # its test code, I don't care if rounding error is folded into the fee
            outp[addrs[x]] = payamt
        if data:
            outp["data"] = data
        txn = createrawtransaction([utxo], outp, script)
        signedtxn = node.signrawtransaction(txn)
        size += len(binascii.unhexlify(signedtxn["hex"]))
        #node.sendrawtransaction(signedtxn["hex"])
        try:
            node.sendrawtransaction(signedtxn["hex"])
        except Exception as e:
            print(e)
            assert 0, "%s: sendrawtransaction failed" % node.clientName
        decimal.getcontext().prec = decContext
        return signedtxn

    @assert_capture()
    def TestHub(self):
        cnxns = [ x.getconnectioncount() for x in self.nodes]
        # failed without enable wallet as getnewaddress is in rpcwallet.cpp
        addrsbch = [ x.getnewaddress() for x in self.nodes]
        addrs = [ self.nodes[0].getaddressforms(x)["legacy"] for x in addrsbch]  # TODO handle bitcoincash addrs in python
        #print(addrs)
        count=1
        for n in self.nodes:
            self.verifyExistingTxnMempool(n, addrsbch, "hub", count)
            tx = self.generateTx(n, addrs)
            mp = [0]*4
            tries = 10
            while mp != [count]*4 and tries > 0:
                tries -= 1
                time.sleep(2) # wait for tx to sync
                try:
                    mp = [ x.getmempoolinfo()["size"] for x in self.nodes]
                except Exception as e:
                    #print(e)
                    pass
            print("memory pools are %s" % str(mp))
            assert [ x.getconnectioncount() for x in self.nodes] == cnxns # make sure nobody dropped or banned
            count += 1
        #only one txn of client Hub left in the mempool
        mp = [ x.getmempoolinfo()["size"] for x in self.nodes]
        print("memory pools are %s" % str(mp))
        assert mp == [1, 1, 1, 1], "transaction was not relayed to all nodes %s" % str(mp)
        node = self.nodes[0]
        node.generate(2)
        sync_blocks(self.nodes)
        mp = [ x.getmempoolinfo()["size"] for x in self.nodes]
        print("memory pools are %s" % str(mp))
        assert mp == [0,0,0,0], "transaction was not relayed to all nodes %s" % str(mp)

    @assert_capture()
    def testOpP2SH(self):
        cnxns = [ x.getconnectioncount() for x in self.nodes]
        addrsbch = [ x.getnewaddress() for x in self.nodes]
        addrs = [ self.nodes[0].getaddressforms(x)["legacy"] for x in addrsbch]  # TODO handle bitcoincash addrs in python
        count=1
        #clean up mempool before testing
        self.emptyMemPool()
        # for each node: create a txn that spends to that P2SH.
        for n in self.nodes:
            tx = self.generateTx(n, addrs, hexlify(("*"*2).encode("utf-8")), p2sh)  #p2sh
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
        # mine a block and verify that all nodes accept it
        self.nodes[0].generate(1)
        sync_blocks(self.nodes)
        logging.info("mempool counts: %s" % [ x.getmempoolinfo()["size"] for x in self.nodes])

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
