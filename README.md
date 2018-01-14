# fork from https://github.com/metromancn/Parse12306


## modify by youngspring1
Python版
原来只有解析的代码 但我想用解析出来的数据做点有意思的事情

## 分析12306 获取全国列车数据
本程序介绍了如何从12306网站抓取全国高速列车数据。

* 开发工具：PyCharm
* 语言：Python
* 存储：mongo engine

## 概述
本程序从12306网站抓取全国高速列车的数据。项目包含了所有数据抓取和数据解析的Python源代码，并在这个基础上实现高铁换乘方案。


## 具体步骤
1. 从12306下载、解析车站信息
2. 从12306下载、解析车次信息
3. 从12306下载、解析时刻表信息
4. 构建站点详细（经过列车车次、停留时间）信息


### 1. 从12306下载、解析车站信息
通过分析12306的网站代码，发现[全国车站信息的URL](https://kyfw.12306.cn/otn/resources/js/framework/station_name.js)

```
https://kyfw.12306.cn/otn/resources/js/framework/station_name.js
```

解析js中的数据，输出成以下格式

```
ID  电报码  站名    拼音        首字母  拼音码
0   BOP    北京北  beijingbei  bjb   bjb
```

### 2. 从12306下载、解析车次信息
通过分析12306的网站代码，发现[全国车次信息的URL](https://kyfw.12306.cn/otn/resources/js/query/train_list.js)。这个文件存储了当前60天的所有车次信息，大约有35MB。

```
https://kyfw.12306.cn/otn/resources/js/query/train_list.js
```

当前天-4, 一共100天的信息

解析数据，按照日期分割成以下格式。

```
类型  列车编号       车次  起点  终点
D    24000000D10R  D1   北京  沈阳
```
12306将全国列车分成了7类，C-城际高速，D-动车，G-高铁，K-普快，T-特快，Z-直达，O-其他列车。后面的换乘方案中我仅抽取 C-城际高速，D-动车，G-高铁 的数据。

### 3. 从12306下载、解析时刻表信息
首先Merge所有日期的车次，以车次和列车编号为KEY，去除重复后得到全部车次一览。  
然后根据各车站的电报码，得出下载时刻表用的URL。如下：

```
https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no=列车编号&from_station_telecode=出发车站电报码&to_station_telecode=到达车站电报码&depart_date=出发日期
```

##### 注意点
a) 部分车次仅在特定日期运营（比如:工作日，周末，节假日等）  
b) 同一车次，在不同日期，运营时刻和停靠车站可能不一样  
c) 同一车次同一列车编号，在不同日期，运营时刻和停靠车站完全一致  

根据时刻表URL，下载所有时刻表信息。（JSON格式）

解析json数据，分别输出完整的“车站”，“车次”，“时刻表”成以下格式

```
ID  电报码  站名    拼音        首字母  拼音码
0   BOP    北京北  beijingbei  bjb   bjb
```

```
车次   起点   终点 出发时间  到达时间 类别  服务
C1002 延吉西 长春  5：47    8：04   动车  2
```

```
车次   站序  站名   到站时间  出发时间  停留时间  是否开通
C1002 1    延吉西  ----    6:20     ----     TRUE
      2    长春    8:25    8:25     ----     TRUE
```

### 4. 构建站点详细（经过列车车次、停留时间）信息
对各个高铁站点，构建经过列车车次，停留时间的信息

```

```


## 许可
MIT License


## 12306额外可以使用的API

1. 余票查询

    https://kyfw.12306.cn/otn/lcxxcx/query?purpose_codes=ADULT&queryDate=2016-08-20&from_station=WHN&to_station=SNH



2. 查询 train_no 指定车次所有经过的站

    https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no=39000D302808&from_station_telecode=AOH&to_station_telecode=ZEK&depart_date=2016-08-20



3. 查询 train_no 指定车次票价

    https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no=39000D302808&from_station_no=01&to_station_no=12&seat_types=OMO&train_date=2016-08-19
    其中, from_station_no, to_station_no 以及 seat_types 来自接口 1