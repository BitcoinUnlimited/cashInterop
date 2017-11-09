clientDirs = ["bucash", "abc", "xt", "classic"]
clientSubvers = set(["Bitcoin ABC", "Classic", "Bitcoin XT", "BUCash"])

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
            print("Client %s is not connected to %s" % myclient, str(notConnectedTo))
        assert(len(notConnectedTo) == 0)
