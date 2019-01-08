import time

from colorama import Fore
from prettytable import PrettyTable

from Configure import QUERY_TICKET_REFERSH_INTERVAL
from define.CityCode import city2code, code2city
from define.Const import PASSENGER_TYPE_ADULT, SEAT_TYPE
from define.UrlsConf import queryUrls
from define.UrlsConf import loginUrls
from net.NetUtils import EasyHttp
from train.TicketDetails import TicketDetails
from utils import TrainUtils
from utils.Log import Log
import train.login.Login

#  车次：3
INDEX_TRAIN_NO = 3
#  start_station_code:起始站：4
INDEX_TRAIN_START_STATION_CODE = 4
#  end_station_code终点站：5
INDEX_TRAIN_END_STATION_CODE = 5
#  from_station_code:出发站：6
INDEX_TRAIN_FROM_STATION_CODE = 6
#  to_station_code:到达站：7
INDEX_TRAIN_TO_STATION_CODE = 7
#  start_time:出发时间：8
INDEX_TRAIN_LEAVE_TIME = 8
#  arrive_time:达到时间：9
INDEX_TRAIN_ARRIVE_TIME = 9
#  历时：10
INDEX_TRAIN_TOTAL_CONSUME = 10
#  商务特等座：32
INDEX_TRAIN_BUSINESS_SEAT = 32
#  一等座：31
INDEX_TRAIN_FIRST_CLASS_SEAT = 31
#  二等座：30
INDEX_TRAIN_SECOND_CLASS_SEAT = 30
#  高级软卧：21
INDEX_TRAIN_ADVANCED_SOFT_SLEEP = 21
#  软卧：23
INDEX_TRAIN_SOFT_SLEEP = 23
#  动卧：33
INDEX_TRAIN_MOVE_SLEEP = 33
#  硬卧：28
INDEX_TRAIN_HARD_SLEEP = 28
#  软座：24
INDEX_TRAIN_SOFT_SEAT = 24
#  硬座：29
INDEX_TRAIN_HARD_SEAT = 29
#  无座：26
INDEX_TRAIN_NO_SEAT = 28
#  其他：22
INDEX_TRAIN_OTHER = 22
#  备注：1
INDEX_TRAIN_MARK = 1

INDEX_SECRET_STR = 0

INDEX_START_DATE = 13  # 车票出发日期


#
#  start_train_date:车票出发日期：13


class Query(object):
    @staticmethod
    def query(trainDate, fromStation, toStation, passengerType=PASSENGER_TYPE_ADULT):
        params = {
            r'leftTicketDTO.train_date': trainDate,
            r'leftTicketDTO.from_station': city2code(fromStation),
            r'leftTicketDTO.to_station': city2code(toStation),
            r'purpose_codes': passengerType
        }
        jsonRet = EasyHttp.send(queryUrls['query'], params=params)
        try:
            if jsonRet:
                return Query.__decode(jsonRet, passengerType)
        except Exception as e:
            Log.error(e)
        Log.error(queryUrls['query'])
        Log.error(jsonRet)
        Log.error('列表为空！确认url！')
        return []

    @staticmethod
    def __decode(jsonRet, passengerType):
        queryResults = jsonRet['data']['result']
        cityMap = jsonRet['data']['map']
        for queryResult in queryResults:
            info = queryResult.split('|')
            ticket = TicketDetails()
            ticket.passengerType = passengerType
            ticket.trainNo = info[INDEX_TRAIN_NO]
            ticket.startStationCode = info[INDEX_TRAIN_START_STATION_CODE]
            ticket.endStationCode = info[INDEX_TRAIN_END_STATION_CODE]
            ticket.fromStationCode = info[INDEX_TRAIN_FROM_STATION_CODE]
            ticket.toStationCode = info[INDEX_TRAIN_TO_STATION_CODE]
            ticket.leaveTime = info[INDEX_TRAIN_LEAVE_TIME]
            ticket.arriveTime = info[INDEX_TRAIN_ARRIVE_TIME]
            ticket.totalConsume = info[INDEX_TRAIN_TOTAL_CONSUME]
            ticket.businessSeat = info[INDEX_TRAIN_BUSINESS_SEAT]
            ticket.firstClassSeat = info[INDEX_TRAIN_FIRST_CLASS_SEAT]
            ticket.secondClassSeat = info[INDEX_TRAIN_SECOND_CLASS_SEAT]
            ticket.advancedSoftSleep = info[INDEX_TRAIN_ADVANCED_SOFT_SLEEP]
            ticket.softSleep = info[INDEX_TRAIN_SOFT_SLEEP]
            ticket.moveSleep = info[INDEX_TRAIN_MOVE_SLEEP]
            ticket.hardSleep = info[INDEX_TRAIN_HARD_SLEEP]
            ticket.softSeat = info[INDEX_TRAIN_SOFT_SEAT]
            ticket.hardSeat = info[INDEX_TRAIN_HARD_SEAT]
            ticket.noSeat = info[INDEX_TRAIN_NO_SEAT]
            ticket.other = info[INDEX_TRAIN_OTHER]
            ticket.mark = info[INDEX_TRAIN_MARK]
            # ticket.startStation = code2city(ticket.startStationCode)
            # ticket.endStation = code2city(ticket.endStationCode)
            ticket.fromStation = cityMap[ticket.fromStationCode]
            ticket.toStation = cityMap[ticket.toStationCode]
            ticket.secretStr = info[INDEX_SECRET_STR]
            ticket.startDate = info[INDEX_START_DATE]
            yield ticket

    @staticmethod
    def outputPretty(trainDate, fromStation, toStation, passengerType=PASSENGER_TYPE_ADULT):
        table = PrettyTable()
        table.field_names = '车次 车站 时间 历时 商务特等座 一等座 二等座 高级软卧 软卧 动卧 硬卧 软座 硬座 无座 其他 备注'.split(sep=' ')
        for ticket in Query.query(trainDate, fromStation, toStation, passengerType):
            Query.ticketPretty(table, ticket)
        Log.info(table)

    @staticmethod
    def ticketPretty(table, ticket):
        if not ticket:
            return
        table.add_row([ticket.trainNo,
                       '\n'.join([Fore.GREEN + ticket.fromStation + Fore.RESET,
                                  Fore.RED + ticket.toStation + Fore.RESET]),
                       '\n'.join(
                           [Fore.GREEN + ticket.leaveTime + Fore.RESET,
                            Fore.RED + ticket.arriveTime + Fore.RESET]),
                       ticket.totalConsume,
                       ticket.businessSeat or '--',
                       ticket.firstClassSeat or '--',
                       ticket.secondClassSeat or '--',
                       ticket.advancedSoftSleep or '--',
                       ticket.softSleep or '--',
                       ticket.moveSleep or '--',
                       ticket.hardSleep or '--',
                       ticket.softSeat or '--',
                       ticket.hardSeat or '--',
                       ticket.noSeat or '--',
                       ticket.other or '--',
                       ticket.mark or '--']
                      )

    @staticmethod
    def querySpec(trainDate, fromStation, toStation, passengerType=PASSENGER_TYPE_ADULT, trainsNo=[],
                  seatTypes=[SEAT_TYPE[key] for key in SEAT_TYPE]):
        tickets = Query.query(trainDate, fromStation, toStation, passengerType)
        for ticket in tickets:

            # filter trainNo
            if not TrainUtils.filterTrain(ticket, trainsNo):
                continue
            # filter seat
            for seatTypeName, seatTypeProperty in TrainUtils.seatWhich(seatTypes, ticket):
                if seatTypeProperty and seatTypeProperty != '无' and seatTypeProperty != '*':
                    Log.info('%s: %s' % (seatTypeName, seatTypeProperty))
                    ticket.seatType = SEAT_TYPE[seatTypeName]
                    yield ticket
        return []

    @staticmethod
    def loopQuery(trainDate, fromStation, toStation, passengerType=PASSENGER_TYPE_ADULT, trainsNo=[],
                  seatTypes=[SEAT_TYPE[key] for key in SEAT_TYPE], count=0, timeInterval=QUERY_TICKET_REFERSH_INTERVAL):
        while True:
            count += 1
            Log.info('正在为您刷票: %d 次' % count)
            if count % 10 == 0:
                jsonRet = EasyHttp.send(loginUrls['normal']['checkUser'])
                Log.debug('checkUser: %s' % jsonRet)
            for ticketDetails in Query.querySpec(trainDate, fromStation, toStation, passengerType, trainsNo, seatTypes):
                if ticketDetails:
                    yield ticketDetails
            time.sleep(timeInterval)


if __name__ == "__main__":
    # for ticket in Query.query('2017-12-31', '深圳北', '潮汕'):
    ticket = Query.outputPretty('2019-01-17', '上海', '杭州')
    # print(ticket)
