#!/usr/bin/env python3
# Copyright (c) 2015-2018 The Bitcoin Unlimited developers
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
import shutil
import random
from binascii import hexlify
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from test_framework.script import *
from test_framework.blocktools import *
from test_framework.bunode import *
import test_framework.script as script
from interopUtils import *

if sys.version_info[0] < 3:
    raise "Use Python 3"
import logging
logging.basicConfig(format='%(asctime)s.%(levelname)s: %(message)s', level=logging.INFO, stream=sys.stdout)

NODE_BITCOIN_CASH = (1 << 5)
invalidOpReturn = hexlify(b'Bitcoin: A Peer-to-Peer Electronic Cash System')

SCRIPT_WORDS = b"this is junk data len125.this is junk data len125.this is junk data len125.this is junk data len125.this is junk data len125."
TX_DATA = '54686973206973203830206279746573206f6620746573742064617461206372656174656420746f20757365207570207472616e73616374696f6e20737061636520666173746572202e2e2e2e2e2e2e'
# number of iteration used to create a 250Kb of wasteful output  of SCRIPT_WORDS
#ITERATIONS_PER_250K = 250
ITERATIONS_PER_100K = 100


SIZE_1_MB = 1000000
SIZE_4_MB = 4000000
SIZE_8_MB = 8000000
SIZE_12_MB = 12000000
SIZE_20_MB = 20000000
SIZE_24_MB = 24000000
SIZE_28_MB = 28000000
SIZE_30_MB = 30000000
SIZE_31_MB = 31000000
SIZE_32_MB = 32000000

def bitcoinAddress2bin(btcAddress):
    """convert a bitcoin address to binary data capable of being put in a CScript"""
    # chop the version and checksum out of the bytes of the address
    return decodeBase58(btcAddress)[1:-4]

B58_DIGITS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def decodeBase58(s):
    """Decode a base58-encoding string, returning bytes"""
    if not s:
        return b''

    # Convert the string to an integer
    n = 0
    for c in s:
        n *= 58
        if c not in B58_DIGITS:
            raise InvalidBase58Error('Character %r is not a valid base58 character' % c)
        digit = B58_DIGITS.index(c)
        n += digit

    # Convert the integer to bytes
    h = '%x' % n
    if len(h) % 2:
        h = '0' + h
    res = binascii.unhexlify(h.encode('utf8'))

    # Add padding back.
    pad = 0
    for c in s[:-1]:
        if c == B58_DIGITS[0]:
            pad += 1
        else:
            break
    return b'\x00' * pad + res

def wastefulOutput(btcAddress):
    """ 
    Create useless data for the CScript. Txn block size of about 100KB
    There are 8 Vouts and 1 Vin in each transaction (see createrawtransaction).
    Input:
        btcAddress : BTC address - public key of the receive
    Return:
        CScript with useless data
    Warning: Creates outputs that can't be spent by bitcoind
    """
    data = b""
    for _ in range(ITERATIONS_PER_100K):
        data += SCRIPT_WORDS
    #logging.info("> Length of Junk data : %d" % len(data))
    
    # trim 31 chars due to extra agruments inputs to CScript  
    # len(bitcoinAddress2bin(btcAddress))) = 20 and the others addd up to be 11
    data = data[:-65]
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
    
    There are 8 outputs and 1 input in each transaction
    Input:
        inputs : Unspent Transaction Output (UTXO) from your wallet into the new transaction for the next recipients
        outputs : List of outputs to spend on addresses with payment amount
    Return:
        raw transaction with TxIn and 8 TxOut
    Warning: Creates outputs that can't be spent by bitcoind
    """
    if not type(inputs) is list:
        inputs = [inputs]

    tx = CTransaction()
    #print("Inputs : ", inputs)
    for i in inputs:
        tx.vin.append(CTxIn(COutPoint(i["txid"], i["vout"]), b"", 0xffffffff))
    for addr, amount in outputs.items():
        if addr == "data":
            tx.vout.append(CTxOut(0, CScript([OP_RETURN, unhexlify(amount)])))
        else:
            txout = CTxOut(amount * BTC, outScriptGenerator(addr))
            tx.vout.append(txout)
            #print(repr(txout))
    tx.rehash()
    return hexlify(tx.serialize()).decode("utf-8")

def generateTx(node, txBytes, addrs, data=None):
    """
    Create many transactions to fill up the required blockchain block size of MBs (from 1Mb to 32MB)

    Input:
        node : client object
        txBytes : number of bytes for the mined block with many transactions each is around 250KB
        addrs : list of addresses from getnewaddress() for the node
        data : one of the CTxout to be created if it's available from the input (eg. TX_DATA is used)
    Return:
        number signed raw transactions, and number of bytes in total (which is close to txBytes specified)
    """
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
        #print(">>>> UTXO  :", utxo)
        outp = {}
        # Make the tx bigger by adding addtl outputs so it validates faster
        payment = satoshi_round(utxo["amount"] / decimal.Decimal(8.0))
        #print(">>>>> UTXO amount = ", utxo["amount"])
        for x in range(0, 8):
            outp[addrs[(count + x) % len(addrs)]] = payment
        if data:
            outp["data"] = data
        txn = createrawtransaction([utxo], outp, wastefulOutput)
        signedtxn = node.signrawtransaction(txn)
        size += len(binascii.unhexlify(signedtxn["hex"]))
        node.sendrawtransaction(signedtxn["hex"])
    logging.info("%d tx %d length" % (count, size))
    decimal.getcontext().prec = decContext
    return (count, size)

def mostly_sync_mempools(rpc_connections, difference=50, wait=1,verbose=1):
    """
    Wait until everybody has the most of the same transactions in their memory
    pools. There is no guarantee that mempools will ever sync due to the
    filterInventoryKnown bloom filter.
    """
    iterations = 0
    while True:
        iterations+=1
        pool = set(rpc_connections[0].getrawmempool())
        num_match = 1
        poolLen = [len(pool)]
        for i in range(1, len(rpc_connections)):
            tmp = set(rpc_connections[i].getrawmempool())
            if tmp == pool:
                num_match = num_match+1
            if iterations > 10 and len(tmp.symmetric_difference(pool)) < difference:
                num_match = num_match+1
            poolLen.append(len(tmp))
        if verbose:
            logging.info("sync mempool: " + str(poolLen))
        if num_match == len(rpc_connections):
            break
        time.sleep(wait)

def get_bestblockhash(node, nodeId):
    best_blockhash = node.getbestblockhash()
    block_size = node.getblock(best_blockhash, True)['size']
    best_blockhash = int(best_blockhash, 16)
    #logging.info("> Node%d  block_size = %d"  %(nodeId, block_size))
    #logging.info("> Blockhash = %s"  %best_blockhash)
    return block_size

@assert_capture()
def test_disconnect_bucash_node(self):
    """ 
    Test system properly disconnected bucash node
    
    """    
    logging.info(">>> Entered : test_disconnect_bucash_node \n")
    try:
        info = self.nodes[0].getnetworkinfo()

        # Both BUcash and BU should connect to a normal BU node
        bunode = BasicBUNode()
        bunode.connect(0,'127.0.0.1', p2p_port(1), self.nodes[1])
        NetworkThread().start()  # Start up network handling in another thread
        bunode.cnxns[0].wait_for_verack()

        buCashNode = BasicBUCashNode()
        buCashNode.connect(0,'127.0.0.1', p2p_port(0), self.nodes[0])
        if int(info["localservices"],16)&NODE_BITCOIN_CASH:
            try: # Accept BU cash nodes if running BTC node
                buCashNode.cnxns[0].wait_for_buverack()
            except DisconnectedError:
                assert(not "should not have disconnected a bitcoin cash node")
        else:
            try: # do not accept BU cash nodes if running BTC node
                buCashNode.cnxns[0].wait_for_buverack()
                assert(not "should have disconnected a bitcoin cash node")
            except DisconnectedError:
                logging.info("properly disconnected bucash node")
    except (Exception, JSONRPCException) as e1:
        logging.info(e1)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e1 ), \
                       "n1" : "N/A", "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})

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
    except AssertionError as err:
        #print(type(err).__name__)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": "N/A", \
                       "n1" : "N/A", "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})

@assert_capture()
def test_set_values_cmdline(self, fblksize=32000000, exblksize=32000000):
    """ 
    Test setting system values of MG and EB

    Input:
        self : test object
        fblksize : fork Block Size
        exblksize : fork Excessive Block Size
    Assertions:
        fail to set the specified values
    """    
    logging.info(">>> Entered : test_set_values_cmdline \n")
    try:
        n = self.nodes[0]
        now = int(time.time())
        n.set("mining.forkTime=%d" % now)

        n.set("mining.forkExcessiveBlock=%d" % exblksize)
        n.set("mining.forkBlockSize=%d" % fblksize)

        n = self.nodes[1]
        n.set("mining.forkTime=%d" % now, "mining.forkExcessiveBlock=%d" % exblksize, "mining.forkBlockSize=%d" % fblksize)

        # Verify that the values were properly set
        for n in self.nodes[0:2]:
            t = n.get("mining.fork*")
            assert(t['mining.forkBlockSize'] == fblksize)
            assert(t['mining.forkExcessiveBlock'] == exblksize)
            assert(t['mining.forkTime'] == now)

        self.nodes[3].set("mining.forkTime=0")
        nodeInfo = self.nodes[3].getnetworkinfo()

        # if this is a bitcoin cash build, we need to do the cash defaults on our old chain node
        if int(nodeInfo["localservices"],16)&NODE_BITCOIN_CASH:
            self.nodes[3].set("net.excessiveBlock=1000000")  # keep it on the 1MB chain
            self.nodes[3].set("net.onlyRelayForkSig=False")
            self.nodes[2].set("net.excessiveBlock=1000000")  # keep it on the 1MB chain
            self.nodes[2].set("net.onlyRelayForkSig=False")
        #print("Returning NOW = ", now)
        self.forkTime = now
    except (Exception, JSONRPCException) as e1:
        logging.info(e1)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e1 ), \
                       "n1" : "N/A", "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})

@assert_capture()
def test_generate_badblock(node):
    """ 
    Test to generate a bad block - too small exception

    Input:
        addrs : addresses for UTXOs
        numTxns : number of transactions generate for different block size 
                  - For 1MB (need 10 txns), 2MB (20 txns), ... , 32MB (320 txns) 
        data : invalid data for a bad block
    Exception:
        Bad Block is thrown
    """
    # TEST 1:   the client refuses to make a < 1MB fork block
    try:
        ret = node.generate(1)
        logging.info(ret)
        assert(0)  # should have raised exception
    except AssertionError as e1:
        logging.info(e1)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e1 ), \
                       "n1" : "N/A", "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})         
    except JSONRPCException as e:
        assert("bad-blk-too-small" in e.error["message"])
        #logging.info(">> PASS : %s " %e.error["message"])

@assert_capture()
def test_generate_wrong_fork(node, txBytes, addrs, data=invalidOpReturn):
    """ 
    Test to generate a work fork exception

    Input:
        addrs : addresses for UTXOs
        numTxns : number of transactions generate for different block size 
                  - For 1MB (need 10 txns), 2MB (20 txns), ... , 32MB (320 txns) 
        data : invalid data for a bad block
    Exception:
        Wrong fork is thrown
    """
    # TEST that the client refuses to include invalid op return txns in the first block
    generateTx(node, 950000, addrs, data=TX_DATA)
    try:
        generateTx(node, txBytes, addrs, data)
        assert(0)  # should have raised exception
    except AssertionError as e1:
        logging.info(e1)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e1 ), \
                       "n1" : "N/A", "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})
    except JSONRPCException as e:
        #print(">>>>>> E2 :\n", e.error["message"])
        assert("wrong-fork" in e.error["message"])

@assert_capture()
def test_generate_largeblock(self, nodeId1, nodeId2, txBytes, addrs, data=TX_DATA):
    """ 
    Test to cause excessive block generated

    Input:
        addrs : addresses for UTXOs
        numTxns : number of transactions generate for different block size 
                  - For 1MB (need 10 txns), 2MB (20 txns), ... , 32MB (320 txns) 
        data : invalid data for a bad block
    Return:
        N/A
    Exception:
        Excessive block generated is thrown if MG > EB in settings
    """
    try:
        count, size = generateTx(self.nodes[nodeId1], txBytes, addrs, data)
        blkHash = self.nodes[nodeId1].generate(1)[0]
        blkInfo = self.nodes[nodeId1].getblock(blkHash)
        logging.info("> blkInfo[size] =  %d " %blkInfo["size"])
        assert(blkInfo["size"] >= txBytes)
        
        self.nodes[nodeId1].generate(1) # should consume all the rest of the spendable tx
        # The unspendable tx I created on node 0 should not have been relayed to node 1
        mempool = self.nodes[nodeId1].getmempoolinfo()
        logging.info(">> Node 1 - mempool size : %d " %mempool["size"])
        block_size1 = get_bestblockhash(self.nodes[nodeId1], nodeId1)
        #sync_blocks(self.nodes[0:3])
        sync_blocks(self.nodes[0:2])
        
        mempool = self.nodes[nodeId2].getmempoolinfo()
        logging.info(">> Node 0 - mempool size : %d " %mempool["size"])
        block_size0 = get_bestblockhash(self.nodes[nodeId2], nodeId2)
        # after sync _blocks, should be equal
        assert_equal(block_size1, block_size0)

    except (Exception, JSONRPCException) as e1:
        logging.info(e1)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e1 ), \
                       "n1" : "N/A", "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})

@assert_capture()
def test_generate_sighash(self, nodeId1, nodeId2, txBytes, addrs, data=TX_DATA):
    """ 
    Test to cause excessive block generated

    Input:
        addrs : addresses for UTXOs
        numTxns : number of transactions generate for different block size 
                  - For 1MB (need 10 txns), 2MB (20 txns), ... , 32MB (320 txns) 
        data : invalid data for a bad block
    Return:
        N/A
    Exception:
        Excessive block generated is thrown
    """
    try:
        # generate blocks and ensure that the other node syncs them
        self.nodes[1].generate(1)
        wallet = self.nodes[1].listunspent()
        utxo = wallet.pop()
        #print("\n UTXO = \n", utxo)
        txn = createrawtransaction([utxo], {self.addrs1[0]:utxo["amount"]}, wastefulOutput)
        signedtxn = self.nodes[1].signrawtransaction(txn, None, None, "ALL|NOFORKID")
        signedtxn2 = self.nodes[1].signrawtransaction(txn, None, None,"ALL|FORKID")
        assert(signedtxn["hex"] != signedtxn2["hex"])  # they should use a different sighash method

        try:
            self.nodes[3].sendrawtransaction(signedtxn2["hex"])
            #self.nodes[3].sendrawtransaction(signedtxn["hex"])    # no exception
            #assert(0) # should failed
        except JSONRPCException as e:
            assert("mandatory-script-verify-flag-failed" in e.error["message"])
            logging.info("PASS: New sighash rejected from 1MB chain")

        self.nodes[1].sendrawtransaction(signedtxn2["hex"])
        try:
           self.nodes[1].sendrawtransaction(signedtxn["hex"])
        except JSONRPCException as e:
            assert("txn-mempool-conflict" in e.error["message"])
            logging.info("PASS: submission of new and old sighash txn rejected")

        self.nodes[1].generate(1)
        # connect 1 to 3 to propagate these transactions
        connect_nodes(self.nodes[1],3)
        # Issue sendtoaddress commands using both the new sighash and the old and ensure that first fails, second works.
        self.nodes[1].set("wallet.useNewSig=False")
        try:
            #txhash2 = self.nodes[1].sendtoaddress(self.addrs[0], 2.345)
            txhash2 = self.nodes[1].sendtoaddress(self.addrs0[0], 0.345)
            assert( not "fork must use new sighash")
        except JSONRPCException as e:
            assert("transaction was rejected" in e.error["message"])    # TODO : check if error is correct?
            logging.info("PASS: New sighash rejected from 1MB chain")
            txhash2 = self.nodes[3].sendtoaddress(self.addrs0[0], 2.345)

        self.nodes[1].set("wallet.useNewSig=True")
        # produce a new sighash transaction using the sendtoaddress API
        txhash = self.nodes[1].sendtoaddress(self.addrs0[0], 1.234)
        rawtx = self.nodes[1].getrawtransaction(txhash)
        try:
            self.nodes[3].sendrawtransaction(rawtx)
            print("ERROR!") # error assert(0)
        except JSONRPCException as e:
            assert("mandatory-script-verify-flag-failed" in e.error["message"])
            logging.info("PASS: New sighash rejected from 1MB chain")
    
    except JSONRPCException as e:
        #print('>>>> Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        raise AssertionError({"file_name": fname, "line_num": exc_tb.tb_lineno, \
                       "error_type": exc_type.__name__, "error_msg": str( e.error["message"]), \
                       "n1" : n, "n2" : "N/A", "amount" : "N/A", "numsig" : "N/A"})

class MyTest(BitcoinTestFramework):
    def __init__(self, build_variant, client_dirs, extended=False):
        BitcoinTestFramework.__init__(self)
        self.buildVariant = build_variant
        self.clientDirs = client_dirs
        self.extended = extended
        self.forkTime = 0
        self.unspendableTx = 0
        self.bins = [ os.path.join(base_dir, x, self.buildVariant, "src","bitcoind") for x in clientDirs]
        logging.info(self.bins)

    # work by itself
    def setup_network(self, split=False):
        self.nodes = []
        self.nodes.append(start_node(0, self.options.tmpdir, ["-rpcservertimeout=0"], timewait=60 * 10))
        self.nodes.append(start_node(1, self.options.tmpdir, ["-rpcservertimeout=0"], timewait=60 * 10))
        self.nodes.append(start_node(2, self.options.tmpdir, ["-rpcservertimeout=0"], timewait=60 * 10))
        self.nodes.append(start_node(3, self.options.tmpdir, ["-rpcservertimeout=0"], timewait=60 * 10))
        interconnect_nodes(self.nodes)
        self.is_network_split = False
        self.sync_all()

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
        logging.info("mine blocks")
        node.generate(1)  # mine all the created transactions
        logging.info("sync all blocks and mempools")
        self.sync_all()

    def run_test(self):
        # this test is mean to test fork scenarios starting from mainchain nodes.
        nodeInfo = self.nodes[0].getnetworkinfo()
        if int(nodeInfo["localservices"],16)&NODE_BITCOIN_CASH:
            return

        test_disconnect_bucash_node(self)

        # Creating UTXOs needed for building tx for large blocks
        NUM_ADDRS = 50
        logging.info("Creating addresses...")
        self.nodes[0].keypoolrefill(NUM_ADDRS)
        self.nodes[1].keypoolrefill(NUM_ADDRS)
        self.addrs0 = [self.nodes[0].getnewaddress() for _ in range(NUM_ADDRS)]
        self.addrs1 = [self.nodes[1].getnewaddress() for _ in range(NUM_ADDRS)]
        self.addrs2 = [self.nodes[2].getnewaddress() for _ in range(NUM_ADDRS)]
        self.addrs3 = [self.nodes[3].getnewaddress() for _ in range(NUM_ADDRS)]
        logging.info("creating utxos")

        self.nodes[1].generate(5)
        sync_blocks(self.nodes)

        self.createUtxos(self.nodes[0], self.addrs0, 3000)
        for i in range(0,2):
            self.createUtxos(self.nodes[1], self.addrs1, 3000)
        self.createUtxos(self.nodes[2], self.addrs2, 3000)
        self.createUtxos(self.nodes[3], self.addrs3, 3000)
        sync_blocks(self.nodes)

        test_default_values(self)
        # create Excessive block generated when this condition is met
        test_set_values_cmdline(self, fblksize=SIZE_32_MB, exblksize=SIZE_31_MB)
        base = [x.getblockcount() for x in self.nodes]
        assert_equal(base, [base[0]] * 4)

        for i in range(0,15):
          self.nodes[3].generate(1)
          time.sleep(1)

        sync_blocks(self.nodes[2:])
        sync_blocks(self.nodes[0:2])

        nMedianTimeSpan = 11  # from chain.h
        projectedForkHeight = int(base[0] + nMedianTimeSpan / 2 + 1)

        counts = [x.getblockcount() for x in self.nodes]
        logging.info("waiting for block: %d" % projectedForkHeight)
        while counts[0] != projectedForkHeight:
            counts = [x.getblockcount() for x in self.nodes]
            logging.info(counts)
            time.sleep(1)

        assert(counts[0] < counts[2])
        assert(counts[1] < counts[3])
        assert(counts[0] == counts[1])
        assert(counts[2] == counts[3])

        # TEST 1:   the client refuses to make a < 1MB fork block
        test_generate_badblock(self.nodes[0])

        # TEST 2:  the client refuses to include invalid op return txns in the first block
        test_generate_wrong_fork(self.nodes[0], 100000, self.addrs0, data=invalidOpReturn)

        logging.info("Building > 1MB block...")
        node = self.nodes[0]

        # TEST REQ-3: generate a large block
        generateTx(node, 100000, self.addrs0)
        mostly_sync_mempools(self.nodes[0:2],difference=100, wait=2)

        commonAncestor = node.getbestblockhash()
        node.generate(1)
        forkHeight = node.getblockcount()
        print("forkHeight: %d" % forkHeight)
        # Test that the forked nodes accept this block as the fork block
        sync_blocks(self.nodes[0:2])
        # counts = [ x.getblockcount() for x in self.nodes[0:2] ]
        counts = [x.getblockcount() for x in self.nodes]
        logging.info(counts)
        assert(counts[0] < counts[2])
        assert(counts[1] < counts[3])
        assert(counts[0] == counts[1])
        assert(counts[2] == counts[3])

        # Node 0 and 1 are forking nodes
        id1 = 1
        id2 = 0
        test_generate_largeblock(self, id1, id2, SIZE_1_MB, self.addrs0, data=TX_DATA)
        test_generate_largeblock(self, id1, id2, SIZE_4_MB, self.addrs0, data=TX_DATA)
        test_generate_largeblock(self, id1, id2, SIZE_8_MB, self.addrs0, data=TX_DATA)
        test_generate_largeblock(self, id1, id2, SIZE_12_MB, self.addrs0, data=TX_DATA)
        test_generate_largeblock(self, id1, id2, SIZE_20_MB, self.addrs0, data=TX_DATA)
        test_generate_largeblock(self, id1, id2, SIZE_24_MB, self.addrs0, data=TX_DATA)
        test_generate_largeblock(self, id1, id2, SIZE_28_MB, self.addrs0, data=TX_DATA)
        # will cause CreateNewBlock: Excessive block generated:  (code 0) 
        # because of  test_set_values_cmdline(self, fblksize=SIZE_32_MB, exblksize=SIZE_31_MB) 
        test_generate_largeblock(self, id1, id2, SIZE_32_MB, self.addrs0, data=TX_DATA) 
        reporter.display_report()

def main(longTest):
    t = MyTest("debug", clientDirs, longTest)
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

def Test(longTest=False):
    if str(longTest).lower() == 'true':
        main(True)
    else:
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