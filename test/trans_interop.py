#!/usr/bin/env python3
# Copyright (c) 2015-2017 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
import os 
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

from interopUtils import *

# number of block used for generate function
num_blocks = 20

def verify_transaction_amount_confirm(self, nodeTxOut, nodeTxIn, amount):
    """
    Verify the transaction of BTC amount and confirmation from one node to the other
    
    Input:
        nodeTxOut : node Id of the TxOut (debit)
        nodeTxIn : node Id of the TxIn (credit)
        amount : amount to spend in BTC
    """ 
    print(" ")
    #print("### Balance (Before) : %s" % [ x.getinfo()["balance"] for x in self.nodes])
    
    debit_before = self.nodes[nodeTxOut].getinfo()["balance"]
    credit_before = self.nodes[nodeTxIn].getinfo()["balance"]
    print("### Balance of Spending Node(%s) " %debit_before)
    print("### Balance of Receiving Node(%s) " %credit_before)
    
    txid = self.nodes[nodeTxOut].sendtoaddress(self.nodes[nodeTxIn].getnewaddress(), amount)
    print("=> txid :  %s " % txid)
    self.sync_all()

    if (nodeTxOut != nodeTxIn):
        #print(self.nodes[nodeTxOut].listtransactions())
        print("### Balance (Before) : %s" % [ x.getinfo()["balance"] for x in self.nodes])  
        assert_array_result(self.nodes[nodeTxOut].listtransactions(),
                            {"txid":txid},
                            {"category":"send","account":"","amount":Decimal(str(-amount)),"confirmations":0})                 
        assert_array_result(self.nodes[nodeTxIn].listtransactions(),
                            {"txid":txid},
                            {"category":"receive","account":"","amount":Decimal(str(amount)),"confirmations":0})

        # mine a block, confirmations should change:
        self.nodes[nodeTxOut].generate(1)
        self.sync_all()

        assert_array_result(self.nodes[nodeTxOut].listtransactions(),
                            {"txid":txid},
                            {"category":"send","account":"","amount":Decimal(str(-amount)),"confirmations":1})
        assert_array_result(self.nodes[nodeTxIn].listtransactions(),
                            {"txid":txid},
                            {"category":"receive","account":"","amount":Decimal(str(amount)),"confirmations":1})
        print("### Balance (After): %s" % [ x.getinfo()["balance"] for x in self.nodes])


        debit_after = self.nodes[nodeTxOut].getinfo()["balance"]
        credit_after = self.nodes[nodeTxIn].getinfo()["balance"]
        print("Balance of Spending Node(%s) " %debit_after)
        print("=> Balance of Receiving Node(%s) " %credit_after)

        # credit after transaction confirmed is increased by amount
        assert( (credit_after - credit_before) == amount)
    else:
        # send-to-self:
        assert_array_result(self.nodes[nodeTxOut].listtransactions(),
                           {"txid":txid, "category":"send"},
                           {"amount":Decimal(str(-amount))})
        assert_array_result(self.nodes[nodeTxIn].listtransactions(),
                           {"txid":txid, "category":"receive"},
                           {"amount":Decimal(str(amount))})

        debit_after = self.nodes[nodeTxOut].getinfo()["balance"]
        credit_after = self.nodes[nodeTxIn].getinfo()["balance"]
        print("Balance of Spending Node(%s) " %debit_after)
        print("=> Balance of Receiving Node(%s) " %credit_after)
        
        # credit and debit after transaction confirmed is the same
        assert( debit_after == credit_after )

        self.nodes[nodeTxOut].generate(1)
        self.sync_all()
        
        debit_after = self.nodes[nodeTxOut].getinfo()["balance"]
        credit_after = self.nodes[nodeTxIn].getinfo()["balance"]
        print("Sync_all Balance of Spending Node(%s) " %debit_after)
        print("=> Sync_all Balance of Receiving Node(%s) " %credit_after)
        
        # credit and debit after sync_all should still be the same
        assert( debit_after == credit_after )
        
             
def verify_sendto_same_node(self, amount):
    """
    Verify the sending and receiving nodes are the same
    Input:
        amount : amount to spend in BTC
    """
    
    print("*** Same Nodes ****")
    # send amount to self (from Node 0 to 0)
    verify_transaction_amount_confirm(self, 0, 0, amount)
    # send amount to self (from Node 1 to 1)
    verify_transaction_amount_confirm(self, 1, 1, amount)
    # send amount to self (from Node 2 to 2)
    verify_transaction_amount_confirm(self, 2, 2, amount)
    # send amount = 10 to self (from Node 3 to 3)
    verify_transaction_amount_confirm(self, 3, 3, amount)
    
 
def verify_sendto_different_node(self, amount):
    """
    Verify the sending and receiving nodes are not the same node
    Input:
        amount : amount to spend in BTC
    """
    
    print("*** Different Nodes ****")
    # send amount from Node 0 to 1 
    verify_transaction_amount_confirm(self, 0, 1, amount)
    # send amount from Node 0 to 2 
    verify_transaction_amount_confirm(self, 0, 2, amount)
    # send amount from Node 1 to 2 
    verify_transaction_amount_confirm(self, 1, 2, amount)
    # send amount from Node 1 to 3 
    verify_transaction_amount_confirm(self, 1, 3, amount)
    # send amount from Node 2 to 3 
    verify_transaction_amount_confirm(self, 2, 3, amount)
    

class CTest(BitcoinTestFramework):
    def __init__(self, build_variant, client_dirs):
        BitcoinTestFramework.__init__(self)
        self.buildVariant = build_variant
        self.clientDirs = client_dirs

    def setup_chain(self,bitcoinConfDict=None, wallets=None):
        logging.info("Initializing test directory "+self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, len(self.clientDirs), bitcoinConfDict, wallets)

    def setup_network(self, split=False):
        bins = [ os.path.join(base_dir, x, self.buildVariant, "src","bitcoind") for x in clientDirs]
        print(bins)
        self.nodes = start_nodes(len(self.clientDirs), self.options.tmpdir,binary=bins, timewait=60*60)

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
        # #########
        print("Verify that all nodes are connected")
        verifyInterconnect(self.nodes)

        print("block count: %s" % ([ x.getblockcount() for x in self.nodes]))
        print("Connection count: %s" % ([ x.getconnectioncount() for x in self.nodes]))

        # #########
        print("Verify that every node can produce blocks and that every other node receives them")
        for n in self.nodes:
            n.generate(num_blocks)
            sync_blocks(self.nodes)

        print("block count: %s" % ([ x.getblockcount() for x in self.nodes]))

        # #########
        print("Verify that every node can produce P2PKH transactions and that every other node receives them")
        # first get mature coins in every client
        self.nodes[0].generate(101)
        sync_blocks(self.nodes)

        for n in self.nodes:
            addr = n.getnewaddress()
            n.sendtoaddress(addr, 1)
            sync_mempools(self.nodes)

        print("mempool counts: %s" % [ x.getmempoolinfo()["size"] for x in self.nodes])

        print("Verify that a block with P2PKH txns is accepted by all nodes and clears the mempool on all nodes")
        self.nodes[0].generate(1)
        sync_blocks(self.nodes)
        print("mempool counts: %s" % [ x.getmempoolinfo()["size"] for x in self.nodes])

        print("Verify transaction amounts and confirmation counts between two nodes")
        verify_sendto_different_node(self, 10)
        
        print("Verify transaction amounts on the same nodes")
        verify_sendto_same_node(self, 10)
         
def Test():
    t = CTest("debug", clientDirs)
    t.drop_to_pdb = True
    bitcoinConf = {
        "debug": ["net", "blk", "thin", "mempool", "req", "bench", "evict"],
        "blockprioritysize": 2000000  # we don't want any transactions rejected due to insufficient fees...
    }
    # "--tmpdir=/ramdisk/test",
    #t.main(["--nocleanup", "--noshutdown"], bitcoinConf, None)
    eachConf = [bitcoinConf]*4
    # eachConf[3]["maxlimitertxfee"] = None  # classic does not have this option
    t.main(["--tmpdir=/ramdisk/test"], bitcoinConf, None)

if __name__ == "__main__":
    Test()
