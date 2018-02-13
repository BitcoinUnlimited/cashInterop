#!/usr/bin/env python3
# Copyright (c) 2015-2017 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
import logging
import os
import sys
global reporter

#clientDirs = ["bucash", "abc", "xt", "classic"]
#clientSubvers = set(["Bitcoin ABC", "Classic", "Bitcoin XT", "BUCash"])
#clientDirs = ["bucash", "abc", "xt", "bucash"]
#clientSubvers = set(["Bitcoin ABC", "Bitcoin XT", "BUCash"])

clientDirs = ["bucash", "bucash", "bucash", "bucash"]
clientSubvers = set(["BUCash"])

#clientDirs = ["bucash", "bucash", "bucash", "bucash"]
#clientSubvers = set(["BUCash"])

def subverParseClient(s):
    """return the client name given a subversion string"""
    return s[1:].split(":")[0]


def verifyInterconnect(nodes, clientTypes=clientSubvers):
    """ Verify that every passed node is interconnected with all the other clients"""
    for n in nodes:
        connectedTo = set()
        myclient = subverParseClient(n.getnetworkinfo()["subversion"])

        pi = n.getpeerinfo()
        for p in pi:
            connectedTo.add(subverParseClient(p["subver"]))
        notConnectedTo = clientTypes - connectedTo
        notConnectedTo.discard(myclient)
        if notConnectedTo:
            print("Client %s is not connected to %s" % (myclient, str(notConnectedTo)))
        assert(len(notConnectedTo) == 0)

class TCReporter(object):
    """
    Test case Reporting class keeps track of test cases that have been executed.
    """
    def __init__(self):
        self.testcases = []
        self.failcount = 0
        self.passcount = 0

    def add_testcase(self, testcase):
        self.testcases.append(testcase)

    def display_report(self):
        for tc in self.testcases:
            if (tc['status'] == "pass"):
                self.passcount +=1
                msg = " ... " + "\n" + \
                    "Name: " + tc['name'] + "\n" + \
                    "Status: " + tc['status'] + "\n"
            else:
                self.failcount +=1
                msg = "\n" + "=================== Fail ===================" + "\n" + \
                    "Name: " + tc['name'] + "\n" + \
                    "File Name: " + str(tc['fname']) + "\n" + \
                    "Line: " + str(tc['line']) + "\n" + \
                    "Exception Type: " + str(tc['type']) + "\n" + \
                    "Message: " + str(tc['message'])+ "\n" + \
                    "Node 1: " + str(tc['node1']) + "\n" + \
                    "Node 2: " + str(tc['node2']) + "\n" + \
                    "Amount: " + str(tc['amount']) + "\n" + \
                    "Number Signature: " + str(tc['numsig']) + "\n" + \
                    "Status: " + tc['status'] + "\n" + \
                    "============================================" + "\n"

            logging.info(msg)
        
        result = "\n" +  "---------------------- " + "\n" + \
                "Total Pass : " + str(self.passcount) + "\n" + \
                "Total Fail : " + str(self.failcount) + "\n"
                    
        logging.info(result)
        # uncomment to inform CI for test failure
        # assert(self.failcount == 0)
        
reporter = TCReporter()

def assert_capture(*args, **kwargs):
    """
    Test function decorated by this decorator will ignore with AssertionError. 
    Instead test case results will be logged to the TCReporter.
    """
    def assert_decorator(func):
        def inner(*args, **kwargs):
            tc = {}
            tc['name'] = func.__name__
            tc['description'] = func.__doc__
            try:
                func(*args, **kwargs)
                tc['status'] = 'pass'
            except AssertionError as e:
                tc['status'] = 'fail'
                messages = e.args[0]
                tc['fname'] = messages["file_name"]
                tc['line'] = messages["line_num"]
                tc['type'] = messages["error_type"]
                tc['message'] = messages["error_msg"]
                tc['node1'] = messages["n1"]
                tc['node2'] = messages["n2"]
                tc['amount'] = messages["amount"]
                tc['numsig'] = messages["numsig"]
            reporter.add_testcase(tc)
        return inner
    return assert_decorator
