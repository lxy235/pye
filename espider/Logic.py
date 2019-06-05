#! /usr/bin env python
# coding:utf-8
# 业务逻辑

import espider.Config as Config
import pymysql


class Logic:
    def __init__(self):
        self.db = pymysql.connect(
            host=Config.DB.get("host"),
            port=Config.DB.get("port"),
            user=Config.DB.get("user"),
            passwd=Config.DB.get("passwd"),
            db=Config.DB.get("db"),
            charset=Config.DB.get("charset")
        )
        self.cursor = self.db.cursor(cursor=pymysql.cursors.DictCursor)
