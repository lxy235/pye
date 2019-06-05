#! /usr/bin env python
# coding:utf-8

import espider.Utils as Utils
import traceback


class Spider:
    def log(self, code, msg, log_prefix):
        curdate = Utils.getCurDay()
        if isinstance(msg, (list)):
            logmsg = [
                curdate.center(100, "*"),
                "\ncode: %s" % code,
                "msg: %s" % "\n".join(msg)
            ]
        else:
            logmsg = [
                curdate.center(100, "*"),
                "\ncode: %s" % code,
                "msg: %s" % msg
            ]
        logmsg.extend([
            "exception: %s" % traceback.format_exc()
        ])
        msg = "\n".join(logmsg)
        Utils.log(msg=msg, log_prefix=log_prefix)
