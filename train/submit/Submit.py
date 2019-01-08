# -*- coding: utf-8 -*-

"""
下单
"""
import json
import re
import time
from datetime import datetime

from colorama import Fore

from Configure import CHOOSE_SEATS
from define.Const import TourFlag
from define.Const import Constant
from define.UrlsConf import submitUrls
from define.UserAgent import FIREFOX_USER_AGENT
from net import NetUtils
from net.NetUtils import EasyHttp
from train.submit.PassengerDetails import PassengerDetails
from utils import TrainUtils
from utils import Utils
from utils.Log import Log
import sms_send


class Submit(object):
    def __init__(self, ticketDetails):
        self.__sendSms = False
        self.__ticket = ticketDetails
        self._urlInfo = submitUrls['wc'] if self.__ticket.tourFlag == TourFlag.GO_BACK else \
            submitUrls['dc']

    # submit orher request,check if the orher is qualified
    def _submitOrderRequest(self, tourFlag='dc'):
        formData = {
            'secretStr': TrainUtils.undecodeSecretStr(self.__ticket.secretStr),
            # 'secretStr': self.__ticket.secretStr,
            # 'secretStr': urllib.parse.unquote(self.__ticket.secretStr),
            'train_date': Utils.formatDate(self.__ticket.startDate),  # 2018-01-04
            'back_train_date': time.strftime("%Y-%m-%d", time.localtime()),  # query date:2017-12-31
            'tour_flag': tourFlag,
            'purpose_codes': self.__ticket.passengerType,
            'query_from_station_name': self.__ticket.fromStation,
            'query_to_station_name': self.__ticket.toStation,
            'undefined': '',
        }
        jsonRet = EasyHttp.send(self._urlInfo['submitOrderRequest'], data=formData)
        print('submitOrderRequest %s' % jsonRet)
        return jsonRet['status'], jsonRet['messages']

    def _getExtraInfo(self):
        def getRepeatSubmitToken(html):
            repeatSubmitToken = re.findall(r"var globalRepeatSubmitToken = '(.*)'", html)[0]
            print('RepeatSubmitToken = %s' % repeatSubmitToken)
            return repeatSubmitToken

        html = EasyHttp.send(self._urlInfo['getExtraInfo'])
        if not Utils.check(html, 'getExtraInfoUrl: failed to visit %s' % self._urlInfo['getExtraInfo']['url']):
            return False
        self.__ticket.repeatSubmitToken = getRepeatSubmitToken(html)

        def decodeTicketInfoForPassengerForm(html):
            ticketInfoForPassengerForm = re.findall(r'var ticketInfoForPassengerForm=(.*);', html)[0]
            return json.loads(ticketInfoForPassengerForm.replace("'", "\""))

        self.__ticket.ticketInfoForPassengerForm = decodeTicketInfoForPassengerForm(html)
        return True

    def __getPassengerInfo(self, passengersList):
        passengersDetails = {}
        for passengerJson in passengersList:
            passenger = PassengerDetails()
            passenger.passengerName = passengerJson.get('passenger_name', '')
            passenger.code = passengerJson.get('code', '')
            passenger.sexCode = passengerJson.get('sex_code', '')
            passenger.sexName = passengerJson.get('sex_name', '')
            passenger.bornDate = passengerJson.get('born_date', '')
            passenger.countryCode = passengerJson.get('country_code', '')
            passenger.passengerIdTypeCode = passengerJson.get('passenger_id_type_code', '')
            passenger.passengerIdTypeName = passengerJson.get('passenger_id_type_name', '')
            passenger.passengerIdNo = passengerJson.get('passenger_id_no', '')
            passenger.passengerType = passengerJson.get('passenger_type', '')
            passenger.passengerFlag = passengerJson.get('passenger_flag', '')
            passenger.passengerTypeName = passengerJson.get('passenger_type_name', '')
            passenger.mobileNo = passengerJson.get('mobile_no', '')
            passenger.phoneNo = passengerJson.get('phone_no', '')
            passenger.email = passengerJson.get('email', '')
            passenger.address = passengerJson.get('address', '')
            passenger.postalcode = passengerJson.get('postalcode', '')
            passenger.firstLetter = passengerJson.get('first_letter', '')
            passenger.recordCount = passengerJson.get('recordCount', '')
            passenger.totalTimes = passengerJson.get('total_times', '')
            passenger.indexId = passengerJson.get('index_id', '')
            passengersDetails[passenger.passengerIdNo] = passenger
        return passengersDetails

    # get user's passengers info
    def _getPassengerDTOs(self):
        if not self._getExtraInfo():
            return False, '获取乘客信息失败', None
        formData = {
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.__ticket.repeatSubmitToken,
        }
        jsonRet = EasyHttp.send(self._urlInfo['getPassengerDTOs'], data=formData)
        passengersList = jsonRet['data']['normal_passengers']
        return jsonRet['status'] if 'status' in jsonRet else False, \
               jsonRet['messages'] if 'messages' in jsonRet else '无法获取乘客信息，请先进行添加!', \
               self.__getPassengerInfo(passengersList)

    # passengerName:乘客姓名
    # seatType:座位类别（一等座，二等座····）
    # ticketTypeCodes:车票类别代码
    def _checkOrderInfo(self, passengersDetails, seatType, ticketTypeCodes=1):
        formData = {
            'cancel_flag': self.__ticket.ticketInfoForPassengerForm['orderRequestDTO']['cancel_flag'] or '2',
            'bed_level_order_num': self.__ticket.ticketInfoForPassengerForm['orderRequestDTO'][
                                       'bed_level_order_num'] or '000000000000000000000000000000',
            'passengerTicketStr': TrainUtils.passengerTicketStrs(seatType, passengersDetails, ticketTypeCodes),
            'oldPassengerStr': TrainUtils.oldPassengerStrs(passengersDetails),
            'tour_flag': self.__ticket.ticketInfoForPassengerForm['tour_flag'] or 'dc',
            'randCode': '',
            'whatsSelect': '1',
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.__ticket.repeatSubmitToken,
        }
        jsonRet = EasyHttp.send(self._urlInfo['checkOrderInfo'], data=formData)
        return jsonRet['status'], jsonRet['messages'], jsonRet['data']['submitStatus'], \
               jsonRet['data']['errMsg'] if 'errMsg' in jsonRet['data'] else 'submit falied'

    def _getQueueCount(self):
        formData = {
            # Thu+Jan+04+2018+00:00:00+GMT+0800
            # 'train_date': datetime.strptime(
            #     self.__ticket.ticketInfoForPassengerForm['queryLeftTicketRequestDTO']['train_date'], '%Y%m%d').strftime(
            #     '%b+%a+%d+%Y+00:00:00+GMT+0800'),
            # Mon Jan 08 2018 00:00:00 GMT+0800 (中国标准时间)
            'train_date': datetime.strptime(
                self.__ticket.ticketInfoForPassengerForm['queryLeftTicketRequestDTO']['train_date'], '%Y%m%d').strftime(
                '%b %a %d %Y 00:00:00 GMT+0800') + ' (中国标准时间)',
            'train_no': self.__ticket.ticketInfoForPassengerForm['queryLeftTicketRequestDTO']['train_no'],
            'stationTrainCode': self.__ticket.trainNo,
            'seatType': self.__ticket.seatType,
            'fromStationTelecode': self.__ticket.fromStationCode,
            'toStationTelecode': self.__ticket.toStationCode,
            'leftTicket': self.__ticket.ticketInfoForPassengerForm['leftTicketStr'],
            'purpose_codes': self.__ticket.ticketInfoForPassengerForm['purpose_codes'],
            'train_location': self.__ticket.ticketInfoForPassengerForm['train_location'],
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.__ticket.repeatSubmitToken,
        }
        jsonRet = EasyHttp.send(self._urlInfo['getQueueCount'], data=formData)
        return jsonRet['status'], jsonRet['messages'], \
               jsonRet['data']['ticket'] if 'data' in jsonRet and 'ticket' in jsonRet['data'] else -1, \
               jsonRet['data']['count'] if 'data' in jsonRet and 'count' in jsonRet['data'] else -1

    # network busy usually occured
    def _confirmSingleOrGoForQueue(self, passengersDetails):
        formData = {
            'passengerTicketStr': TrainUtils.passengerTicketStrs(self.__ticket.seatType, passengersDetails,
                                                                 self.__ticket.ticketTypeCodes),
            'oldPassengerStr': TrainUtils.oldPassengerStrs(passengersDetails),
            'randCode': '',
            'purpose_codes': self.__ticket.ticketInfoForPassengerForm['purpose_codes'],
            'key_check_isChange': self.__ticket.ticketInfoForPassengerForm['key_check_isChange'],
            'leftTicketStr': self.__ticket.ticketInfoForPassengerForm['leftTicketStr'],
            'train_location': self.__ticket.ticketInfoForPassengerForm['train_location'],
            'choose_seats': ''.join(CHOOSE_SEATS) or '',
            'seatDetailType': '000',  # todo::make clear 000 comes from
            'whatsSelect': '1',
            'roomType': '00',  # todo::make clear this value comes from
            'dwAll': 'N',
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.__ticket.repeatSubmitToken,
        }
        jsonRet = EasyHttp.send(self._urlInfo['confirmForQueue'], data=formData)
        return jsonRet['status'], jsonRet['messages'], jsonRet['data']['submitStatus'], jsonRet['data'][
            'errMsg'] if 'errMsg' in jsonRet['data'] else None

    def _queryOrderWaitTime(self):
        params = {
            'random': '%10d' % (time.time() * 1000),
            'tourFlag': self.__ticket.ticketInfoForPassengerForm['tour_flag'] or 'dc',
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.__ticket.repeatSubmitToken,
        }
        jsonRet = EasyHttp.send(self._urlInfo['queryOrderWaitTime'], params=params)
        print('queryOrderWaitTime: %s' % jsonRet)
        return jsonRet['status'], jsonRet['messages'], jsonRet['data']['waitTime'], jsonRet['data']['orderId'], \
               jsonRet['data']['msg'] if 'msg' in jsonRet['data'] else None

    def _resultOrderForDcOrWcQueue(self, orderSequenceNo):
        formData = {
            'orderSequence_no': orderSequenceNo,
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.__ticket.repeatSubmitToken,
        }
        jsonRet = EasyHttp.send(self._urlInfo['resultOrderForQueue'], data=formData)
        print('resultOrderForDcOrWcQueue', jsonRet)
        return jsonRet['status'], jsonRet['messages'], jsonRet['data']['submitStatus']

    # TODO::finish it
    def _payOrderInfo(self):
        url = r'https://kyfw.12306.cn/otn//payOrder/init?random=%10d' % (time.time() * 1000)
        headers = {
            'User-Agent': FIREFOX_USER_AGENT,
            'Connection': 'keep-alive',
        }
        response = NetUtils.get(self.__session, url, headers=headers).text

    # seatType:商务座(9),特等座(P),一等座(M),二等座(O),高级软卧(6),软卧(4),硬卧(3),软座(2),硬座(1),无座(1)
    # ticket_type_codes:ticketInfoForPassengerForm['limitBuySeatTicketDTO']['ticket_type_codes']:(成人票:1,儿童票:2,学生票:3,残军票:4)
    def submit(self):
        status, msg = self._submitOrderRequest(self.__ticket.tourFlag)
        if not Utils.check(status, 'submitOrderRequesst: %s' % msg):
            return False
        Log.info('提交订单请求成功!')

        status, msg, passengersDetailsList = self._getPassengerDTOs()
        if not Utils.check(status, 'getPassengerDTOs: %s' % msg):
            return False
        Log.info('获取乘客信息成功!')

        passengersDetails = []
        for id in self.__ticket.passengersId:
            passengersDetails.append(passengersDetailsList.get(id))

        time.sleep(1)
        status, msg, submitStatus, errMsg = self._checkOrderInfo(passengersDetails, self.__ticket.seatType,
                                                                 self.__ticket.ticketTypeCodes)
        if not Utils.check(status, 'checkOrderInfo: %s' % msg) or not Utils.check(submitStatus,
                                                                                  'checkOrderInfo: %s' % errMsg):
            return False
        Log.info('校验订单信息成功!')

        status, msg, leftTickets, personsCount = self._getQueueCount()
        if not Utils.check(status, 'getQueueCount: %s' % msg):
            return False
        Log.info('%s 剩余车票:%s ,目前排队人数: %s' % (self.__ticket.trainNo, leftTickets, personsCount))
        status, msg, submitStatus, errMsg = self._confirmSingleOrGoForQueue(passengersDetails)

        if not Utils.check(status, 'confirmSingleOrGoForQueue: %s' % msg) \
                or not Utils.check(submitStatus, 'confirmSingleOrGoForQueue: %s' % errMsg or '订单信息提交失败！'):
            return False

        orderId = self.__waitForOrderId()
        if not Utils.check(orderId, '订单获取失败！'):
            return False

        status, msg, submitStatus = self._resultOrderForDcOrWcQueue(orderId)
        if not Utils.check(status, 'resultOrderForDcOrWcQueue: %s' % msg):
            return False
        if not submitStatus:
            Log.error('订单提交失败！')
            return False
        if not Constant.send_sms:
            sms_send.send()
            Constant.send_sms = True
        Log.info('您已成功订购火车票！请在30分钟内前往12306官方网站进行支付！')
        return True

    def _queryMyOrderNoComplete(self):
        formData = {
            '_json_att': '',
        }
        jsonRet = EasyHttp.send(self._urlInfo['queryMyOrderNoComplete'], data=formData)
        return jsonRet['status'], jsonRet['messages'], jsonRet['data']

    def showSubmitInfoPretty(self):
        status, msg, jsonTicketInfo = self._queryMyOrderNoComplete()
        if not Utils.check(status, msg):
            return False
        from prettytable import PrettyTable
        table = PrettyTable()
        table.field_names = '序号 车次信息 席位信息 旅客信息 票款金额 车票状态'.split(sep=' ')
        totalTicketNum = TrainUtils.submitTicketTotalNum(jsonTicketInfo)
        for i in range(totalTicketNum):
            table.add_row([i + 1,
                           TrainUtils.submitTrainInfo(i, jsonTicketInfo),
                           TrainUtils.submitCoachInfo(i, jsonTicketInfo),
                           TrainUtils.submitPassengerInfo(i, jsonTicketInfo),
                           TrainUtils.submitTicketCostInfo(i, jsonTicketInfo),
                           TrainUtils.submitTicketPayInfo(i, jsonTicketInfo),
                           ])
            if not i == totalTicketNum - 1:
                table.add_row([2 * '-', 2 * '-', 2 * '-', 2 * '-', 2 * '-', 2 * '-'])

        print(table)
        Log.info('总张数:%d\t待支付金额:%s' % (
            totalTicketNum, Fore.YELLOW + '{}元'.format(TrainUtils.submitTicketTotalCost(jsonTicketInfo)) + Fore.RESET))
        return True

    def showSubmitInfo(self):
        return self._queryMyOrderNoComplete()

    def __waitForOrderId(self):
        Log.info('正在排队获取订单!')
        count = 0
        while True:
            count += 1
            status, msg, waitTime, orderId, errorMsg = self._queryOrderWaitTime()
            if not Utils.check(status, 'queryOrderWaitTime: %s' % msg):
                return None
            Log.info('[%d]正在等待订单提交结果...' % count)
            if waitTime < 0:
                if orderId:
                    Log.info('订单提交成功，订单号: %s' % orderId)
                    return orderId
                elif errorMsg:
                    Log.error(errorMsg)
                    return None
            interval = waitTime // 60
            Log.warning('未出票，订单排队中...预估等待时间: %s 分钟' % (interval if interval <= 30 else '超过30'))
            if interval > 30:
                time.sleep(60)
            elif interval > 20:
                time.sleep(30)
            elif interval > 10:
                time.sleep(10)
            else:
                time.sleep(3)

        return None
