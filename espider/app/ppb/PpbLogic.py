#! /usr/bin env python
# coding:utf-8
# 业务逻辑

import espider.app.ppb.Config as Config


class PpbLogic:
    def __init__(self):
        pass

    def getDefaultClients(self):
        return Config.DEFAULT_CLIENTS

    def getDefaultRequests(self):
        return Config.DEFAULT_REQUESTS