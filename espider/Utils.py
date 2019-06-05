#!/usr/bin/python
# coding:utf-8
# 公共方法库

import time, datetime
import hashlib
import espider.Config as Config
from espider.Log import Log
import re
import os
from urllib import request


# 获取昨天的日期
def getYesterday():
    now_time = datetime.datetime.now()  # 返回的是本地时区的当前时间
    yesterday = now_time + datetime.timedelta(days=-1)  # 昨天的现在
    return yesterday.strftime("%Y-%m-%d")


# 获取当前日期
def getCurDay():
    nowtime = datetime.datetime.now()  # 返回的是本地时区的当前时间
    return nowtime.strftime("%Y-%m-%d")


# 获取当前日期
def getCurDayFormat(format='%Y-%m-%d'):
    nowtime = datetime.datetime.now()  # 返回的是本地时区的当前时间
    return nowtime.strftime(format)


# 获取两个日期之间的日期列表
def getDayDeltas(startdate="", enddate=""):
    if "" == startdate:
        return []
    if "" == enddate:
        enddate = startdate
    d1 = datetime.datetime.strptime(startdate, '%Y-%m-%d')
    d2 = datetime.datetime.strptime(enddate, '%Y-%m-%d')
    delta = d2 - d1
    days = delta.days + 1
    dates = []
    for i in range(days):
        deltaval = datetime.timedelta(days=i)
        ndays = d1 + deltaval
        dates.append(ndays.strftime('%Y-%m-%d'))
    return dates


# 获取毫秒数
def getMicSecond():
    t = time.time()
    return (int(round(t * 1000)))


def md5(src):
    m2 = hashlib.md5()
    m2.update(src)
    return m2.hexdigest()


def log(msg="", log_type=Config.LOG_SYSTEM, log_level=Config.ERROR, log_file="", log_prefix="log"):
    # 日志对象
    l = Log()
    if Config.LOG_RECORD and msg != "":
        # 写日志
        l.write(msg, log_file, log_prefix, log_type, log_level)


# 去字符串中的回车换行付
def denter(str=''):
    if '' == str:
        return ''
    return re.sub(r'[\r|\n|\r\n]', "", str.strip())


# 输出
def D(val):
    if Config.KD_DEBUG:
        print(val)


# 获取文件md5
def get_file_md5(file_path):
    md5 = None
    if os.path.isfile(file_path):
        f = open(file_path, 'rb')
        md5_obj = hashlib.md5()
        md5_obj.update(f.read())
        hash_code = md5_obj.hexdigest()
        f.close()
        md5 = str(hash_code).lower()
    return md5


# 下载素材到本地目录
def downloadPhoto(getImgUrl, filepath):
    # 创建目录
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    # 下载文件
    try:
        filename = filepath + md5(getImgUrl.encode())
        request.urlretrieve(getImgUrl, filename)
        return filename
    except:
        return ''


if __name__ == "__main__":
    print(getDayDeltas("2018-03-01", "2018-04-05"))
