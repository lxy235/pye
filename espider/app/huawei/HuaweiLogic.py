#! /usr/bin env python
# coding:utf-8
# 业务逻辑

import espider.Config as Config
import pymysql
import json
import time
import espider.Utils as Utils
from espider.app.huawei.HuaweiException import HuaweiException


class HuaweiLogic:
    def __init__(self, agencyId=0, mediaId=0):
        self.agencyId = agencyId
        self.mediaId = mediaId
        self.db = pymysql.connect(
            host=Config.DB.get("host"),
            port=Config.DB.get("port"),
            user=Config.DB.get("user"),
            passwd=Config.DB.get("passwd"),
            db=Config.DB.get("db"),
            charset=Config.DB.get("charset")
        )
        self.cursor = self.db.cursor(cursor=pymysql.cursors.DictCursor);

    # 获取客户列表
    def getTokens(self, agencyId):
        sql = 'select * from %s where `agency_id` = %d' % (
            Config.TableMap.get('AGENCY_COOKIE_TABLE'), agencyId)
        # print "Query: %s" % sql
        self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
        res = self.cursor.fetchone()
        if res:
            res = json.loads(res.get("json_data", "{}"), encoding="utf-8")
            return res.get("token_agency", "")
        else:
            return ""

    # 获取客户列表
    def getAccounts(self):
        sql = 'select * from %s where `media_id` = %d and `agency_id` = %d' % (
            Config.TableMap.get('ACCOUNT_TABLE'), self.mediaId, self.agencyId)
        # print "Query: %s" % sql
        self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
        res = self.cursor.fetchall()
        if res:
            return res
        else:
            return []

    # 获取任务列表
    def getTaskIdList(self):
        sql = 'select * from %s where `agency_id` = %d' % (
            Config.TableMap.get('TASK_TABLE'), self.agencyId)
        # print "Query: %s" % sql
        self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
        res = self.cursor.fetchall()
        taskIdList = {}
        for i in res:
            if i['account_id'] not in taskIdList:
                taskIdList[i['account_id']] = []
            taskIdList[i['account_id']].append(i['task_id'])
        return taskIdList

    # 获取代理商列表
    def getAgencys(self, agencytype):
        sql = 'select * from %s where `media_id` = %d and `usable_status` = 1 and `agency_ext`->"$.agency_type" = %d' % (
            Config.TableMap.get('AGENCY_TABLE'), Config.MEDIA_ID, Config.agencyType.get(agencytype, 1))
        # print "Query: %s" % sql
        self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
        res = self.cursor.fetchall()
        if res:
            return res
        else:
            return []

    # 批量导入客户
    def importAccount(self, jsonresult):
        totalCount = jsonresult.get("totalCount", 0)
        accounts = jsonresult.get("accounts", [])
        if 0 == totalCount or 0 == len(accounts):
            return
        # 入库account表
        for i in accounts:
            accountId = i.get('accountId', 0)

            sql = 'select * from %s where `account_id_from_media` = "%s" and agency_id = %d' % (
                Config.TableMap.get('ACCOUNT_TABLE'), accountId, self.agencyId)
            Utils.D("Query: %s" % sql)
            res = self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
            status = Config.AUDIT_OK if i['status'] == 'AUDITED' else Config.AUDIT_FAIL
            accountExt = json.dumps({
                "createTime": i.get('createTime', ''),
                "lastDaySpent": i.get('lastDaySpent', ''),
                "todaySpent": i.get('todaySpent', ''),
                "status": i.get('status', '')
            })
            valuesTuple = (
                i.get('corpName', ''),
                status,
                self.agencyId,
                self.mediaId,
                i.get('balance', 0),
                accountId,
                accountExt,
                ''
            )
            xx = time.strftime("%Y%m%d", time.localtime())
            batch = self.api.getHbaseConn("account")
            rowkey = '{}|{}|{}|{}|{}'.format(str(accountId)[-1:], xx, self.mediaId, accountId, self.agencyId)
            data_list = json.dumps(accountExt)
            batch.put(row=rowkey, data={'info:data': str(data_list)})
            batch.send()
            try:
                if (res):
                    # update
                    sets = {
                        "`account_fullname` = '%s'" % valuesTuple[0],
                        "`usable_status` = %s" % valuesTuple[1],
                        "`agency_id` = %s" % valuesTuple[2],
                        "`media_id` = %s" % valuesTuple[3],
                        "`funds` = %.2f" % valuesTuple[4],
                        "`account_id_from_media` = '%s'" % valuesTuple[5],
                        "`account_ext` = '%s'" % valuesTuple[6],
                        "`usable_log` = '%s'" % valuesTuple[7],
                    }
                    sql = "update %s set %s where `account_id_from_media` = '%s'" % (
                        Config.TableMap.get('ACCOUNT_TABLE'), ",".join(sets), accountId)
                    Utils.D("Update: %s" % sql)
                else:
                    # insert
                    values = "'%s',%s,%s,%s,%.2f,'%s','%s','%s'" % valuesTuple
                    sql = "insert into %s (`account_fullname`, `usable_status`, `agency_id`, `media_id`, `funds`, `account_id_from_media`, `account_ext`, `usable_log`) values (%s)" % (
                        Config.TableMap.get('ACCOUNT_TABLE'), values)
                    Utils.D("Insert: %s" % sql)
                self.cursor.execute(sql)
            except:
                raise HuaweiException(Config.KD_ERROR, [
                    "sql: %s" % sql,
                    "value: %s" % json.dumps(valuesTuple)
                ])

        # 提交事物
        self.db.commit()

    # 数据管理导入
    def importDataManager(self, jsonresult, startdate):
        totalCount = jsonresult.get("totalCount", 0)
        reportDetail = jsonresult.get("reportDetail", [])
        if 0 == totalCount or 0 == len(reportDetail):
            return
        # [1:]从第二条记录开始循环，第一条记录时报表的汇总信息
        for i in reportDetail[1:]:
            accountId = i.get('accountId', 0)

            sql = 'select * from %s where `account_id` = "%s" and `agency_id` = %d and `ymd` = "%s"' % (
                Config.TableMap.get('DATA_MANAGER_TABLE'), accountId, self.agencyId, startdate)
            Utils.D("Query: %s" % sql)
            res = self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
            jsondata = json.dumps({
                "cashSpend": i.get('cashSpend', ''),  # 现金消耗
                "totalSpend": i.get('totalSpend', ''),  # 总消耗
                "exchangeSpend": i.get('exchangeSpend', ''),  # 置换消耗
                "giftSpend": i.get('giftSpend', ''),  # 赠送消耗
                "totalImp": i.get('totalImp', ''),  # 曝光量
                "totalDownload": i.get('totalDownload', ''),  # 下载量
            }, encoding="utf-8")
            valuesTuple = (
                accountId,
                self.agencyId,
                self.mediaId,
                jsondata,
                i.get('corpName', ''),
                startdate
            )

            batch = self.api.getHbaseConn("huawei_daily_report_account")
            rowkey = '{}|{}|{}|{}|{}'.format(str(accountId)[-1:], startdate.replace('-', ''), self.mediaId, accountId,
                                             self.agencyId)
            data_list = json.dumps(jsondata)
            batch.put(row=rowkey, data={'info:data': str(data_list)})
            batch.send()

            try:
                if (res):
                    # update
                    sets = {
                        "`account_id` = '%s'" % valuesTuple[0],
                        "`agency_id` = %s" % valuesTuple[1],
                        "`media_id` = %s" % valuesTuple[2],
                        "`jsondata` = '%s'" % valuesTuple[3],
                        "`corpname` = '%s'" % valuesTuple[4],
                    }
                    sql = "update %s set %s where `account_id` = '%s' and `agency_id` = %s and `ymd` = '%s'" % (
                        Config.TableMap.get('DATA_MANAGER_TABLE'), ",".join(sets), accountId, self.agencyId, startdate)
                    Utils.D("Update: %s" % sql)
                else:
                    # insert
                    values = "'%s',%s,%s,'%s','%s','%s'" % valuesTuple
                    sql = "insert into %s (`account_id`, `agency_id`, `media_id`, `jsondata`, `corpname`, `ymd`) values (%s)" % (
                        Config.TableMap.get('DATA_MANAGER_TABLE'), values)
                    Utils.D("Insert: %s" % sql)
                self.cursor.execute(sql)
            except:
                raise HuaweiException(Config.KD_ERROR, [
                    "sql: %s" % sql,
                    "value: %s" % json.dumps(valuesTuple)
                ])

        # 提交事物
        self.db.commit()

    # 导入推广任务列表
    def importTaskList(self, jsonresult, accountId):
        totalCount = jsonresult.get('totalCount', 0)
        taskList = jsonresult.get('taskList', [])
        if 0 == totalCount or 0 == len(taskList):
            return
        for i in taskList:
            sql = 'select * from %s where `account_id` = "%s" and `agency_id` = %d and `task_id` = %d' % (
                Config.TableMap.get('TASK_TABLE'), accountId, self.agencyId, int(i['taskID']))
            Utils.D("Query: %s" % sql)
            res = self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
            status = Config.AUDIT_OK if i['status'] == 'RUN' else Config.AUDIT_FAIL
            jsondata = json.dumps({
                "auditLastFlag": i.get('auditLastFlag', ''),
                "auditLastTime": i.get('auditLastTime', ''),
                "budget": i.get('budget', ''),
                "contentStatus": i.get('contentStatus', ''),
                "dailyLimit": i.get('dailyLimit', ''),
                "download": i.get('download', ''),
                "downloadRate": i.get('downloadRate', ''),
                "endDate": i.get('endDate', ''),
                "impression": i.get('impression'),
                "mediaChannel": i.get('mediaChannel', ''),
                "price": i.get('price', ''),
                "pricingType": i.get('pricingType', ''),
                "rtbStatus": i.get('rtbStatus', ''),
                "schedule": i.get('schedule', ''),
                "spent": i.get('spent', ''),
                "startDate": i.get('startDate', ''),
                "todaySpent": i.get('todaySpent', ''),
                "status": i.get('status', '')
            }, encoding="utf-8")
            valuesTuple = (
                status,
                int(i.get('taskID', 0)),
                i.get('taskName', ''),
                int(i.get('contentAppId', 0)),
                i.get('contentAppName', ''),
                jsondata,
                accountId,
                self.agencyId,
                self.mediaId,
            )

            try:
                if (res):
                    # update
                    task_id = valuesTuple[1]
                    sets = {
                        "`status` = %s" % valuesTuple[0],
                        "`task_id` = %s" % task_id,
                        "`task_name` = '%s'" % valuesTuple[2],
                        "`app_id` = %s" % valuesTuple[3],
                        "`app_name` = '%s'" % valuesTuple[4],
                        "`jsondata` = '%s'" % valuesTuple[5],
                        "`account_id` = '%s'" % valuesTuple[6],
                        "`agency_id` = %s" % valuesTuple[7],
                        "`media_id` = %s" % valuesTuple[8],
                    }
                    sql = "update %s set %s where `account_id` = '%s' and `agency_id` = %s and `task_id` = %s" % (
                        Config.TableMap.get('TASK_TABLE'), ",".join(sets), accountId, self.agencyId, task_id)
                    Utils.D("Update: %s" % sql)
                else:
                    # insert
                    values = "%s, %s, '%s', %s, '%s', '%s', '%s', %s, %s" % valuesTuple
                    sql = "insert into %s (`status`, `task_id`, `task_name`, `app_id`, `app_name`, `jsondata`, `account_id`, `agency_id`, `media_id`) values (%s)" % (
                        Config.TableMap.get('TASK_TABLE'), values)
                    Utils.D("Insert: %s" % sql)
                self.cursor.execute(sql)
            except:
                raise HuaweiException(Config.KD_ERROR, [
                    "sql: %s" % sql,
                    "value: %s" % json.dumps(valuesTuple)
                ])

        # 提交事物
        self.db.commit()

    # 导入推广任务报表
    def importTaskReport(self, jsonresult, accountId, startdate):
        totalCount = jsonresult.get('totalCount', 0)
        taskDateList = jsonresult.get('taskDateList', [])
        if 0 == totalCount or 0 == len(taskDateList):
            return
        for i in taskDateList:
            jsondata = json.dumps({
                "clickRate": i.get('clickRate', ''),
                "download": i.get('download', ''),
                "downloadAvgMoney": i.get('downloadAvgMoney', ''),
                "downloadRate": i.get('downloadRate', ''),
                "impression": i.get('impression', ''),
                "money": i.get('money', ''),
                "pricingType": i.get('pricingType', ''),
                "siteSlotName": i.get('siteSlotName', ''),
                "slotName": i.get('slotName', ''),
            }, encoding="utf-8")
            taskName = i.get('taskName', '')
            date = i.get('date', '')
            appName = i.get('appName', '')
            taskId = str(i.get('taskId', ''))
            keyword_str = taskName + date + appName + taskId + accountId
            report_task_id = Utils.md5(keyword_str.encode("utf-8"))
            valuesTuple = (
                report_task_id,
                int(i.get('taskId', 0)),
                taskName,
                appName,
                jsondata,
                date,
                accountId,
                self.agencyId,
                self.mediaId,
                startdate
            )

            sql = 'select * from %s where `account_id` = "%s" and `agency_id` = %d and `report_task_id` = "%s" and `ymd` = "%s"' % (
                Config.TableMap.get('TASK_REPORT_TABLE'), accountId, self.agencyId, report_task_id, startdate)
            Utils.D("Query: %s" % sql)
            res = self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0

            try:
                if (res):
                    # update
                    sets = {
                        "`report_task_id` = '%s'" % valuesTuple[0],
                        "`task_id` = %s" % valuesTuple[1],
                        "`task_name` = '%s'" % valuesTuple[2],
                        "`app_name` = '%s'" % valuesTuple[3],
                        "`jsondata` = '%s'" % valuesTuple[4],
                        "`report_date` = '%s'" % valuesTuple[5],
                        "`account_id` = '%s'" % valuesTuple[6],
                        "`agency_id` = %s" % valuesTuple[7],
                        "`media_id` = %s" % valuesTuple[8],
                    }
                    sql = 'update %s set %s where `account_id` = "%s" and `agency_id` = %s  and `report_task_id` = "%s" and `ymd` = "%s"' % (
                        Config.TableMap.get('TASK_REPORT_TABLE'), ",".join(sets), accountId, self.agencyId,
                        report_task_id, startdate)
                    Utils.D("Update: %s" % sql)
                else:
                    # insert
                    values = "'%s', %s, '%s', '%s', '%s', '%s', '%s', %s, %s, '%s'" % valuesTuple
                    sql = "insert into %s (`report_task_id`, `task_id`, `task_name`, `app_name`, `jsondata`, `report_date`, `account_id`, `agency_id`, `media_id`, `ymd`) values (%s)" % (
                        Config.TableMap.get('TASK_REPORT_TABLE'), values)
                    Utils.D("Insert: %s" % sql)
                self.cursor.execute(sql)
            except:
                raise HuaweiException(Config.KD_ERROR, [
                    "sql: %s" % sql,
                    "value: %s" % json.dumps(valuesTuple)
                ])

        # 提交事物
        self.db.commit()

    # 导入推广关键词列表
    def importKeywordList(self, jsonresult, accountId, startdate):
        for i in jsonresult.get('taskPositiveSearchKeyInfo', []):
            status = Config.AUDIT_OK if i['searchKeyStatus'] == 'ON' else Config.AUDIT_FAIL
            jsondata = json.dumps({
                "downloadRate": i.get('downloadRate', ''),
                "fastSearchPrice": i.get('fastSearchPrice', ''),
                "searchListPrice": i.get('searchListPrice', ''),
                "todayConsume": i.get('todayConsume', ''),
                "totalConsumeSum": i.get('totalConsumeSum', ''),
                "totalDownloadAll": i.get('totalDownloadAll', ''),
                "totalImpressionAll": i.get('totalImpressionAll', ''),
                "searchKeyStatus": i.get('searchKeyStatus', '')
            }, encoding="utf-8")
            searchKey = i.get('searchKey', '')
            appName = i.get('appName', '')
            searchKeyStatus = i.get('searchKeyStatus', '')
            taskName = i.get('taskName', '')
            taskId = str(i.get('taskId', ''))
            keyword_str = searchKey + appName + searchKeyStatus + taskId + taskName + accountId
            keyword_id = Utils.md5(keyword_str.encode("utf-8"))
            valuesTuple = (
                status,
                int(i.get('taskId', 0)),
                i.get('taskName', ''),
                appName,
                searchKey,
                jsondata,
                accountId,
                self.agencyId,
                self.mediaId,
                keyword_id,
                startdate
            )

            sql = 'select * from %s where `account_id` = "%s" and `agency_id` = %d and `keyword_id` = "%s" and `ymd` = "%s"' % (
                Config.TableMap.get('KEYWORD_TABLE'), accountId, self.agencyId, keyword_id, startdate)
            Utils.D("Query: %s" % sql)
            res = self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0

            try:
                if (res):
                    # update
                    sets = {
                        "`status` = %s" % valuesTuple[0],
                        "`task_id` = %s" % valuesTuple[1],
                        "`task_name` = '%s'" % valuesTuple[2],
                        "`app_name` = '%s'" % valuesTuple[3],
                        "`keyword` = '%s'" % valuesTuple[4],
                        "`jsondata` = '%s'" % valuesTuple[5],
                        "`account_id` = '%s'" % valuesTuple[6],
                        "`agency_id` = %s" % valuesTuple[7],
                        "`media_id` = %s" % valuesTuple[8],
                        "`keyword_id` = '%s'" % valuesTuple[9],
                    }
                    sql = 'update %s set %s where `account_id` = "%s" and `agency_id` = %s  and `keyword_id` = "%s" and `ymd` = "%s"' % (
                        Config.TableMap.get('KEYWORD_TABLE'), ",".join(sets), accountId, self.agencyId, keyword_id,
                        startdate)
                    Utils.D("Update: %s" % sql)
                else:
                    # insert
                    values = "%s, %s, '%s', '%s', '%s', '%s', '%s', %s, %s, '%s', '%s'" % valuesTuple
                    sql = "insert into %s (`status`, `task_id`, `task_name`, `app_name`, `keyword`, `jsondata`, `account_id`, `agency_id`, `media_id`, `keyword_id`, `ymd`) values (%s)" % (
                        Config.TableMap.get('KEYWORD_TABLE'), values)
                    Utils.D("Insert: %s" % sql)
                self.cursor.execute(sql)
            except:
                raise HuaweiException(Config.KD_ERROR, [
                    "sql: %s" % sql,
                    "value: %s" % json.dumps(valuesTuple)
                ])

        # 提交事物
        self.db.commit()

    # 导入否定关键词列表
    def importDenyKeywordList(self, jsonresult, accountId):
        for i in jsonresult.get('taskNegativeSearchKeyInfo', []):
            searchKey = i.get('searchKey', '')
            appName = i.get('appName', '')
            taskName = i.get('taskName', '')
            taskId = str(i.get('taskId', ''))
            keyword_str = searchKey + appName + taskName + taskId
            deny_keyword_id = Utils.md5(keyword_str.encode("utf-8"))
            valuesTuple = (
                deny_keyword_id,
                int(i.get('taskId', 0)),
                i.get('taskName', ''),
                appName,
                searchKey,
                accountId,
                self.agencyId,
                self.mediaId,
            )

            sql = 'select * from %s where `account_id` = "%s" and `agency_id` = %d and `deny_keyword_id` = "%s"' % (
                Config.TableMap.get('KEYWORD_DENY_TABLE'), accountId, self.agencyId, deny_keyword_id)
            Utils.D("Query: %s" % sql)
            res = self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0

            try:
                if (res):
                    # update
                    sets = {
                        "`deny_keyword_id` = '%s'" % valuesTuple[0],
                        "`task_id` = %s" % valuesTuple[1],
                        "`task_name` = '%s'" % valuesTuple[2],
                        "`app_name` = '%s'" % valuesTuple[3],
                        "`keyword` = '%s'" % valuesTuple[4],
                        "`account_id` = '%s'" % valuesTuple[5],
                        "`agency_id` = %s" % valuesTuple[6],
                        "`media_id` = %s" % valuesTuple[7],
                    }
                    sql = 'update %s set %s where `account_id` = "%s" and `agency_id` = %s  and `deny_keyword_id` = "%s"' % (
                        Config.TableMap.get('KEYWORD_DENY_TABLE'), ",".join(sets), accountId, self.agencyId,
                        deny_keyword_id)
                    Utils.D("Update: %s" % sql)
                else:
                    # insert
                    values = "'%s', %s, '%s', '%s', '%s', '%s', %s, %s" % valuesTuple
                    sql = "insert into %s (`deny_keyword_id`, `task_id`, `task_name`, `app_name`, `keyword`, `account_id`, `agency_id`, `media_id`) values (%s)" % (
                        Config.TableMap.get('KEYWORD_DENY_TABLE'), values)
                    Utils.D("Insert: %s" % sql)
                self.cursor.execute(sql)
            except:
                raise HuaweiException(Config.KD_ERROR, [
                    "sql: %s" % sql,
                    "value: %s" % json.dumps(valuesTuple)
                ])

        # 提交事物
        self.db.commit()

    # 导入推广关键词报表
    def importKeywordReport(self, jsonresult, accountId, startdate):
        for i in jsonresult.get('taskSearchKeyReportList'):
            jsondata = json.dumps({
                "aveRanking": i.get('aveRanking', ''),
                "fastSearchAvePrice": i.get('fastSearchAvePrice', ''),
                "matchType": i.get('matchType', ''),
                "searchListAvePrice": i.get('searchListAvePrice', ''),
                "siteType": i.get('siteType', ''),
                "totalConsumeSum": i.get('totalConsumeSum', ''),
                "totalDownloadAll": i.get('totalDownloadAll', ''),
            }, encoding="utf-8")
            searchKey = i.get('searchKey', '')
            appName = i.get('appName', '')
            taskId = str(i.get('taskId', ''))
            taskName = i.get('taskName', '')
            keyword_str = searchKey + appName + taskId + taskName + accountId
            report_keyword_id = Utils.md5(keyword_str.encode("utf-8"))
            valuesTuple = (
                report_keyword_id,
                int(i.get('taskId', 0)),
                i.get('taskName', ''),
                appName,
                searchKey,
                jsondata,
                accountId,
                self.agencyId,
                self.mediaId,
                startdate
            )
            try:
                sql = 'select * from %s where `account_id` = "%s" and `agency_id` = %d and `report_keyword_id` = "%s" and `ymd` = "%s"' % (
                    Config.TableMap.get('KEYWORD_REPORT_TABLE'), accountId, self.agencyId, report_keyword_id, startdate)
                Utils.D("Query: %s" % sql)
                res = self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
                if (res):
                    # update
                    sets = {
                        "`report_keyword_id` = '%s'" % valuesTuple[0],
                        "`task_id` = %s" % valuesTuple[1],
                        "`task_name` = '%s'" % valuesTuple[2],
                        "`app_name` = '%s'" % valuesTuple[3],
                        "`keyword` = '%s'" % valuesTuple[4],
                        "`jsondata` = '%s'" % valuesTuple[5],
                        "`account_id` = '%s'" % valuesTuple[6],
                        "`agency_id` = %s" % valuesTuple[7],
                        "`media_id` = %s" % valuesTuple[8],
                    }
                    sql = "update %s set %s where `account_id` = '%s' and `agency_id` = %s  and `report_keyword_id` = '%s' and `ymd` = '%s'" % (
                        Config.TableMap.get('KEYWORD_REPORT_TABLE'), ",".join(sets), accountId, self.agencyId,
                        report_keyword_id, startdate)
                    Utils.D("Update: %s" % sql)
                else:
                    # insert
                    values = "'%s', %s, '%s', '%s', '%s', '%s', '%s', %s, %s, '%s'" % valuesTuple
                    sql = "insert into %s (`report_keyword_id`,`task_id`, `task_name`, `app_name`, `keyword`, `jsondata`, `account_id`, `agency_id`, `media_id`,`ymd`) values (%s)" % (
                        Config.TableMap.get('KEYWORD_REPORT_TABLE'), values)
                    Utils.D("Insert: %s" % sql)
                self.cursor.execute(sql)
            except:
                raise HuaweiException(Config.KD_ERROR, [
                    "sql: %s" % sql,
                    "value: %s" % json.dumps(valuesTuple)
                ])

        # 提交事物
        self.db.commit()

    # 批量导入二代
    def importHuaweiAgencys(self, jsonresult):
        totalCount = jsonresult.get("totalCount", 0)
        accounts = jsonresult.get("accounts", [])
        if 0 == totalCount or 0 == len(accounts):
            return
        # 入库account表
        for i in accounts:
            accountId = i.get('accountId', 0)
            sql = 'select * from %s where `account_id` = "%d"' % (
            Config.TableMap.get('HUAWEI_AGENCYS_TABLE'), accountId)
            Utils.D("Query: %s" % sql)
            res = self.cursor.execute(sql)  # 如果找到返回主键id，否则返回0
            status = Config.AUDIT_OK if i['status'] == 'AUDITED' else Config.AUDIT_FAIL
            jsondata = json.dumps({
                "createTime": i.get('createTime', ''),
                "lastDaySpent": i.get('lastDaySpent', ''),
                "todaySpent": i.get('todaySpent', ''),
                "status": i.get('status', '')
            })
            valuesTuple = (
                i.get('corpName', ''),
                status,
                i.get('balance', 0),
                accountId,
                jsondata,
            )
            xx = time.strftime("%Y%m%d", time.localtime())
            batch = self.api.getHbaseConn("account")
            rowkey = '{}|{}|{}|{}|{}'.format(str(accountId)[-1:], xx, self.mediaId, accountId, self.agencyId)
            data_list = json.dumps(jsondata)
            batch.put(row=rowkey, data={'info:data': str(data_list)})
            batch.send()
            try:
                if (res):
                    # update
                    sets = {
                        "`corp_name` = '%s'" % valuesTuple[0],
                        "`status` = %s" % valuesTuple[1],
                        "`balance` = %s" % valuesTuple[2],
                        "`account_id` = '%s'" % valuesTuple[3],
                        "`jsondata` = '%s'" % valuesTuple[4],
                    }
                    sql = "update %s set %s where `account_id` = '%s'" % (
                        Config.TableMap.get('HUAWEI_AGENCYS_TABLE'), ",".join(sets), accountId)
                    Utils.D("Update: %s" % sql)
                else:
                    # insert
                    values = "'%s',%s,%s,'%s','%s'" % valuesTuple
                    sql = "insert into %s (`corp_name`, `status`, `balance`, `account_id`, `jsondata`) values (%s)" % (
                        Config.TableMap.get('HUAWEI_AGENCYS_TABLE'), values)
                    Utils.D("Insert: %s" % sql)
                self.cursor.execute(sql)
            except:
                raise HuaweiException(Config.KD_ERROR, [
                    "sql: %s" % sql,
                    "value: %s" % json.dumps(valuesTuple)
                ])

        # 提交事物
        self.db.commit()
