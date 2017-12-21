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

class MyTest(BitcoinTestFramework):
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
        print("block count: %s" % ([ x.getblockcount() for x in self.nodes]))
        print("peers: %s" % ([ x.getpeerinfo() for x in self.nodes]))
        for n in self.nodes[0:3]:
            n.generate(10)
        time.sleep(5)
        #self.nodes[3].generate(10, coinbase) # classic is different
        print("block count: %s" % ([ x.getblockcount() for x in self.nodes]))



def Test():
    t = MyTest("debug", clientDirs)
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
