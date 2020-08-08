#! /usr/bin env python
# coding:utf-8
import sys, getopt, time
import threading
from espider.app.aiqy.AiqyLogic import AiqyLogic
import requests as r
from xml.dom.minidom import parseString


class Aiqy(threading.Thread):
    def __init__(self, kwargs):
        threading.Thread.__init__(self, target=self.work, kwargs=kwargs)
        self.logic = AiqyLogic()
        self.derequrl = "http://de.as.pptv.com/ikandelivery/vast/3.0/?platform=1024&chid=10133943&clid=10133943&pos=300001&juid=0000000&ver=2.1.0.4&o=99990023"
        self.s = r.session()
        self.initDevice()

    # 初始化设备
    def initDevice(self):
        self.devices = AiqyLogic.getDevices(2000)

    def work(self, *args, **kwargs):
        totalreq = kwargs["totalreq"]
        print("每个客户端发送 %s 个请求" % totalreq)
        for i in range(totalreq):
            # 请求广告
            print("请求广告：%s" % self.derequrl)
            xmlstr = self.s.get(self.derequrl).text
            # 曝光请求
            jpUrl = self.getJpurl(xmlstr)
            if '' != jpUrl:
                print("曝光请求：%s" % jpUrl)
                self.s.get(jpUrl)
            # 每个请求暂停100毫秒
            time.sleep(0.1)

    def getJpurl(self, xmlstr):
        rootnode = parseString(xmlstr)
        jpUrl = ''
        trackingEventsNode = rootnode.getElementsByTagName("TrackingEvents")
        try:
            trackingChildNode = trackingEventsNode[0].childNodes
            for child in trackingChildNode[0:1]:
                jpUrl = child.firstChild.data
        except IndexError:
            print("节点trackingEventsNode为空")
        return jpUrl


if __name__ == "__main__":
    argv = sys.argv[1:]
    requests = clients = 0
    try:
        opts, args = getopt.getopt(argv, "hc:r:", ["clients=", "requests="])
    except getopt.GetoptError:
        print('python3 Aiqy.py -c <客户端个数> -r <请求个数>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('python3 Aiqy.py -c <客户端个数> -r <请求个数>')
            sys.exit()
        elif opt in ("-c", "--clients"):
            clients = int(arg)
        elif opt in ("-r", "--requests"):
            requests = int(arg)
    if 0 == clients or 0 == requests:
        print('python3 Aiqy.py -c <客户端个数> -r <请求个数>')
        sys.exit(2)
    totalreq = int(requests / clients)
    kwargs = {"totalreq": totalreq}
    for i in range(clients):
        pb = Aiqy(kwargs)
        pb.start()
