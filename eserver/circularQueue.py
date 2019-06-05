# !/usr/bin/python
# coding=utf-8
#
# @Author: LiXiaoYu
# @Time: 2013-11-06
# @Info: queue Server.

import eserver.library.epoll as epoll
from eserver.library.config import Config
from eserver.app.queue.circularQueue import CircularQueue

# 获取队列服务配置
_config = Config("queue")

# 初始参数
_port = _config.get("queue.port")  # 服务端口
_app = CircularQueue()
# _allow_ip = ['192.168.1.100'] #白名单IP列表

# 开始服务
s = epoll.createServer(_app)
# s.setAllowIp(_allow_ip)
s.listen(_port)
