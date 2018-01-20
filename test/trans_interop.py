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
import sys
logging.basicConfig(format='%(asctime)s.%(levelname)s: %(message)s', level=logging.INFO)

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *

from interopUtils import *

# number of block used for generate function
num_blocks = 20


def verify_transaction_sendmany(self, nodeTxOne, nodeTxTwo):
    """
    Verify the transaction of BTC using
    "sendmany" API from one node: twice to self, and twice to other node
    
    See Bitcoin API JSON-RPC:
    > https://chainquery.com/bitcoin-api/sendmany
    
    Input:
        nodeTxOne : node one involved in the transaction
        nodeTxTwo : node two involved in the transaction
        num_signature : number of signatures required
    """
    #logging.info("### Balance (Before) : %s" % [ x.getinfo()["balance"] for x in self.nodes])
    send_to = { self.nodes[nodeTxOne].getnewaddress() : 0.11,
                self.nodes[nodeTxTwo].getnewaddress() : 0.22,
                self.nodes[nodeTxOne].getaccountaddress("from1") : 0.33,
                self.nodes[nodeTxTwo].getaccountaddress("toself") : 0.44 }
    txid = self.nodes[nodeTxTwo].sendmany("", send_to)
    self.sync_all()
    assert_array_result(self.nodes[nodeTxTwo].listtransactions(),
                       {"category":"send","amount":Decimal("-0.11")},
                       {"txid":txid} )
    assert_array_result(self.nodes[nodeTxOne].listtransactions(),
                       {"category":"receive","amount":Decimal("0.11")},
                       {"txid":txid} )
    assert_array_result(self.nodes[nodeTxTwo].listtransactions(),
                       {"category":"send","amount":Decimal("-0.22")},
                       {"txid":txid} )
    assert_array_result(self.nodes[nodeTxTwo].listtransactions(),
                       {"category":"receive","amount":Decimal("0.22")},
                       {"txid":txid} )
    assert_array_result(self.nodes[nodeTxTwo].listtransactions(),
                       {"category":"send","amount":Decimal("-0.33")},
                       {"txid":txid} )
    assert_array_result(self.nodes[nodeTxOne].listtransactions(),
                       {"category":"receive","amount":Decimal("0.33")},
                       {"txid":txid, "account" : "from1"} )
    assert_array_result(self.nodes[nodeTxTwo].listtransactions(),
                       {"category":"send","amount":Decimal("-0.44")},
                       {"txid":txid, "account" : ""} )
    assert_array_result(self.nodes[nodeTxTwo].listtransactions(),
                       {"category":"receive","amount":Decimal("0.44")},
                       {"txid":txid, "account" : "toself"} )

def verify_transaction_createmultisig(self, nodeTxOne, nodeTxTwo, num_signature):
    """
    Verify the transaction of BTC using
    "createmultisig" to create a P2SH multi-signature address
    
    See Bitcoin API JSON-RPC:
    > https://chainquery.com/bitcoin-api/creatmultisig
    
    Input:
        nodeTxOut : node Id of the TxOut (debit)
        nodeTxIn : node Id of the TxIn (credit)
        num_signature : number of signatures required
    """

    multisig = self.nodes[nodeTxTwo].createmultisig(num_signature, [self.nodes[nodeTxTwo].getnewaddress()])
    self.nodes[nodeTxOne].importaddress(multisig["redeemScript"], "watchonly", False, True)
    txid = self.nodes[nodeTxTwo].sendtoaddress(multisig["address"], 0.1)
    self.nodes[nodeTxTwo].generate(1)
    self.sync_all()
    assert(len(self.nodes[nodeTxOne].listtransactions("watchonly", 100, 0, False)) == 0)
    assert_array_result(self.nodes[nodeTxOne].listtransactions("watchonly", 100, 0, True),
                       {"category":"receive","amount":Decimal("0.1")},
                       {"txid":txid, "account" : "watchonly"} )
                
def verify_transaction_amount_confirm(self, nodeTxOut, nodeTxIn, amount):
    """
    Verify the transaction of BTC amount and confirmation from one node to the other
    
    Input:
        nodeTxOut : node Id of the TxOut (debit)
        nodeTxIn : node Id of the TxIn (credit)
        amount : amount to spend in BTC
    """
    debit_before = self.nodes[nodeTxOut].getinfo()["balance"]
    credit_before = self.nodes[nodeTxIn].getinfo()["balance"]
    #logging.info("### Balance of Spending Node(%s) " %debit_before)
    #logging.info("### Balance of Receiving Node(%s) " %credit_before)
    
    txid = self.nodes[nodeTxOut].sendtoaddress(self.nodes[nodeTxIn].getnewaddress(), amount)
    #logging.info("=> txid :  %s " % txid)
    self.sync_all()

    if (nodeTxOut != nodeTxIn):
        #logging.info(self.nodes[nodeTxOut].listtransactions())
        #logging.info("### Balance (Before) : %s" % [ x.getinfo()["balance"] for x in self.nodes])  
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
        #logging.info("### Balance (After): %s" % [ x.getinfo()["balance"] for x in self.nodes])

        debit_after = self.nodes[nodeTxOut].getinfo()["balance"]
        credit_after = self.nodes[nodeTxIn].getinfo()["balance"]
        logging.info("Balance of Spending Node(%s) " %debit_after)
        logging.info("=> Balance of Receiving Node(%s) " %credit_after)

        # credit after transaction confirmed is increased by amount
        assert_equal( (credit_after - credit_before) , amount)
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
        logging.info("Balance of Spending Node(%s) " %debit_after)
        logging.info("=> Balance of Receiving Node(%s) " %credit_after)
        
        # credit and debit after transaction confirmed is the same
        assert_equal( debit_after, credit_after )

        self.nodes[nodeTxOut].generate(1)
        self.sync_all()
        
        debit_after = self.nodes[nodeTxOut].getinfo()["balance"]
        credit_after = self.nodes[nodeTxIn].getinfo()["balance"]
        logging.info("Sync_all Balance of Spending Node(%s) " %debit_after)
        logging.info("=> Sync_all Balance of Receiving Node(%s) " %credit_after)
        
        # credit and debit after sync_all should still be the same
        assert_equal( debit_after, credit_after )
        
@assert_capture()
def verify_amount_sendto_nodes(self, node1, node2, amount):
    """
    Verify amount sending and receiving between two nodes
    Input:
        node1 : node 1 involved in the transaction
        node2 : node 2 involved in the transaction
        amount : amount to spend in BTC
    """

    try:
        verify_transaction_amount_confirm(self, node1, node2, amount)
    except JSONRPCException as e:
        #print('>>>> Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        if e.error['code'] == -5: # Invalid Bitcoin address
            raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                           "error_type": exc_type.__name__, "error_msg": str( e.error["message"]), \
                           "n1" : node1, "n2" : node2, "amount" : amount, "numsig" : "N/A"})

@assert_capture()
def verify_sendmany(self, node1, node2):
    """
    Verify amount sending and receiving between two nodes
    Input:
        node1 : node 1 involved in the transaction
        node2 : node 2 involved in the transaction
    """

    try:
        verify_transaction_sendmany(self, node1, node2)
    except JSONRPCException as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        if e.error['code'] == -5: # Invalid Bitcoin address
            raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                           "error_type": exc_type.__name__, "error_msg": str( e.error["message"]), \
                           "n1" : node1, "n2" : node2, "amount" : "N/A", "numsig" : "N/A"})

@assert_capture()
def verify_createmultisig(self, node1, node2, num_signature):
    """
    Verify the transaction of BTC using
    "createmultisig" to create a P2SH multi-signature address
    
    See Bitcoin API JSON-RPC:
    > https://chainquery.com/bitcoin-api/creatmultisig
    
    Input:
        node1 : node 1 involved in the transaction
        node2 : node 2 involved in the transaction
        num_signature : number of signatures required
    """

    try:
        verify_transaction_createmultisig(self, node1, node2, num_signature)
    except JSONRPCException as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        if e.error['code'] == -5: # Invalid Bitcoin address
            raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                           "error_type": exc_type.__name__, "error_msg": str( e.error["message"]), \
                           "n1" : node1, "n2" : node2, "amount" : "N/A", "numsig" : num_signature})

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
        logging.info(bins)
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
        logging.info("Verify that all nodes are connected")
        verifyInterconnect(self.nodes)

        logging.info("block count: %s" % ([ x.getblockcount() for x in self.nodes]))
        logging.info("Connection count: %s" % ([ x.getconnectioncount() for x in self.nodes]))

        # #########
        logging.info("Verify that every node can produce blocks and that every other node receives them")
        for n in self.nodes:
            n.generate(num_blocks)
            sync_blocks(self.nodes)

        logging.info("block count: %s" % ([ x.getblockcount() for x in self.nodes]))

        # #########
        logging.info("Verify that every node can produce P2PKH transactions and that every other node receives them")
        # first get mature coins in every client
        self.nodes[0].generate(101)
        sync_blocks(self.nodes)

        for n in self.nodes:
            addr = n.getnewaddress()
            n.sendtoaddress(addr, 1)
            sync_mempools(self.nodes)

        logging.info("mempool counts: %s" % [ x.getmempoolinfo()["size"] for x in self.nodes])

        logging.info("Verify that a block with P2PKH txns is accepted by all nodes and clears the mempool on all nodes")
        self.nodes[0].generate(1)
        sync_blocks(self.nodes)
        logging.info("mempool counts: %s" % [ x.getmempoolinfo()["size"] for x in self.nodes])

        logging.info("******* Verify transaction amounts on different nodes ********* ")
        verify_amount_sendto_nodes(self, 0, 1, 10)
        verify_amount_sendto_nodes(self, 0, 2, 10)
        verify_amount_sendto_nodes(self, 2, 3, 10)  #failing
        verify_amount_sendto_nodes(self, 1, 2, 10)
        verify_amount_sendto_nodes(self, 1, 3, 10)
        verify_amount_sendto_nodes(self, 2, 3, 10)  #failing

        logging.info("******* Verify transaction amounts on the same nodes ********* ")
        verify_amount_sendto_nodes(self, 0, 0, 10)
        verify_amount_sendto_nodes(self, 1, 1, 10)
        verify_amount_sendto_nodes(self, 2, 2, 10)
        verify_amount_sendto_nodes(self, 3, 3, 10)
        
        logging.info("Verify transaction using sendmany and createmultisig APIs : Node 0 to 1")
        verify_sendmany(self, 0, 1)
        verify_createmultisig(self, 0, 1, 1)
        
        logging.info("Verify transaction using sendmany and createmultisig APIs : Node 1 to 2")
        verify_sendmany(self, 1, 2)
        verify_createmultisig(self, 1, 2, 1)
        
        logging.info("Verify transaction using sendmany and createmultisig APIs : Node 2 to 3")
        verify_sendmany(self, 2, 3)
        verify_createmultisig(self, 2, 3, 1)
        
        reporter.display_report()
        
def Test():
    t = CTest("debug", clientDirs)
    t.drop_to_pdb = True
    bitcoinConf = {
        "debug": ["net", "blk", "thin", "mempool", "req", "bench", "evict"],
        "blockprioritysize": 2000000  # we don't want any transactions rejected due to insufficient fees...
    }
    # folder to store bitcoin runtime data and logs
    tmpdir = "--tmpdir=/tmp/cashInterop"
    
    for arg in sys.argv[1:]:
        if "--tmpdir=" in arg:
            tmpdir = str(arg)
            logging.info("# User input : %s" %tmpdir)
    
    t.main([tmpdir], bitcoinConf, None)

if __name__ == "__main__":
    Test()
