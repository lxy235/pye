#! /usr/bin env python
# coding:utf-8
# common config file


from espider.Config import *

# Table
TableMap.update({
    "DATA_MANAGER_TABLE": "huawei_daily_report_account",
    "TASK_TABLE": "huawei_task",
    "TASK_REPORT_TABLE": "huawei_daily_report_task",
    "KEYWORD_TABLE": "huawei_keyword",
    "KEYWORD_DENY_TABLE": "huawei_deny_keyword",
    "KEYWORD_REPORT_TABLE": "huawei_daily_report_keyword",
    "HUAWEI_AGENCYS_TABLE": "huawei_agencys",
})

#媒体ID，需要根据实际媒体ID修改这个值
MEDIA_ID = 16

# 代理类型
agencyType = {
    'agencyuser': 1,  # 直客
    'agencys': 2  # 二代维护
}