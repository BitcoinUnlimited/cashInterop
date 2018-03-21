import sys
import logging
import types
import copy
import os
import os.path
import test_framework.util

def BU_setMay2018ForkTime(self, secondsSinceEpoch):
    self.set("mining.forkMay2018Time=%d" % secondsSinceEpoch)
    return None

def ABC_setMay2018ForkTime(self, secondsSinceEpoch):
    logging.error("%s not implemented", sys._getframe().f_code.co_name)
    return None

def XT_setMay2018ForkTime(self, secondsSinceEpoch):
    logging.error("%s not implemented", sys._getframe().f_code.co_name)
    return None


def addInteropApis(node, bin):
    if "bucash" in bin:
        node.clientName = "bucash"
        node.setMay2018ForkTime = types.MethodType(BU_setMay2018ForkTime,node)
    elif "abc" in bin:
        node.clientName = "abc"
        pass
    elif "xt" in bin:
        node.clientName = "xt"
        pass
    else:
        node.clientName = "unknown"
        pass
    return node

configXlat = {
    "forkMay2018time" : { "bucash" : "mining.forkMay2018Time",
                          "xt" : "thirdhftime",
                          "abc" : "monolithactivationtime" },
    "limitfreerelay" : { "bucash" : "",
                         "xt" : "",
                         "abc" : "limitfreerelay" }
}

def start(datadir, clientDirs, bins, conf):
    nodes = []
    i = 0
    for name, executable in zip(clientDirs, bins):
        confDict = copy.copy(conf)
        for k, xlat in configXlat.items():  # convert "standard" conf options to client specific
            if k in confDict:
                val = confDict[k]
                del confDict[k]
                if xlat[name]:
                    confDict[xlat[name]] = val
        test_framework.util.initialize_datadir(datadir, i, confDict)
        node = test_framework.util.start_node(i, datadir, binary=executable)
        addInteropApis(node, name)
        i+=1
        nodes.append(node)
    return nodes
