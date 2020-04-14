#! /usr/bin env python
# coding:utf-8
import json
import sys, getopt
import threading
import requests
import espider.Config as Config
import time
import espider.Utils as Utils
from espider.app.huawei.HuaweiException import HuaweiException
from espider.app.huawei.HuaweiLogic import HuaweiLogic
from espider.Spider import Spider


class HuaweiSpider(threading.Thread, Spider):
    def __init__(self, mediaId, agencyId, kwargs):
        threading.Thread.__init__(self, target=self.work, kwargs=kwargs)
        self.logic = HuaweiLogic(agencyId, mediaId)
        self.accessToken = self.getAccessToken(mediaId, agencyId)
        self.maxReqCount = 99999  # 每页最大记录条数
        self.maxPageCount = 9999  # 最大页数
        self.agencyId = agencyId
        self.mediaId = mediaId
        self.s = requests.session()
        self.restUrl = "https://e.appstore.huawei.com/rest.php"
        self.headers = {
            'Accept-Language': 'zh-CN, zh;q = 0.9',
            'Content-type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.119 Chrome/64.0.3282.119 Safari/537.36'
        }

    def getAccessToken(self, mediaId, agencyId):
        try:
            accessToken = self.logic.getTokens(agencyId)
            if "" == accessToken:
                raise HuaweiException(Config.KD_ERROR, [
                    "please config access token",
                    "agencyId: %s" % agencyId
                ])
            return accessToken
        except HuaweiException as e:
            self.log(e.code, e.msg, log_prefix="huawei")

    def work(self, *args, **kwargs):
        # print args
        Utils.D(kwargs)
        agencytype = kwargs['agencytype']  # 代理类型：agencyuser直客，agencys二代维护
        operation = kwargs['operation']
        startdate = kwargs['startdate']
        enddate = kwargs['enddate']
        agency_ext = kwargs.get("agency_ext", {})
        agency_user_id = agency_ext.get('agency_user_id', '')  # 二代用户id

        # 直客
        if 'agencyuser' == agencytype and '' != agency_user_id:
            if 'getaccounts' == operation:
                self.accountManager()
            elif 'datamanager' == operation:
                self.dataManager(startdate, enddate)
            elif 'keywordreport' == operation:
                self.keywordReport(startdate, enddate)
            elif 'keywordlist' == operation:
                self.keywordList(startdate, enddate)
            elif 'keyworddenylist' == operation:
                self.keywordDenyList()
            elif 'taskreport' == operation:
                self.taskReport(startdate, enddate)
            elif 'tasklist' == operation:
                self.taskList(agency_user_id)
            else:
                self.accountManager()
                self.dataManager(startdate, enddate)
                self.taskList(agency_user_id)
                self.taskReport(startdate, enddate)
                self.keywordList(startdate, enddate)
                self.keywordDenyList()
                self.keywordReport(startdate, enddate)

        # 二代维护
        if 'agencys' == agencytype:
            if 'agencyslist' == operation:
                self.huaweiAgencys()

    # 客户管理
    def accountManager(self):
        try:
            formdata = {
                "agentAccountId": 0,
                "corpName": "",
                "status": "ALL",
                "fromRecCount": 0,
                "maxReqCount": self.maxReqCount,
                "nsp_svc": "AppPromote.Agent.queryCustomerList",
                "access_token": self.accessToken,
                "nsp_fmt": "JSON",
                "nsp_ts": Utils.getMicSecond()
            }
            result = self.s.post(self.restUrl, data=formdata, headers=self.headers).text
            try:
                jsonresult = json.loads(result, encoding="utf-8")
            except:
                return
            if 'error' in jsonresult:
                raise HuaweiException(Config.KD_ERROR, [
                    jsonresult.get('error'),
                    'methodName: %s' % sys._getframe().f_code.co_name,
                    "resultText: %s" % result,
                    "agencyId: %s" % self.agencyId,
                    "mediaId: %s" % self.mediaId,
                ])
            # 导入account表
            self.logic.importAccount(jsonresult)
        except HuaweiException as e:
            self.log(e.code, e.msg, log_prefix="huawei")

    # 数据管理
    def dataManager(self, startdate, enddate):
        try:
            dates = Utils.getDayDeltas(startdate, enddate)
            for dateval in dates:
                startdate = enddate = dateval
                formdata = {
                    "beginTime": startdate,
                    "endTime": enddate,
                    "fromRecCount": 0,
                    "maxReqCount": self.maxReqCount,
                    "nsp_svc": "AppPromote.Agent.queryReport",
                    "access_token": self.accessToken,
                    "nsp_fmt": "JSON",
                    "nsp_ts": Utils.getMicSecond()
                }
                Utils.D(formdata)
                result = self.s.post(self.restUrl, data=formdata, headers=self.headers).text
                try:
                    jsonresult = json.loads(result, encoding="utf-8")
                except:
                    continue
                if 'error' in jsonresult:
                    raise HuaweiException(Config.KD_ERROR, [
                        jsonresult.get('error'),
                        'methodName: %s' % sys._getframe().f_code.co_name,
                        "resultText: %s" % result,
                        "agencyId: %s" % self.agencyId,
                        "mediaId: %s" % self.mediaId,
                        "startdate: %s" % startdate,
                        "enddate: %s" % enddate,
                    ])
                # print jsonresult
                # exit()
                # 入库huawei_daily_report_account表
                self.logic.importDataManager(jsonresult, startdate)

                time.sleep(Config.HUAWEI_REQUEST_TIME)
        except HuaweiException as e:
            self.log(e.code, e.msg, log_prefix="huawei")

    # 推广任务列表
    def taskList(self, agencyUserId):
        try:
            # 获取客户列表
            accounts = self.logic.getAccounts()
            for i in accounts:
                formdata = {
                    "userID": agencyUserId,
                    "fromRecCount": 0,
                    "maxReqCount": self.maxReqCount,
                    "sortType": 1,
                    "sortField": "modify_time",
                    "customerAccountId": i['account_id_from_media'],
                    "nsp_svc": "Inapp.Developer.queryTaskList",
                    "access_token": self.accessToken,
                    "nsp_fmt": "JSON",
                    "nsp_ts": Utils.getMicSecond()
                }
                result = self.s.post(self.restUrl, data=formdata, headers=self.headers).text
                try:
                    jsonresult = json.loads(result, encoding="utf-8")
                except:
                    continue
                if 'error' in jsonresult:
                    raise HuaweiException(Config.KD_ERROR, [
                        jsonresult.get('error'),
                        'methodName: %s' % sys._getframe().f_code.co_name,
                        "resultText: %s" % result,
                        "agencyId: %s" % self.agencyId,
                        "mediaId: %s" % self.mediaId,
                        "accountId: %s" % i['account_id_from_media'],
                        "agencyUserId: %s" % agencyUserId,
                    ])
                # print jsonresult
                self.logic.importTaskList(jsonresult, i['account_id_from_media'])
        except HuaweiException as e:
            self.log(e.code, e.msg, log_prefix="huawei")

    # 推广任务报表
    def taskReport(self, startdate, enddate):
        try:
            # 获取推广任务列表
            tasks = self.logic.getTaskIdList()
            dates = Utils.getDayDeltas(startdate, enddate)
            for accountId, taskIdList in tasks.items():
                for dateval in dates:
                    startdate = enddate = dateval
                    startdateval = startdate.replace("-", "")
                    enddateval = enddate.replace("-", "")
                    formdata = {
                        "taskIDList": json.dumps(taskIdList),
                        "beginDate": startdateval,
                        "endDate": enddateval,
                        "sortField": "task,time",
                        "sortType": 0,
                        "fromRecCount": 0,
                        "maxReqCount": self.maxReqCount,
                        "customerAccountId": accountId,
                        "nsp_svc": "Inapp.Developer.reportPromoApp",
                        "access_token": self.accessToken,
                        "nsp_fmt": "JSON",
                        "nsp_ts": Utils.getMicSecond()
                    }
                    result = self.s.post(self.restUrl, data=formdata, headers=self.headers).text
                    try:
                        jsonresult = json.loads(result, encoding="utf-8")
                    except:
                        continue
                    if 'error' in jsonresult:
                        raise HuaweiException(Config.KD_ERROR, [
                            jsonresult.get('error'),
                            'methodName: %s' % sys._getframe().f_code.co_name,
                            "resultText: %s" % result,
                            "agencyId: %s" % self.agencyId,
                            "mediaId: %s" % self.mediaId,
                            "accountId: %s" % accountId,
                            "taskIDList: %s" % json.dumps(taskIdList),
                            "startdate: %s" % startdate,
                            "enddate: %s" % enddate,
                        ])
                    # 入库huawei_task表
                    self.logic.importTaskReport(jsonresult, accountId, startdate)
        except HuaweiException as e:
            self.log(e.code, e.msg, log_prefix="huawei")

    # 关键词列表
    def keywordList(self, startdate, enddate):
        try:
            # 获取客户列表
            accounts = self.logic.getAccounts()
            dates = Utils.getDayDeltas(startdate, enddate)
            for i in accounts:
                for dateval in dates:
                    startdate = enddate = dateval
                    fromRecCount = 0  # 初始页码0
                    for c in range(self.maxPageCount):
                        formdata = {
                            "fromRecCount": fromRecCount,
                            "maxReqCount": 100,
                            "dateFilterStart": startdate,
                            "dateFilterEnd": enddate,
                            "sortType": "DESC",
                            "customerAccountId": i['account_id_from_media'],
                            "nsp_svc": "Inapp.Developer.queryTaskListByPositiveKeys",
                            "access_token": self.accessToken,
                            "nsp_fmt": "JSON",
                            "nsp_ts": Utils.getMicSecond()
                        }
                        result = self.s.post(self.restUrl, data=formdata, headers=self.headers).text
                        try:
                            jsonresult = json.loads(result, encoding="utf-8")
                        except:
                            continue
                        if 'error' in jsonresult:
                            raise HuaweiException(Config.KD_ERROR, [
                                jsonresult.get('error'),
                                'methodName: %s' % sys._getframe().f_code.co_name,
                                "resultText: %s" % result,
                                "agencyId: %s" % self.agencyId,
                                "mediaId: %s" % self.mediaId,
                                "accountId: %s" % i['account_id_from_media'],
                                "fromRecCount: %s" % fromRecCount,
                                "startdate: %s" % startdate,
                                "enddate: %s" % enddate,
                            ])
                        totalCount = jsonresult.get('totalCount', 0)
                        taskPositiveSearchKeyInfo = jsonresult.get("taskPositiveSearchKeyInfo", [])
                        if 0 == totalCount:
                            break
                        if 0 == len(taskPositiveSearchKeyInfo):
                            break
                        self.logic.importKeywordList(jsonresult, i['account_id_from_media'], startdate)
                        # print jsonresult
                        # print fromRecCount
                        fromRecCount = fromRecCount + 100
        except HuaweiException as e:
            self.log(e.code, e.msg, log_prefix="huawei")

    # 关键词报表
    def keywordReport(self, startdate, enddate):
        try:
            # 获取客户列表
            accounts = self.logic.getAccounts()
            dates = Utils.getDayDeltas(startdate, enddate)
            for i in accounts:
                for dateval in dates:
                    startdate = enddate = dateval
                    fromRecCount = 1  # 初始页码1
                    for c in range(self.maxPageCount):
                        formdata = {
                            "dateFilterStart": startdate,
                            "dateFilterEnd": enddate,
                            "sortField": "totalConsumeSum",
                            "sortType": "DESC",
                            "fromRecCount": fromRecCount,
                            "maxReqCount": 100,
                            "customerAccountId": i['account_id_from_media'],
                            "nsp_svc": "Inapp.Developer.reportPromoAppBySearchKeys",
                            "access_token": self.accessToken,
                            "nsp_fmt": "JSON",
                            "nsp_ts": Utils.getMicSecond()
                        }
                        result = self.s.post(self.restUrl, data=formdata, headers=self.headers).text
                        try:
                            jsonresult = json.loads(result, encoding="utf-8")
                        except:
                            continue
                        if 'error' in jsonresult:
                            raise HuaweiException(Config.KD_ERROR, [
                                jsonresult.get('error'),
                                'methodName: %s' % sys._getframe().f_code.co_name,
                                "resultText: %s" % result,
                                "agencyId: %s" % self.agencyId,
                                "mediaId: %s" % self.mediaId,
                                "accountId: %s" % i['account_id_from_media'],
                                "fromRecCount: %s" % fromRecCount,
                                "startdate: %s" % startdate,
                                "enddate: %s" % enddate,
                            ])
                        totalCount = jsonresult.get('totalCount', 0)
                        taskSearchKeyReportList = jsonresult.get('taskSearchKeyReportList', [])
                        if 0 == totalCount:
                            break
                        if 0 == len(taskSearchKeyReportList):
                            break
                        self.logic.importKeywordReport(jsonresult, i['account_id_from_media'], startdate)
                        # print jsonresult
                        # print fromRecCount
                        fromRecCount = fromRecCount + 100
        except HuaweiException as e:
            self.log(e.code, e.msg, log_prefix="huawei")

    # 否定关键词列表
    def keywordDenyList(self):
        try:
            # 获取客户列表
            accounts = self.logic.getAccounts()
            for i in accounts:
                fromRecCount = 0  # 初始页码0
                for c in range(self.maxPageCount):
                    formdata = {
                        "fromRecCount": fromRecCount,
                        "maxReqCount": 100,
                        "customerAccountId": i['account_id_from_media'],
                        "nsp_svc": "Inapp.Developer.queryTaskListByNegativeKeys",
                        "access_token": self.accessToken,
                        "nsp_fmt": "JSON",
                        "nsp_ts": Utils.getMicSecond()
                    }
                    result = self.s.post(self.restUrl, data=formdata, headers=self.headers).text
                    try:
                        jsonresult = json.loads(result, encoding="utf-8")
                    except:
                        continue
                    if 'error' in jsonresult:
                        raise HuaweiException(Config.KD_ERROR, [
                            jsonresult.get('error'),
                            'methodName: %s' % sys._getframe().f_code.co_name,
                            "resultText: %s" % result,
                            "agencyId: %s" % self.agencyId,
                            "mediaId: %s" % self.mediaId,
                            "accountId: %s" % i['account_id_from_media'],
                            "fromRecCount: %s" % fromRecCount,
                        ])
                    totalCount = jsonresult.get('totalCount', 0)
                    taskNegativeSearchKeyInfo = jsonresult.get("taskNegativeSearchKeyInfo", [])
                    if 0 == totalCount:
                        break
                    if 0 == len(taskNegativeSearchKeyInfo):
                        break
                    self.logic.importDenyKeywordList(jsonresult, i['account_id_from_media'])
                    # print jsonresult
                    # print fromRecCount
                    fromRecCount = fromRecCount + 100
        except HuaweiException as e:
            self.log(e.code, e.msg, log_prefix="huawei")

    # 二代维护
    def huaweiAgencys(self):
        try:
            formdata = {
                "status": "ALL",
                "fromRecCount": 0,
                "maxReqCount": self.maxReqCount,
                "nsp_svc": "AppPromote.CoreAgent.queryAgentList",
                "access_token": self.accessToken,
                "nsp_fmt": "JSON",
                "nsp_ts": Utils.getMicSecond()
            }
            result = self.s.post(self.restUrl, data=formdata, headers=self.headers).text
            try:
                jsonresult = json.loads(result, encoding="utf-8")
            except:
                return
            if 'error' in jsonresult:
                raise HuaweiException(Config.KD_ERROR, [
                    jsonresult.get('error'),
                    'methodName: %s' % sys._getframe().f_code.co_name,
                    "resultText: %s" % result,
                    "agencyId: %s" % self.agencyId,
                    "mediaId: %s" % self.mediaId,
                ])
            totalCount = jsonresult.get('totalCount', 0)
            accounts = jsonresult.get("accounts", [])
            if 0 == totalCount or 0 == len(accounts):
                return
            self.logic.importHuaweiAgencys(jsonresult)
        except HuaweiException as e:
            self.log(e.code, e.msg, log_prefix="huawei")


if __name__ == "__main__":
    agencytype = operation = ''
    startdate = enddate = Utils.getYesterday()  # 默认昨天的日期
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "ht:o:s:e:", ["agencytype=", "operation=", "startdate=", "enddate="])
    except getopt.GetoptError:
        print
        'python Ppb.py -t <agencytype> -o <operation> -s <startdate> -e <enddate>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print
            'python Ppb.py -t <agencytype> -o <operation> -s <startdate> -e <enddate>'
            sys.exit()
        elif opt in ("-t", "--agencytype"):
            agencytype = arg
        elif opt in ("-o", "--operation"):
            operation = arg
        elif opt in ("-s", "--startdate"):
            startdate = arg
        elif opt in ("-e", "--enddate"):
            enddate = arg
    Utils.D('代理类型：%s' % agencytype)
    Utils.D('执行的操作：%s' % operation)
    Utils.D('开始时间：%s' % startdate)
    Utils.D('结束时间：%s' % enddate)
    hl = HuaweiLogic()
    agencys = hl.getAgencys(agencytype)
    for i in agencys:
        agency_ext = json.loads(i.get('agency_ext', '{}'))
        kwargs = {"agencytype": agencytype, "operation": operation, "startdate": startdate, "enddate": enddate,
                  "agency_ext": agency_ext}
        hw = HuaweiSpider(i['media_id'], i['id'], kwargs)
        hw.start()
        hw.join()
