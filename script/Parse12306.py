import os
import json
import requests
import logging
import concurrent.futures
from script.models import Station, Train, TrainDetail, StopInfo, StationDetail, PassTrain

# 连接mongo
from mongoengine import connect
from script import config
connect(config.db_name)


# 1. Download & Parse station list from 12306
def get_station_list():
    logging.info('获取车站信息开始...')
    Station.drop_collection()

    try:
        url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js'
        resp = requests.get(url)
        resp_str = resp.text
        data = resp_str[resp_str.find("'") + 1: resp_str.rfind("'")]
        # print(data)

        station_list = data.split('@')
        for station in station_list:
            if station.find('|') > -1:
                details = station.split('|')
                point = Station()
                point.py_code = '@' + details[0]
                point.name = details[1]
                point.tel_code = details[2]
                point.pinyin = details[3]
                point.initial = details[4]
                point.identity = details[5]
                # save
                point.save()
    except Exception as exc:
        print(exc)
        logging.info('异常退出')
        return

    logging.info('获取到了 %s座 车站信息' % Station.objects().count())


# 2. Download & Parse train list from 12306
def get_train_list():
    logging.info('获取车次信息开始...')
    Train.drop_collection()

    try:
        url = 'https://kyfw.12306.cn/otn/resources/js/query/train_list.js'
        resp = requests.get(url)
        resp_str = resp.text
        data = resp_str[resp_str.find('{') + 1: resp_str.rfind('}')]
        json_data = json.loads('{' + data + '}')
        for day, day_value in json_data.items():
            print(day)
            if len(day_value) > 0:
                for category, trains in day_value.items():
                    print('category: ' + category)
                    for train in trains:
                        code = train['train_no']
                        detail_text = train['station_train_code']
                        name = detail_text[:detail_text.find('(')]
                        # start
                        start_station_name = detail_text[detail_text.find('(') + 1: detail_text.find('-')]
                        # 就保存个字符串吧 下面本来想保存referenced field的
                        # results = Station.objects(name=station_name)
                        # if results.count() > 1:
                        #     print(station_name)
                        # elif results.count() == 1:
                        #     tr.start = results[0]
                        # else:
                        #     tr.start = Station(name=station_name)

                        # end
                        end_station_name = detail_text[detail_text.find('-') + 1: detail_text.find(')')]
                        # 就保存个字符串吧 下面本来想保存referenced field的
                        # results = Station.objects(name=station_name)
                        # if results.count() > 1:
                        #     print(station_name)
                        # elif results.count() == 1:
                        #     tr.end = results[0]
                        # else:
                        #     tr.start = Station(name=station_name)

                        # check exist
                        results = Train.objects(category=category, code=code, name=name, start=start_station_name, end=end_station_name)
                        if results.count() >= 1:
                            print('%s 已经存在 跳过' % name)
                        else:
                            tr = Train()
                            tr.category = category
                            tr.code = code
                            tr.name = name
                            tr.start = start_station_name
                            tr.end = end_station_name
                            tr.save()

    except Exception as exc:
        print(exc)
        logging.info('异常退出')
        return

    logging.info('获取到了 %s次 车次信息' % Train.objects().count())


# 3. Download all train detail
def get_train_detail_list():
    # clear collection
    TrainDetail.drop_collection()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for result in Train.objects():
            if result.category == 'G':
                executor.submit(get_train_detail, result.code, result.start, result.end, '2018-01-22')


# 3.1 Download one train detail
def get_train_detail(train_no, from_station, to_station, depart_date):
    from_station_code = Station.objects(name=from_station).first().tel_code
    to_station_telecode = Station.objects(name=to_station).first().tel_code
    try:
        # url = 'https://kyfw.12306.cn/otn/czxx/queryByTrainNo'
        # params = {
        #     'train_no': train_no,
        #     'from_station_telecode': from_station_code,
        #     'to_station_telecode': to_station_telecode,
        #     'depart_date': depart_date,
        # }
        # resp = requests.get(url, params=params)
        url = 'https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no={}&from_station_telecode={}&to_station_telecode={}&depart_date={}'.format(
            train_no, from_station_code, to_station_telecode, depart_date)
        resp = requests.get(url)
        real_data = resp.json().get('data').get('data')
        if len(real_data) > 0:
            train_detail = TrainDetail()
            for item in real_data:
                if 'start_station_name' in item.keys():
                    train_detail.station_train_code = item.get('station_train_code', '')
                    train_detail.start_station_name = item.get('start_station_name', '')
                    train_detail.end_station_name = item.get('end_station_name', '')
                    train_detail.service_type = item.get('service_type', '')
                    train_detail.train_class_name = item.get('train_class_name', '')
                    train_detail.save()

                stop = StopInfo()
                stop.isEnabled = item.get('isEnabled', True)
                stop.station_no = int(item.get('station_no', '0'))
                stop.station_name = item.get('station_name', '')
                stop.arrive_time = item.get('arrive_time', '')
                stopover_time_text = item.get('stopover_time', '----')
                if '----' == stopover_time_text:
                    stop.stopover_time = 0
                else:
                    stop.stopover_time = int(stopover_time_text.replace('分钟', ''))
                stop.start_time = item.get('start_time', '')
                train_detail.stop_info_list.append(stop)
                train_detail.save()


            logging.info('保存 %s:%s-%s(%s)' % (train_detail.station_train_code, train_detail.start_station_name, \
                                              train_detail.end_station_name, len(train_detail.stop_info_list)))

    except Exception as exc:
        print(exc)
        return


# 下面是 https://kyfw.12306.cn/otn/czxx/queryByTrainNo 的返回结果示例
'''
{
    'status': True,
    'validateMessages': {
        
    },
    'messages': [
        
    ],
    'validateMessagesShowId': '_validatorMessage',
    'httpstatus': 200,
    'data': {
        'data': [
            {
                'end_station_name': '延吉西',
                'service_type': '2',
                'train_class_name': '动车',
                'start_time': '05: 47',
                'isEnabled': True,
                'station_name': '长春',
                'start_station_name': '长春',
                'station_no': '01',
                'arrive_time': '----',
                'station_train_code': 'C1001',
                'stopover_time': '----'
            },
            {
                'isEnabled': True,
                'start_time': '06: 29',
                'station_name': '吉林',
                'station_no': '02',
                'stopover_time': '2分钟',
                'arrive_time': '06: 27'
            },
            {
                'isEnabled': True,
                'start_time': '07: 25',
                'station_name': '敦化',
                'station_no': '03',
                'stopover_time': '2分钟',
                'arrive_time': '07: 23'
            },
            {
                'isEnabled': True,
                'start_time': '08: 04',
                'station_name': '延吉西',
                'station_no': '04',
                'stopover_time': '----',
                'arrive_time': '08: 04'
            }
        ]
    }
}
'''


# 4. Merge station stop info
def merge_station_stop_info():
    TrainDetail.drop_collection()

    # 多线程会引起重复写入的问题
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     for train_detail in TrainDetail.objects():
    #         executor.submit(merge_train_stop_info, train_detail)
    for train_detail in TrainDetail.objects():
        merge_train_stop_info(train_detail)

def merge_train_stop_info(train_detail):
    try:
        for stop_info in train_detail.stop_info_list:
            station_name = stop_info.station_name

            if exist_station_detail(station_name):
                # exist
                station_detail = StationDetail.objects(station_name=station_name).first()
            else:
                # new
                station_detail = StationDetail()
                station_detail.station_name=station_name

            pass_train = PassTrain()
            # 车次信息
            pass_train.station_train_code = train_detail.station_train_code
            pass_train.start_station_name = train_detail.start_station_name
            pass_train.end_station_name = train_detail.end_station_name
            pass_train.service_type = train_detail.service_type
            pass_train.train_class_name = train_detail.train_class_name
            # 车次在本站的停站信息
            pass_train.isEnabled = stop_info.isEnabled
            pass_train.station_no = stop_info.station_no
            pass_train.station_name = stop_info.station_name
            pass_train.arrive_time = stop_info.arrive_time
            pass_train.stopover_time = stop_info.stopover_time
            pass_train.start_time = stop_info.start_time

            logging.info('车站 %s (车次 %s)' % (pass_train.station_name, pass_train.station_train_code))
            station_detail.pass_train_list.append(pass_train)
            station_detail.save()
            station_detail.pass_train_num = len(station_detail.pass_train_list)
            station_detail.save()
    except Exception as exc:
        print(exc)
        return

# 检查是否保存
def exist_station_detail(station_name):
    count = StationDetail.objects(station_name=station_name).count()
    if count > 1:
        logging.info('有问题吧 %s' % station_name)
        return True
    elif count == 1:
        return True
    else:
        return False


# 经过车次top 20 的高铁站 可以直达的站点数目
def top_20_gaotie_direct():
    # 高铁站数目
    logging.info('全国高铁站总数 %s' % StationDetail.objects.count())

    # 经过车次top 20 的高铁站
    results = StationDetail.objects.order_by('-pass_train_num')[:20]
    top_ten_list = list()
    for result in results:
        top_ten_list.append(result.station_name)
        # logging.info('%s %s' % (result.station_name, result.pass_train_num))


    # 可以直达的站点
    for station_name in top_ten_list:
        reach_station_list = get_direct_station(station_name)
        logging.info('从 %s 可以直达 %s 座车站' % (station_name, len(reach_station_list)))
        logging.info(reach_station_list)


def get_direct_station(station_name):
    reach_station_list = list()
    result = StationDetail.objects(station_name=station_name).first()
    for pass_train in result.pass_train_list:
        station_train_code = pass_train.station_train_code
        train_detail = TrainDetail.objects(station_train_code=station_train_code).first()
        for stop_info in train_detail.stop_info_list:
            if not stop_info.station_name in reach_station_list:
                reach_station_list.append(stop_info.station_name)

    return reach_station_list


def find_transfer_plan():
    start = '南京南'
    end = '黄山北'
    depth = 0
    logging.info(find_path(start, end, depth))


def find_path(start, end, depth):
    try:
        depth = depth + 1
        logging.info('depth: %s' % depth)

        found = False
        path = list()
        reach_station_list = list()

        result = StationDetail.objects(station_name=start).first()
        for pass_train in result.pass_train_list:
            station_train_code = pass_train.station_train_code
            train_detail = TrainDetail.objects(station_train_code=station_train_code).first()
            for stop_info in train_detail.stop_info_list:
                if stop_info.station_name == end:
                    found = True
                    logging.info(start + '-' + station_train_code + '-' + stop_info.station_name)
                    path.append(station_train_code + '-' + stop_info.station_name)

                if not stop_info.station_name in reach_station_list:
                    reach_station_list.append(stop_info.station_name)

        if not found and depth < 2:
            for station_name in reach_station_list:
                path.extend(find_path(station_name, end, depth))
        else:
            return path

    except Exception as exc:
        logging.info(exc)
        return list()

def main():
    # 1. Download & Parse station list from 12306
    # get_station_list()

    # 2. Download & Parse train list from 12306
    # get_train_list()

    # 3. Download all train detail with url
    # get_train_detail_list()

    # 4. Merge station stop info
    # merge_station_stop_info()

    # 经过车次最多的高铁站 能直达的站点
    # top_20_gaotie_direct()

    # 中转换乘方案
    find_transfer_plan()

if __name__ == '__main__':
    # file
    log_file_name = os.path.join('logs', 'Parse12306.log')
    logging.basicConfig(level=logging.DEBUG, format='%(message)s', filename=log_file_name, filemode='w')

    # console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    main()