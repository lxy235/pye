# !/usr/bin/python
# coding=utf-8
#
# @Author: LiXiaoYu
# @Time: 2019-04-25
# @Info: Install Server.
# @exam: sudo python3 install.py

import os, sys, time
from distutils.sysconfig import get_python_lib

sp = get_python_lib()
print('::This site-package path is: %s' % sp)
time.sleep(1)

libfile = sp + '/eserver_library.pth'

if os.path.isfile(libfile):
	print('The python library install is successful!')
	sys.exit()

path = os.getcwd()+"/"
print('::Python library path is: %s' % path)
time.sleep(2)

if os.path.isfile(path):
	path = os.path.dirname(path)

io = open(libfile, 'w+')
io.write(path+"\n")
io.close()

print('::Write the <library.pth> in %s dir, File content is python library path' % sp)
time.sleep(1)

if os.path.isfile(libfile) == False:
	print('System install error: -1001')
	sys.exit()

print('...........................................')
print('.     [Welcome Use The Python Server]     .')
print('.                                         .')
print('. System Last Modify Time Is : 2019-04-25 .')
print('...........................................')

