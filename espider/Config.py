#! /usr/bin env python
# coding:utf-8
# common config file

from espider.Env import *

# 开发环境
if ENV == 'devel':
    DB = {
        "host": "10.200.21.239",
        "port": 3306,
        "user": "root",
        "passwd": "qwe123",
        "db": "pplive_ad",
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
    "AD_DPL_DEVICE_TABLE": "ad_dpl_device"
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
