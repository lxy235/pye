#! /usr/bin env python
# coding:utf-8
# common config file

from espider.Env import *

# DB
if ENV == 'remote':
    DB = {
        "host": "192.144.146.211",
        "port": 3306,
        "user": "remoteuser",
        "passwd": "DvcMfeLFCsakGtyn",
        "db": "ladonnew_db",
        "charset": "utf8mb4"
    }

# DB
if ENV == 'testing':
    DB = {
        "host": "123.206.73.104",
        "port": 3306,
        "user": "txtest",
        "passwd": "aJxu1OGpYxaBsNKIXuYQ",
        "db": "ladon",
        "charset": "utf8mb4"
    }

# 开发环境
if ENV == 'devel':
    DB = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "passwd": "123456",
        "db": "ladonnew_db",
        "charset": "utf8mb4"
    }

if ENV == 'online':
    DB = {
        "host": "172.21.16.3",
        "port": 3306,
        "user": "sogou",
        "passwd": "aJxu1OGpYxaBsNKUkOkw",
        "db": "ladon",
        "charset": "utf8mb4"
    }

# Public TableMap
TableMap = {
    "ACCOUNT_TABLE": "account",
    "AGENCY_TABLE": "agencys",
    "AGENCY_COOKIE_TABLE": "agency_cookie"
}

# Status
AUDIT_OK = 2  # 审核通过
AUDIT_FAIL = 3  # 审核不通过

# Log Type
LOG_SYSTEM = 1  # 系统日志
LOG_QUEUE = 2  # 队列日志

# Log Level
CRITICAL = 50  # 临界值错误: 超过临界值的错误，例如一天24小时，而输入的是25小时这样
ERROR = 40  # 一般错误: 一般性错误
WARNING = 30  # 警告性错误: 需要发出警告的错误
INFO = 20  # 信息: 程序输出信息
DEBUG = 10  # 调试: 调试信息

LOG_RECORD = 1  # 是否开启日志记录
LOG_LEVEL = "DEBUG,ERROR,INFO"
LOG_FILE_SIZE = 1024  # 日志尺寸

# except
KD_ERROR = 0  # 程序异常

# 暂停时长
HUAWEI_REQUEST_TIME = 5
