EasyTrain
-----------------
[12306](http://www.12306.cn/)自动抢票软件。

Usage
---------------------------------
0. 在执行前先执行python3 setup.py install 安装阿里云短信发送
1. 更改 const.py 中 阿里云的 key 和secret
2. 更改configure 中购买车票的信息
2. 在[Configure.py](https://github.com/Why8n/EasyTrain/blob/master/Configure.py)中配置车票信息。
3. 执行[easytrain.py](https://github.com/Why8n/EasyTrain/blob/master/easytrain.py)。

Notice
-------------
需要额外安装的第三方库:
* [requests](https://github.com/requests/requests)
* [Pillow](https://github.com/python-pillow/Pillow)
* [PrettyTable](https://github.com/lmaurits/prettytable)
* [colorama](https://github.com/tartley/colorama)

**注:**
* 登录模块分析可查看:[12306之登录流程解析](https://www.jianshu.com/p/ca93eba60609)
* 查询模块分析可查看:[12306之余票查询流程解析](https://www.jianshu.com/p/89f6170991c8)
* 下单模块分析可查看:[12306之下单流程解析](https://www.jianshu.com/p/6b1f94e32713)
