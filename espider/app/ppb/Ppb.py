#! /usr/bin env python
# coding:utf-8
import sys, getopt
import threading
import requests
import espider.Utils as Utils
from espider.app.ppb.PpbLogic import PpbLogic


class Ppb(threading.Thread):
    def __init__(self, kwargs):
        threading.Thread.__init__(self, target=self.work, kwargs=kwargs)
        self.logic = PpbLogic()

    def work(self, *args, **kwargs):
        Utils.D(kwargs)
        clients = kwargs['clients']
        requests = kwargs['requests']
        totalreq = requests / clients
        Utils.D("每个线程请求数: %s" % totalreq)


if __name__ == "__main__":
    argv = sys.argv[1:]
    requests = clients = 0
    try:
        opts, args = getopt.getopt(argv, "hc:r:", ["clients=", "requests="])
    except getopt.GetoptError:
        print('python3 Ppb.py -c <客户端个数> -r <请求个数>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('python3 Ppb.py -c <客户端个数> -r <请求个数>')
            sys.exit()
        elif opt in ("-c", "--clients"):
            clients = int(arg)
        elif opt in ("-r", "--requests"):
            requests = int(arg)
    if 0 == clients or 0 == requests:
        print('python3 Ppb.py -c <客户端个数> -r <请求个数>')
        sys.exit(2)
    kwargs = {"clients": clients, "requests": requests}
    pb = Ppb(kwargs)
    pb.start()
