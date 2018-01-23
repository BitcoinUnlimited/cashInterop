#!/usr/bin/env python3
# Copyright (c) 2015-2017 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
import os 
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(dir_path, "..")

import pdb
import time
import math
import json
import logging
logging.basicConfig(format='%(asctime)s.%(levelname)s: %(message)s', level=logging.INFO)

from binascii import hexlify
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal
from test_framework.script import *
from test_framework.blocktools import *
from test_framework.bunode import *
from interopUtils import *

NODE_BITCOIN_CASH = (1 << 5)
SCRIPT_WORDS = b"this is junk data len125.this is junk data len125.this is junk data len125.this is junk data len125.this is junk data len125."
TX_DATA = 'aa54686973206973203830206279746573206f6620746573742064617461206372656174656420746f20757365207570207472616e73616374696f6e20737061636520666173746572202e2e2e2e2e2e2e'
AMOUNT =  3000      # amount in BTC
NUM_ADDRS = 50      # for UTXOs generation  Note: JSONRPC error: 256: absurdly-high-fee when NUM_ADDRS is tool low (eg. 5)
ITERATIONS = 100    # number of iterations to create 12500 bytes of useless script words
GENERATED_BLKS = 200   # number of blocks for generate command

def wastefulOutput(btcAddress):
    """ 
    Create useless data for CScript to generate many transactions used for Large Block size of 1MB to 32MB
    Input:
        btcAddress : BTC address - public key of the receiver
    Return:
        CScript with useless data
    Warning: 
        Creates outputs that can't be spent by bitcoind
    """
    data = b""
    # Concatenate len(SCRIPT_WORDS) for 100 times to get data of 12500 bytes
    for _ in range(ITERATIONS):
        data += SCRIPT_WORDS
    #print("\n#Length of Junk data : ", len(data))

    # len(bitcoinAddress2bin(btcAddress))) = 20 and others OP codes adding up to 31
    # trim 67 chars due to extra agruments inputs to CScript (size = 31) and 
    # to make Signed Txn Block to round up to MB block steps  (see signedtxn in generateTx)
    data = data[:-67]
    ret = CScript([data, OP_DROP, OP_DUP, OP_HASH160, bitcoinAddress2bin(btcAddress), OP_EQUALVERIFY, OP_CHECKSIG])
    return ret

def p2pkh(btcAddress):
    """ 
    Create a pay-to-public-key-hash script
    """
    ret = CScript([OP_DUP, OP_HASH160, bitcoinAddress2bin(btcAddress), OP_EQUALVERIFY, OP_CHECKSIG])
    return ret

def createrawtransaction(inputs, outputs, outScriptGenerator=p2pkh):
    """
    Create a transaction with the exact input and output syntax as the bitcoin-cli "createrawtransaction" command.
    If you use the default outScriptGenerator, this function will return a hex string that exactly matches the
    output of bitcoin-cli createrawtransaction.

    Input:
        inputs : list of inputs used as input to the transaction
        outputs : outputs to be spent, the first output in a index of 0
        outScriptGenerator : generates script content (wastefulOutput is used for generate useless data)
    """
    if not type(inputs) is list:
        inputs = [inputs]

    tx = CTransaction()
    for i in inputs:
        tx.vin.append(CTxIn(COutPoint(i["txid"], i["vout"]), b"", 0xffffffff))
    for addr, amount in outputs.items():
        if addr == "data":
            tx.vout.append(CTxOut(0, CScript([OP_RETURN, unhexlify(amount)])))
        else:
            tx.vout.append(CTxOut(amount * BTC, outScriptGenerator(addr)))
    tx.rehash()
    return hexlify(tx.serialize()).decode("utf-8")

def generateTx(node, addrs, numTxns=1, data=None):
    """
    Generate, signed and send Transactions for Large Block generation
    Input:
        node : node for the transactions
        addrs : addresses for UTXOs
        numTxns : number of transactions generate for different block size 
                  - For 1MB (need 10 txns), 2MB (20 txns), ... , 32MB (320 txns) 
        data : random data to fill up the block
    Return:
        count : number of transactions sent
        size : total bytes of all transactions (1MB, 2MB, etc...)
    """
    wallet = node.listunspent()
    wallet.sort(key=lambda x: x["amount"], reverse=False)
#        if len(wallet) > 0:
#            logging.info(wallet[0:1]) # just to see what's in it
    logging.info("\n Wallet length is %d" % len(wallet))
    size = 0
    count = 0
    decContext = decimal.getcontext().prec
    decimal.getcontext().prec = 8 + 8  # 8 digits to get to 21million, and each bitcoin is 100 million satoshis
    utxo = wallet.pop()
    outp = {}
    # Make the tx bigger by adding addtl outputs so it validates faster
    payment = satoshi_round(utxo["amount"] / decimal.Decimal(8.0))
    for x in range(0, 8):
        outp[addrs[(count + x) % len(addrs)]] = payment
    #print("OUTP ==>>>>> ", outp)

    for i in range(numTxns):
        count += 1
        if data:
            outp["data"] = data
        txn = createrawtransaction([utxo], outp, wastefulOutput)
        signedtxn = node.signrawtransaction(txn)
        size += len(binascii.unhexlify(signedtxn["hex"]))
        logging.info("=> Signed txn size : %d" % size)
        node.sendrawtransaction(signedtxn["hex"])
        logging.info("Txn number: %d Length %d " % (count, size))
    decimal.getcontext().prec = decContext
    return (count, size)

@assert_capture()
def test_generate_sendblock(self, addrs, nodeId, numtxn=1):
    """ 
    Test to generate and send block in MB increments

    Input:
        addrs : addresses for UTXOs
        nodeId : node Id for the transactions
        numTxns : number of transactions generate for different block size 
                  - For 1MB (need 10 txns), 2MB (20 txns), ... , 32MB (320 txns) 
    Return:
        count : number of transactions sent
        size : total bytes of all transactions (1MB, 2MB, etc...)
    """
    # data used must be 
    #  1. Even; Otherwise, Error('Odd-length string',)
    #  2. hexadecimal; Error('Non-hexadecimal digit found
    ##self.generateTx(self.nodes[nodeId], addrs, numtxn, data=TX_DATA)
    #generateTx(self.nodes[nodeId], addrs, numtxn, data=TX_DATA)
    logging.info("mine blocks")
    try: 
        generateTx(self.nodes[nodeId], addrs, numtxn, data=TX_DATA)
        self.nodes[nodeId].generate(1)  # mine all the created transactions
        self.sync_all()
    except JSONRPCException as e:
        print('>>>> Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        if e.error['code'] == -1: # Excessive block generated
            print(fname, str( e.error["message"]))
            assert(0)

    logging.info("sync all blocks")
    sync_blocks(self.nodes)
    base = [x.getblockcount() for x in self.nodes]
    assert_equal(base, [base[0]] * 4)

class ExcessiveTest(BitcoinTestFramework):
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

    def testDefaults(self):
        for n in self.nodes:
            nodeInfo = n.getnetworkinfo()
            t = n.get("mining.fork*")
            assert(t['mining.forkBlockSize'] == 2000000)  # REQ-4-2
            assert(t['mining.forkExcessiveBlock'] == 8000000)  # REQ-4-1

            if int(nodeInfo["localservices"],16)&NODE_BITCOIN_CASH:
                assert(t['mining.forkTime'] == 1501590000)  # Bitcoin Cash release REQ-2
            else:
                assert(t['mining.forkTime'] == 0)  # main release default

    def testCli(self):
        n = self.nodes[0]
        now = int(time.time())
        n.set("mining.forkTime=%d" % now)
        n.set("mining.forkExcessiveBlock=9000000")
        n.set("mining.forkBlockSize=3000000")
        n = self.nodes[1]
        n.set("mining.forkTime=%d" % now, "mining.forkExcessiveBlock=9000000", "mining.forkBlockSize=3000000")

        # Verify that the values were properly set
        for n in self.nodes[0:2]:
            t = n.get("mining.fork*")
            assert(t['mining.forkBlockSize'] == 3000000)
            assert(t['mining.forkExcessiveBlock'] == 9000000)
            assert(t['mining.forkTime'] == now)

        self.nodes[3].set("mining.forkTime=0")
        nodeInfo = self.nodes[3].getnetworkinfo()
        # if this is a bitcoin cash build, we need to do the cash defaults on our old chain node
        # default for node2 and node3 are 
        assert(t['mining.forkBlockSize'] == 2000000)
        assert(t['mining.forkExcessiveBlock'] == 8000000)
        return now

    def createUtxos(self, addrs, node, amt=AMOUNT, genblks=GENERATED_BLKS):
        """
        Create unspent transaction output (UTXO)

        Input:
            addrs : addresses for UTXOs generation
            node : node to get the created UTXO
            amt : amount in BTC
            genblks : number of block to generate/mine
        Output:
            addrs : 
        """
        node.generate(genblks)
        sync_blocks(self.nodes)
        wallet = node.listunspent()
        wallet.sort(key=lambda x: x["amount"], reverse=True)

        # Create a LOT of UTXOs
        logging.info("Create lots of UTXOs...")
        n = 0
        group = min(100, amt)
        count = 0
        for w in wallet:
            count += group
            (txn,inp,outp,txid) = split_transaction(node, [w], addrs[n:group + n])
            #logging.info("---> Txid : %s " % txid)
            n += group
            if n >= len(addrs):
                n = 0
            if count > amt:
                break
        logging.info("mine blocks")
        node.generate(1)  # mine all the created transactions
        logging.info("sync all blocks and mempools")
        self.sync_all()

    def run_test(self):
        logging.info("block count: %s" % ([ x.getblockcount() for x in self.nodes]))
        #BitcoinTestFramework.run_test (self)
        tips = self.nodes[0].getchaintips ()
        assert_equal (len (tips), 1)
        assert_equal (tips[0]['branchlen'], 0)
        #assert_equal (tips[0]['height'], 200)
        assert_equal (tips[0]['status'], 'active')
        
        # Creating UTXOs needed for building tx for large blocks
        logging.info("Creating addresses...")
        self.nodes[0].keypoolrefill(NUM_ADDRS)
        self.nodes[1].keypoolrefill(NUM_ADDRS)
        self.nodes[2].keypoolrefill(NUM_ADDRS)
        self.nodes[3].keypoolrefill(NUM_ADDRS)

        address0 = [self.nodes[0].getnewaddress() for _ in range(NUM_ADDRS)]
        address1 = [self.nodes[1].getnewaddress() for _ in range(NUM_ADDRS)]
        address2 = [self.nodes[2].getnewaddress() for _ in range(NUM_ADDRS)]
        address3 = [self.nodes[3].getnewaddress() for _ in range(NUM_ADDRS)]

        logging.info("creating utxos")
        #amount =  3000
        #genBlksize = 200  # to give 50 BTC
        #self.createUtxos(address0, self.nodes[0], amount, genBlksize)

        # use defaults amount and genBlksize
        self.createUtxos(address0, self.nodes[0])
        self.createUtxos(address1, self.nodes[1])
        self.createUtxos(address2, self.nodes[2])
        self.createUtxos(address3, self.nodes[3])

        self.testDefaults()
        #forkTime = self.testCli()  # also sets up parameters on nodes 0, 1 to fork
        base = [x.getblockcount() for x in self.nodes]
        assert_equal(base, [base[0]] * 4)

        logging.info("Building > 1MB block...")
        numtxn = 10   # num of trans  : 10 = 1M, 50 = 5M, 320 = 32M
        test_generate_sendblock(self, address0, 0, numtxn)
        test_generate_sendblock(self, address1, 1, numtxn)
        test_generate_sendblock(self, address2, 2, numtxn)
        test_generate_sendblock(self, address3, 3, numtxn)
        logging.info("====>> 1 MB <<====\n ")

        numtxn = 50   # num of trans  : 10 = 1M, 50 = 5M, 320 = 32M
        test_generate_sendblock(self, address0, 0, numtxn)
        test_generate_sendblock(self, address1, 1, numtxn)
        test_generate_sendblock(self, address2, 2, numtxn)
        test_generate_sendblock(self, address3, 3, numtxn)
        logging.info("====>> 50 MB <<====\n ")

        numtxn = 320   # num of trans  : 10 = 1M, 50 = 5M, 320 = 32M
        test_generate_sendblock(self, address0, 0, numtxn)
        test_generate_sendblock(self, address1, 1, numtxn)
        test_generate_sendblock(self, address2, 2, numtxn)
        test_generate_sendblock(self, address3, 3, numtxn)
        logging.info("====>> 320 MB <<====\n ")

        reporter.display_report()

def Test():
    t = ExcessiveTest("debug", clientDirs)
    t.drop_to_pdb = True
    bitcoinConf = {
        "debug": ["net", "blk", "thin", "mempool", "req", "bench", "evict"],
        "blockprioritysize": 2000000000
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
