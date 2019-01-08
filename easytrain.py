#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import time

from Configure import *
from define.Const import SEAT_TYPE
from train.login.Login import Login
from train.query.Query import Query
from train.submit.Submit import Submit
from utils import TrainUtils
from utils import Utils
from utils.Log import Log
from utils import daemo


def main():
    PIDFILE = '/tmp/easy_train.pid'

    login = Login()
    Log.info('正在登录...')
    result, msg = login.login(USER_NAME, USER_PWD)
    if not Utils.check(result, msg):
        Log.error(msg)
        return
    Log.info('%s,登录成功' % msg)
    daemo.daemonize(PIDFILE)

    seatTypesCode = SEAT_TYPE_CODE if SEAT_TYPE_CODE else [SEAT_TYPE[key] for key in SEAT_TYPE.keys()]
    passengerTypeCode = PASSENGER_TYPE_CODE if PASSENGER_TYPE_CODE else '1'
    while True:
        # 死循环一直查票，直到下单成功
        try:
            print('-' * 40)
            count = 0
            for date in TRAIN_DATE:
                tarin(date, passengerTypeCode, seatTypesCode, count)
        except Exception as e:
            Log.warning(e)


def tarin(date, passengerTypeCode, seatTypesCode, count=0):
    ticketDetails = Query.loopQuery(date, FROM_STATION, TO_STATION,
                                    TrainUtils.passengerType2Desc(passengerTypeCode),
                                    TRAINS_NO,
                                    seatTypesCode, count=count)
    for ticketDetail in ticketDetails:
        Log.info('已为您查询到可用余票:%s' % ticketDetail)

        ticketDetail.passengersId = PASSENGERS_ID
        ticketDetail.ticketTypeCodes = passengerTypeCode
        ticketDetail.tourFlag = TOUR_FLAG if TOUR_FLAG else 'dc'
        submit = Submit(ticketDetail)
        if submit.submit():
            submit.showSubmitInfoPretty()
            break
        time.sleep(1)


if __name__ == '__main__':
    main()
