#!/usr/bin/env python3
# Copyright (c) 2015-2018 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

# Test emergent consensus scenarios
import time
import random
import pdb
import os 
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(dir_path, "..")
if sys.version_info[0] < 3:
    raise "Use Python 3"

import logging
logging.basicConfig(format='%(asctime)s.%(levelname)s: %(message)s', level=logging.INFO, stream=sys.stdout)

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from test_framework.mininode import *
from test_framework.script import CScript, OP_TRUE, OP_CHECKSIG, OP_DROP, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG
from interopUtils import *

NODE_BITCOIN_CASH = (1 << 5)
ONE_MB = 1000000
TWO_MB = 2000000
FIVE_MB = 5000000

SCRIPT_WORDS = b"this is junk data. this is junk data. this is junk data. this is junk data. this is junk data."
ITERATIONS = 4   # number of iterations to create 12500 bytes of useless script words

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
    ret = CScript([data, OP_DROP, OP_DUP, OP_HASH160, bitcoinAddress2bin(btcAddress), OP_EQUALVERIFY, OP_CHECKSIG])
    return ret

def p2pkh(btcAddress):
    """ create a pay-to-public-key-hash script"""
    ret = CScript([OP_DUP, OP_HASH160, bitcoinAddress2bin(btcAddress), OP_EQUALVERIFY, OP_CHECKSIG])
    return ret

def createrawtransaction(inputs, outputs, outScriptGenerator=p2pkh):
    """
    Create a transaction with the exact input and output syntax as the bitcoin-cli "createrawtransaction" command.
    If you use the default outScriptGenerator, this function will return a hex string that exactly matches the
    output of bitcoin-cli createrawtransaction.
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

def generateTx(node, txBytes, addrs, data=None):
    wallet = node.listunspent()
    wallet.sort(key=lambda x: x["amount"], reverse=False)
    logging.info("Wallet length is %d" % len(wallet))

    size = 0
    count = 0
    decContext = decimal.getcontext().prec
    decimal.getcontext().prec = 8 + 8  # 8 digits to get to 21million, and each bitcoin is 100 million satoshis
    while size < txBytes:
        count += 1
        utxo = wallet.pop()
        outp = {}
        # Make the tx bigger by adding addtl outputs so it validates faster
        payment = satoshi_round(utxo["amount"] / decimal.Decimal(8.0))
        for x in range(0, 8):
            outp[addrs[(count + x) % len(addrs)]] = payment
        if data:
            outp["data"] = data
        txn = createrawtransaction([utxo], outp, wastefulOutput)
        # txn2 = node.createrawtransaction([utxo], outp)
        signedtxn = node.signrawtransaction(txn)
        size += len(binascii.unhexlify(signedtxn["hex"]))
        node.sendrawtransaction(signedtxn["hex"])
    logging.info("%d tx %d length" % (count, size))
    decimal.getcontext().prec = decContext
    return (count, size)

def mostly_sync_mempools(rpc_connections, difference=50, wait=1, verbose=1):
    """
    Wait until everybody has the most of the same transactions in their memory
    pools. There is no guarantee that mempools will ever sync due to the
    filterInventoryKnown bloom filter.
    """
    iterations = 0
    while True:
        iterations += 1
        pool = set(rpc_connections[0].getrawmempool())
        num_match = 1
        poolLen = [len(pool)]
        for i in range(1, len(rpc_connections)):
            tmp = set(rpc_connections[i].getrawmempool())
            if tmp == pool:
                num_match = num_match + 1
            if iterations > 10 and len(tmp.symmetric_difference(pool)) < difference:
                num_match = num_match + 1
            poolLen.append(len(tmp))
        if verbose:
            logging.info("sync mempool: " + str(poolLen))
        if num_match == len(rpc_connections):
            break
        time.sleep(wait)

def print_bestblockhash(node, nodeId):
    """ 
    Helper to print bestblockhash and block size
    Input:
        node : node to get the block information
        nodeId : Id of the mode
    Return:
        block_size : block size
        best_block_hash : hash of the best block (tip of the chain)
    """
    best_blockhash = node.getbestblockhash()
    block_size = node.getblock(best_blockhash, True)['size']
    best_blockhash = int(best_blockhash, 16)

    logging.info("> Node%d  block_size = %d"  %(nodeId, block_size))
    logging.info("> Blockhash = %s"  %best_blockhash)
    return block_size, best_blockhash

@assert_capture()
def test_default_values(self):
    """
    Test system default values of MG and EB
    Criteria:
    BUIP-HF Technical Specification:
    MB = 2000000
    EB = 8000000
    # Bitcoin Cash node
    forkTime = 1501590000   #corresponding to Tue 1 Aug 2017 12:20:00 UTC

    Input:
        self : test object
    Assertions:
        fail when not match with default
    """    
    logging.info(">>> Entered : test_default_values \n")
    try:
        for n in self.nodes:
            nodeInfo = n.getnetworkinfo()
            t = n.get("mining.fork*")
            assert(t['mining.forkBlockSize'] == 2000000)  # REQ-4-2
            assert(t['mining.forkExcessiveBlock'] == 8000000)  # REQ-4-1
        
            if int(nodeInfo["localservices"],16)&NODE_BITCOIN_CASH:
                assert(t['mining.forkTime'] == 1501590000)  # Bitcoin Cash release REQ-2
            else:
                assert(t['mining.forkTime'] == 0)  # main release default
    except (Exception, JSONRPCException) as e1:
        logging.info(e1)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e1 ), \
                       "n1" : "N/A", "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})

@assert_capture()
def test_setting_values(self, nodeId=0):
    """ 
    Test setting and getting values of MG and EB. Assumes the default 
    excessive at 8MB and mining at 2MB
    
    Criteria:
        MB must be less than or equal to EB
    Input:
        self : test object
    Assertions:
        fail when not match with defaults
    """
    logging.info(">>> Entered  : test_setting_values \n")
    node = self.nodes[nodeId]
    # excessive block size is smaller than your proposed mined block size
    try:
        node.setminingmaxblock(32000000)
    except JSONRPCException as e:
        logging.info(">> PASS : %s " %e.error["message"])
        pass
    else:
        assert(0)  # was able to set the mining size > the excessive size

    # max generated block size must be greater than 100 byte
    try:
        node.setminingmaxblock(99)
    except JSONRPCException as e:
        logging.info(">> PASS : %s " %e.error["message"])
        pass
    else:
        assert(0)  # was able to set the mining size below our arbitrary minimum

    # maximum mined block is larger than your proposed excessive size
    try:
        node.setexcessiveblock(1000, 10)
    except JSONRPCException as e:
        logging.info(">> PASS : %s " %e.error["message"])
        pass
    else:
        assert(0)  # was able to set the excessive size < the mining size

@assert_capture()
def test_sync_clear_mempool(self):
    """ 
    Test mempool synchornization and clearance

    Input:
        self : test object
    Raise: 
        Encounter RPC error
    """
    logging.info(">>> Entered : test_sync_clear_mempool \n")
    try:
        # clear out the mempool
        mostly_sync_mempools(self.nodes)
        for n in self.nodes:
            n.generate(2)
            sync_blocks(self.nodes)
        for n in self.nodes:
            while len(n.getrawmempool()):
                n.generate(1)
                sync_blocks(self.nodes)
        logging.info("cleared mempool: %s" % str([len(x) for x in [y.getrawmempool() for y in self.nodes]]))
        base = [x.getrawmempool() for x in self.nodes]
        assert_equal(base, [base[0]] * 4)
    except (Exception, JSONRPCException) as e1:
        logging.info(e1)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e1 ), \
                       "n1" : "N/A", "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})

@assert_capture()
def test_accept_depth(self, nodeOneId, nodeTwoId):
    """ 
    Test accept depth case

    Input:
        self : test object
        nodeOneId : first node ID
        nodeTwoId : second node ID
    Raise: 
        Encounter RPC error or General Exception
    """
    logging.info(">>> Entered : test_accept_depth \n")
    try:
        self.nodes[nodeTwoId].setminingmaxblock(1000)
        self.nodes[nodeTwoId].setexcessiveblock(1010, 4)

        # Mine an excessive block. Node One should not accept it
        addr = self.nodes[nodeTwoId].getnewaddress()
        for i in range(0,10):
          self.nodes[nodeOneId].sendtoaddress(addr, 1.0)
        self.nodes[nodeOneId].generate(1)
        time.sleep(2) #give blocks a chance to fully propagate
        counts = [ x.getblockcount() for x in self.nodes[0:2] ]

        logging.info("Counts: Node1 = %d and Node2 = %d " %(counts[0], counts[1]))
        assert_equal(counts[0]-counts[1], 1)
        # Mine a block on top. Node 1 should still not accept it
        self.nodes[nodeOneId].generate(1)
        time.sleep(2) #give blocks a chance to fully propagate
        counts = [ x.getblockcount() for x in self.nodes[0:2] ]
        logging.info("Counts: Node1 = %d and Node2 = %d " %(counts[0], counts[1]))
        assert_equal(counts[0]-counts[1], 2)

        # Change node 1 to AD=2. The assertion will fail if it doesn't accept the chain now 
        self.nodes[nodeTwoId].setexcessiveblock(1010, 2)
        self.nodes[nodeOneId].generate(1)
        time.sleep(2) #give blocks a chance to fully propagate  !!!!

        counts = [ x.getblockcount() for x in self.nodes[0:2] ]
        logging.info("Counts: Node1 = %d and Node2 = %d " %(counts[0], counts[1]))
        assert_equal(counts[0]-counts[1], 0)
    except (Exception, JSONRPCException) as e1:
        logging.info(e1)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e1 ), \
                       "n1" : self.nodes[nodeOneId], "n2" : self.nodes[nodeTwoId], "amount" : "N/A", "numsig" : "N/A"})

@assert_capture()
def test_excessive_Sigops(self):
    """ 
    Test Excessive Sig Ops
    
    Note: Re-use existing test from BU/qa/rpc-tests/excessive.py
    Input:
        self : test object
    """
    logging.info("Entered : test_excessive_Sigops \n")
    try:
        testExcessiveSigops(self)
    except (Exception, JSONRPCException) as e1:
        logging.info(e1)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e1 ), \
                       "n1" : "N/A", "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})

def testExcessiveSigops(self):
    """This test checks the behavior of the nodes in the presence of transactions that take a long time to validate.
    """
    NUM_ADDRS = 50
    logging.info("testExcessiveSigops: Cleaning up node state")

    # We are not testing excessively sized blocks so make these large
    self.nodes[0].set("net.excessiveBlock=5000000")
    self.nodes[1].set("net.excessiveBlock=5000000")
    self.nodes[2].set("net.excessiveBlock=5000000")
    self.nodes[3].set("net.excessiveBlock=5000000")
    self.nodes[0].setminingmaxblock(FIVE_MB)
    self.nodes[1].setminingmaxblock(FIVE_MB)
    self.nodes[2].setminingmaxblock(FIVE_MB)
    self.nodes[3].setminingmaxblock(FIVE_MB)
    # Stagger the accept depths so we can see the block accepted stepwise
    self.nodes[0].set("net.excessiveAcceptDepth=0")
    self.nodes[1].set("net.excessiveAcceptDepth=1")
    self.nodes[2].set("net.excessiveAcceptDepth=2")
    self.nodes[3].set("net.excessiveAcceptDepth=3")

    for n in self.nodes:
        n.generate(10)
        self.sync_blocks()

    self.nodes[0].generate(100)  # create a lot of BTC for spending
    self.sync_all()

    self.nodes[0].set("net.excessiveSigopsPerMb=100")  # Set low so txns will fail if its used
    self.nodes[1].set("net.excessiveSigopsPerMb=5000")
    self.nodes[2].set("net.excessiveSigopsPerMb=1000")
    self.nodes[3].set("net.excessiveSigopsPerMb=100")

    logging.info("Creating addresses...")
    self.nodes[0].keypoolrefill(NUM_ADDRS)
    addrs = [self.nodes[0].getnewaddress() for _ in range(NUM_ADDRS)]

    # test that a < 1MB block ignores the sigops parameter
    self.nodes[0].setminingmaxblock(ONE_MB)
    # if excessive Sigops was heeded, this txn would not make it into the block
    self.createUtxos(self.nodes[0], addrs, NUM_ADDRS)
    mpool = self.nodes[0].getmempoolinfo()
    assert_equal(mpool["size"], 0)

    # test that a < 1MB block ignores the sigops parameter, even if the max block size is less
    self.nodes[0].setminingmaxblock(FIVE_MB)
    # if excessive Sigops was heeded, this txn would not make it into the block
    self.createUtxos(self.nodes[0], addrs, NUM_ADDRS)
    mpool = self.nodes[0].getmempoolinfo()
    assert_equal(mpool["size"], 0)

    if self.extended:  # creating 1MB+ blocks is too slow for travis due to the signing cost
        self.createUtxos(self.nodes[0], addrs, 10000)  # we need a lot to generate 1MB+ blocks

        wallet = self.nodes[0].listunspent()
        wallet.sort(key=lambda x: x["amount"], reverse=True)
        self.nodes[0].set("net.excessiveSigopsPerMb=100000")  # Set this huge so all txns are accepted by this node

        logging.info("Generate > 1MB block with excessive sigops")
        generateTx(self.nodes[0], 1100000, addrs)

        counts = [x.getblockcount() for x in self.nodes]
        base = counts[0]

        self.nodes[0].generate(1)
        assert_equal(True, self.expectHeights([base + 1, base, base, base], 30))

        logging.info("Test excessive block propagation to nodes with different AD")
        self.nodes[0].generate(1)
        # it takes a while to sync all the txns
        assert_equal(True, self.expectHeights([base + 2, base + 2, base, base], 500))

        self.nodes[0].generate(1)
        assert_equal(True, self.expectHeights([base + 3, base + 3, base + 3, base], 90))

        self.nodes[0].generate(1)
        assert_equal(True, self.expectHeights([base + 4, base + 4, base + 4, base + 4], 90))

    logging.info("Excessive sigops test completed")

    # set it all back to defaults
    for n in self.nodes:
        n.generate(150)
        self.sync_blocks()

    self.nodes[0].set("net.excessiveSigopsPerMb=20000")  # Set low so txns will fail if its used
    self.nodes[1].set("net.excessiveSigopsPerMb=20000")
    self.nodes[2].set("net.excessiveSigopsPerMb=20000")
    self.nodes[3].set("net.excessiveSigopsPerMb=20000")

    self.nodes[0].setminingmaxblock(ONE_MB)
    self.nodes[1].setminingmaxblock(ONE_MB)
    self.nodes[2].setminingmaxblock(ONE_MB)
    self.nodes[3].setminingmaxblock(ONE_MB)
    self.nodes[0].set("net.excessiveBlock=1000000")
    self.nodes[1].set("net.excessiveBlock=1000000")
    self.nodes[2].set("net.excessiveBlock=1000000")
    self.nodes[3].set("net.excessiveBlock=1000000")

class TestInterOpExcessive(BitcoinTestFramework):
    def __init__(self, build_variant, client_dirs, extended=False):
        BitcoinTestFramework.__init__(self)
        self.buildVariant = build_variant
        self.clientDirs = client_dirs
        self.extended = extended
        self.bins = [ os.path.join(base_dir, x, self.buildVariant, "src","bitcoind") for x in clientDirs]
        logging.info(self.bins)

    def setup_network(self, split=False):
        self.nodes = start_nodes(len(self.clientDirs), self.options.tmpdir,binary=self.bins, timewait=60*60)

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
        BitcoinTestFramework.run_test(self)

        test_default_values(self)

        test_setting_values(self, nodeId=0)
        test_setting_values(self, nodeId=1)
        test_setting_values(self, nodeId=2)
        test_setting_values(self, nodeId=3)

        test_sync_clear_mempool(self)
        test_accept_depth(self, nodeOneId=0, nodeTwoId=1)

        test_excessive_Sigops(self)

        reporter.display_report()

    def createUtxos(self, node, addrs, amt):
        wallet = node.listunspent()
        wallet.sort(key=lambda x: x["amount"], reverse=True)

        # Create a LOT of UTXOs
        logging.info("Create lots of UTXOs...")
        n = 0
        group = min(100, amt)
        count = 0
        for w in wallet:
            count += group
            split_transaction(node, [w], addrs[n:group + n])
            n += group
            if n >= len(addrs):
                n = 0
            if count > amt:
                break
        self.sync_all()
        logging.info("mine blocks")
        node.generate(1)  # mine all the created transactions
        logging.info("sync all blocks and mempools")
        self.sync_all()

    def expectHeights(self, blockHeights, waittime=10):
        loop = 0
        count = []
        while loop < waittime:
            counts = [x.getblockcount() for x in self.nodes]
            if counts == blockHeights:
                return True  # success!
            time.sleep(1)
            loop += 1
            if ((loop % 30) == 0):
                logging.info("...waiting %s" % loop)
        return False

    def generateAndPrintBlock(self, node):
        hsh = node.generate(1)
        inf = node.getblock(hsh[0])
        logging.info("block %d size %d" % (inf["height"], inf["size"]))
        return hsh

def main(longTest):
    t = TestInterOpExcessive("debug", clientDirs, longTest)
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

def Test():
    main(False)

if __name__ == "__main__":
    if "--extensive" in sys.argv:
        longTest = True
        # we must remove duplicate 'extensive' arg here
        while True:
            try:
                sys.argv.remove('--extensive')
            except:
                break
        logging.info("Running extensive tests")
    else:
        longTest = False

    Test(longTest)
