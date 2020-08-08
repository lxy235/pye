#! /usr/bin env python
# coding:utf-8
# 业务逻辑

import espider.app.aiqy.Config as Config
import pymysql


class AiqyLogic:
    def __init__(self):
        self.db = pymysql.connect(
            host=Config.DB.get("host"),
            port=Config.DB.get("port"),
            user=Config.DB.get("user"),
            passwd=Config.DB.get("passwd"),
            db=Config.DB.get("db"),
            charset=Config.DB.get("charset")
        )
        self.cursor = self.db.cursor(cursor=pymysql.cursors.DictCursor);

    # 获取设备信息
    def getDevices(self, nums):
        sql = 'select `ip`, `dpid` from `%s` where `os` = "ios" limit %d' % (
            Config.TableMap.get('AD_DPL_DEVICE_TABLE'), nums)
        self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
        res = self.cursor.fetchall()
        if res:
            return res
        else:
            return []

    def getDefaultClients(self):
        return Config.DEFAULT_CLIENTS

    def getDefaultRequests(self):
        return Config.DEFAULT_REQUESTS
