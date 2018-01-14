# 数据结构定义
from mongoengine import BooleanField
from mongoengine import DateTimeField
from mongoengine import Document
from mongoengine import EmbeddedDocument, EmbeddedDocumentField
from mongoengine import ReferenceField, LazyReferenceField
from mongoengine import FloatField
from mongoengine import IntField
from mongoengine import ListField
from mongoengine import StringField

# 车站
# @bjb|北京北|VAP|beijingbei|bjb|0
# @bjd|北京东|BOP|beijingdong|bjd|1
class Station(Document):
    py_code = StringField()    # @...
    name = StringField()
    tel_code = StringField()
    pinyin = StringField()     # 拼音
    initial = StringField()    # 首字母
    identity = StringField()

    def __repr__(self):
        return self.name + ' - ' + self.tel_code + ' - ' + self.pinyin


# 车次
# 类型  列车编号       车次  起点  终点
# D    24000000D10R  D1   北京  沈阳
class Train(Document):
    category = StringField()
    code = StringField()
    name = StringField()
    start = StringField()
    end = StringField()

    def __repr__(self):
        return self.category + ': ' + self.name + '(' + self.start + '-' + self.end + ')'


# 列车详情-停站信息
class StopInfo(EmbeddedDocument):
    isEnabled = BooleanField()
    station_no = IntField()       # 站序 始发站是1
    station_name = StringField()  # 站名
    arrive_time = StringField()   # 到站时间
    stopover_time = IntField()    # 停站时间 分钟'----'
    start_time = StringField()    # 发车时间

    def __repr__(self):
        return self.station_name + ':' + str(self.station_no) + ' (' + self.arrive_time + ' - ' + str(self.stopover_time) + ' - ' + self.start_time + ')'


# 列车详情
class TrainDetail(Document):
    station_train_code = StringField()  # 车次
    start_station_name = StringField()  # 始发站
    end_station_name = StringField()    # 终到站
    service_type = StringField()        # 服务类型
    train_class_name = StringField()    # 列车类型
    stop_info_list = ListField(EmbeddedDocumentField(StopInfo))

    def str(self):
        return self.__repr__()

    def __repr__(self):
        return self.station_train_code + ' (' + self.start_station_name + ' - ' + self.end_station_name + ')'

    def stop_list(self):
        stop_list = list()
        for stop in self.stop_info_list:
            stop_list.append(stop.station_name)
        return stop_list

# 车站详情-经过列车
class PassTrain(EmbeddedDocument):
    # 车次信息
    station_train_code = StringField()  # 车次
    start_station_name = StringField()  # 始发站
    end_station_name = StringField()    # 终到站
    service_type = StringField()        # 服务类型
    train_class_name = StringField()    # 列车类型

    # 车次在本站的停站信息
    isEnabled = BooleanField()
    station_no = IntField()       # 站序 始发站是1
    station_name = StringField()  # 站名
    arrive_time = StringField()   # 到站时间
    stopover_time = IntField()    # 停站时间 分钟'----'
    start_time = StringField()    # 发车时间

    def __repr__(self):
        return self.station_train_code + ':' + self.station_name + ' (' + self.arrive_time + ' - ' + str(
            self.stopover_time) + ' - ' + self.start_time + ')'


# 车站详情
class StationDetail(Document):
    station_name = StringField()  # 站名
    pass_train_list = ListField(EmbeddedDocumentField(PassTrain))
    pass_train_num = IntField()   # 过站车辆数
    def __repr__(self):
        return self.station_name + ' (经过车次数 ' + str(self.pass_train_num) + ')'