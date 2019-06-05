#! /usr/bin env python
# coding:utf-8

class HuaweiException(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self, code, msg)
        self.code = code
        self.msg = msg
