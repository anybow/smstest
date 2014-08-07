# -*- coding: utf-8 -*-
__author__ = 'syber'
"""
    可用性测试结果分析上传工具v0.17
    1、支持Android版本和windows mobile版本的日志文件分析。
    2、日志文件中需要手工在第一行写测试的省分名，第二行写测试的手机号。
    3、在文件前面的全局变量区有可用性测试账号信息，用户名myname，账号mypwd，缺省为空，需要在运行时手工填写。
    用户可以自行填上自己的账户信息，系统采用myname和mypwd的值自动登录。
    4、新增测试省份字段，缺省值为空，可以自行填写，如不填则在运行时提示填写。若省份与账号的对应关系不对则会导致读取网站数据错误。
    5、先选择日志文件进行分析，再选择上传报告即可。

    更新日志：
    2014年7月18日发布v0.17版本
        新增对Android版日志的测试卡限额的处理
        修复一个特定情况下报告上传失败的bug
        修复测试账号省份与日志省份混淆的bug
    2014年7月16日发布v0.16版本
        解决测试省份逻辑关系错乱导致多个不同省份的日志上传失败的问题。
    2014年7月16日发布v0.15版本
        解决账号与测试省分的绑定关系带来的网站数据读取问题，增加了测试省分的填写和输入
    2014年7月15日发布v0.13版本
        增加系统容错能力，允许一个日志文件中只存在部分业务。对于分拆多个测试文件生成多个日志的用户可以分别分析每个日志
        文件，但每个文件仍需要添加省分，电话号码信息。
    2014年7月8日第一次发布v0.12版本
        具备Android和windows mobile版本日志的分析，上传功能。
"""
import  re, urllib.parse, urllib.request, http.cookiejar, os, tkinter.filedialog,codecs
"""全局变量区"""
myname = ""        #可用性系统网站用户名，将自己的信息填在引号里，可自动登录用
mypwd = ""         #可用性系统网站登录密码
myprovice = ""     #填写该账号负责的任一省分信息，系统需要根据该信息读取网站数据，如果填写错误将得不到正确结果

#日志文件分析处理相关变量
logfile = []    #读取的日志文件全局变量
logfileversion = "Android"
sms_report=[]   #日志分析后的报告文件
sms_status =('业务正常，无故障','上行无响应','无资费提醒','提示：点播失败','提示：发送指令或号码错误','提示：产品状态不正常','其他:无SP下行信息','其他:包月业务无二次确认信息','异常','其他：测试卡点播限额','未测试')
                #0                  1              2            3               4                               5                       6                       7                8       9                      10
encoder_smsurl = ('%E4%B8%9A%E5%8A%A1%E6%AD%A3%E5%B8%B8%EF%BC%8C%E6%97%A0%E6%95%85%E9%9A%9C',   #0：业务正常，无故障
                  '%E4%B8%8A%E8%A1%8C%E6%97%A0%E5%93%8D%E5%BA%94',                              #1：上行无响应
                  '%E6%97%A0%E8%B5%84%E8%B4%B9%E6%8F%90%E9%86%92',                              #2：无资费提醒
                  '%E6%8F%90%E7%A4%BA%EF%BC%9A%E7%82%B9%E6%92%AD%E5%A4%B1%E8%B4%A5',            #3：提示：点播失败
                  '%E6%8F%90%E7%A4%BA%EF%BC%9A%E5%8F%91%E9%80%81%E6%8C%87%E4%BB%A4%E6%88%96%E8%80%85%E5%8F%B7%E7%A0%81%E9%94%99%E8%AF%AF',   #4：提示：发送指令或号码错误
                  '%E6%8F%90%E7%A4%BA%EF%BC%9A%E4%BA%A7%E5%93%81%E7%8A%B6%E6%80%81%E4%B8%8D%E6%AD%A3%E5%B8%B8',             #5提示:产品状态不正常
                  "%E6%97%A0SP%E4%B8%8B%E8%A1%8C%E4%BF%A1%E6%81%AF",  #6:无SP下行信息   其他
                  "%E5%8C%85%E6%9C%88%E4%B8%9A%E5%8A%A1%E6%97%A0%E4%BA%8C%E6%AC%A1%E7%A1%AE%E8%AE%A4%E4%BF%A1%E6%81%AF",   #7： 包月业务无二次确认信息  其他
                  "%E5%85%B6%E4%BB%96",   #8：其他
                  "%E6%B5%8B%E8%AF%95%E5%8D%A1%E7%82%B9%E6%92%AD%E9%99%90%E9%A2%9D"  #9:测试卡点播限额
)
#没见过点播失败的信息是怎样的，故无法判断
smstesturl = "http://219.143.33.58/smstest/smstest.txt"     #可用性测试当期测试内容

#网站登录，提交数据相关变量
servicetype = "sms"
batch = 0           #测试批次数据，如当前为2014年1411批次
sms_startID = 0     #提交业务时，第一个业务的ID数
sms_count = 0        #本次测试短信业务总数
service_count = 0    #本次测试业务总数
proviceID = 0       #报告省份ID
myproviceID = 0     #用户账号能访问的省份的ID
proviceKey = ""     #报告省份的url参数
provicename =""     #报告省份的名称
phonenumber = 0     #报告的测试号码
limitflag = 0    #点播限额标识
loginurl = "http://219.143.33.58:8891/TestManage/login.jsp"
loginposturl = "http://219.143.33.58:8891/TestManage/login.action"
confirm_url = "http://219.143.33.58:8891/TestManage/save.action"


hasreport = False
provice ={      #省分编码
    "北京":1,
    "上海":2,
    "天津":3,
    "重庆":4,
    "河北":5,
    "山西":6,
    "内蒙古":7,
    "辽宁":8,
    "吉林":9,
    "黑龙江":10,
    "江苏": 11,
    "浙江": 12,
    "安徽": 13,
    "福建": 14,
    "江西": 15,
    "山东": 16,
    "河南": 17,
    "湖北": 18,
    "湖南": 19,
    "广东": 20,
    "广西": 21,
    "海南": 22,
    "四川": 23,
    "贵州": 24,
    "云南": 25,
    "西藏": 26,
    "陕西": 27,
    "甘肃": 28,
    "青海": 29,
    "宁夏": 30,
    "新疆": 31
}

"""cookie"""
cookiefile = os.getcwd()+"\cookie.txt"
cookie=http.cookiejar.LWPCookieJar()
if os.path.exists(cookiefile): cookie.load(cookiefile,True,True)
chandle=urllib.request.HTTPCookieProcessor(cookie)
"""获取数据"""
def getData(url):

    r=urllib.request.Request(url)
    r.add_header('User-agent', 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/6.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; InfoPath.3)')
    r.add_header('Content-Type', 'application/x-www-form-urlencoded')
    r.add_header('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7')	
    opener=urllib.request.build_opener(chandle)
    u=opener.open(r)
    chandle.cookiejar.save(cookiefile,True,True)
    data=u.read()
    try:
        data=data.decode('utf-8')
    except:
        data=data.decode('gbk','ignore')
    return data
def postData(url,data):
    data=urllib.parse.urlencode(data);data=bytes(data,'utf-8')
    r=urllib.request.Request(url,data)
    opener=urllib.request.build_opener(chandle)
    u=opener.open(r)
    chandle.cookiejar.save(cookiefile,True,True)
    data=u.read()
    try:
        data=data.decode('utf-8')
    except:
        data=data.decode('gbk','ignore')
    return data

def splitdata(smsdata):                 #网上的待测数据整理
    prestr_split_line = re.compile(r'\r\n')  #预编译 分割行
    prestr_split_col  = re.compile(r'\|')  #预编译，分割每条记录
    linedata = prestr_split_line.split(smsdata)
    returnlist=[]
    for a in range(len(linedata)):
        coldata = prestr_split_col.split(linedata[a])
        coldata = [a+1]+coldata                    #在每行前面加个序号
        returnlist.append(coldata)
    return returnlist

def selectlog():
    logfile = tkinter.filedialog.askopenfilename(filetypes = [("短信测试日志文件", "*.txt"),("所有文件","*.*")],defaultextension = ".txt")
    if logfile:
        lines = open(logfile,'r')
        logdata =lines.readlines(100000)
        lines.close()
        return logdata
    else:
        return False
def selectlogutf():
    logfile = tkinter.filedialog.askopenfilename(filetypes = [("短信测试日志文件", "*.txt"),("所有文件","*.*")],defaultextension = ".txt")
    if logfile:
        lines = codecs.open(logfile,'r','utf-8')
        logdata =lines.readlines(100000)
        lines.close()
        return logdata
    else:
        return False
def smsdb(sn,smsno,command,sname):
    #判断短信业务成功条件
    #返回成功或者错误信息。成功是0，错误有代码表
    global logfile
    global limitflag
    if limitflag ==1: return 9  #只要出现一次点播限额判断，后面的点播业务都会是限额的。
    report =[0,0,0,0,0,0,0,0]   #0:业务名称行数，1：是否存在业务名，2：是否存在发送指令，3：是否存在10001888资费信息，4：接收SP信息，5：指令不正确，6：产品状态不正常,7:点播限额
    prestr_title = re.compile("(【"+str(sn)+"】"+sname+"（点播）)")         #1判断当前业务名
    prestr_send = re.compile("(【发送】"+str(smsno)+":"+str(command)+")")      #2判断当前业务发送指令
    prestr_10000 = re.compile("(【接收】10001888:感谢您使用).*(提供的"+str(sname)+")")     #3判断10001888资费信息，需要正则表达式了
    prestr_reciver = re.compile("(【接收】"+str(smsno)+")")      #4判断接收SP信息
    prestr_badcommand = re.compile("(【接收】10001888:对不起，您发送的指令或号码不正确)")     #5判断指令不正确
    prestr_badstatus = re.compile("(【接收】10001888:尊敬的客户，您申请的业务产品服务已由SP商暂停注销)")     #6判断产品状态不正常
    prestr_limit = re.compile("(【接收】10001888:你当日的点播上限)")   #判断点播限额
    for b in range(len(logfile)):
       record=prestr_title.search(logfile[b]) #1 业务名称处理
       if record:
           report[0] = b
           report[1] = 1
       record=prestr_send.search(logfile[b]) #2 发送指令处理
       if record: report[2] = 1
       record=prestr_10000.search(logfile[b]) #3 10001888资费信息处理
       if record: report[3] = 1
       record=prestr_reciver.search(logfile[b]) #4 SP接收的信息处理
       if record and report[0]!=0: report[4] = 1  #相同接入号的情况下，要在指定的业务名称出现后的接收信息才算。
       record=prestr_badcommand.search(logfile[b]) #5 指令不正确的信息处理
       if record and b-report[0]<3:report[5] = 1                 #只有紧接着发送指令记录的不正确指令信息才有关联关系
       record=prestr_badstatus.search(logfile[b]) #6 产品状态不正常的信息处理
       if record and b-report[0]<3:report[6] = 1                 #只有紧接着发送指令记录的产品状态不正常信息才有关联关系
       record=prestr_limit.search(logfile[b]) #6 点播限额常的信息处理
       if record and b-report[0]<3:
           report[7] = 1                 #只有紧接着发送指令记录的点播限额信息才有关联关系
           limitflag = 1
           return 9                     #返回sms_status(9)  其他：测试卡点播限额

       #报告最终状态判断
#    print("判断结果是：%s %i %i %i %i %i %i"%(sn,report[1],report[2],report[3],report[4],report[5],report[6]))
    if   report[1]== 1 and report[2]== 1 and report[3]==1 and report[4]== 1:return 0  #业务正常
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]== 0 and report[5]==0 and report[6]==0:return 1  #上行无响应
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==1:return 2  #无资费提醒
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[5]==1:return 4  #指令不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[6]==1:return 5  #产品状态不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==1 and report[4]==0 and report[5]==0 and report[6]==0:return 6  #其他：无SP下行信息
    elif report[1]== 0:return 10   #该业务未测试
    else:
        return 8    #数据异常

def mmsdb(sn,smsno,command,sname):
    #判断彩信业务成功条件
    #返回成功或者错误信息。成功是0，错误有代码表
    global logfile
    global limitflag
    if limitflag ==1: return 9  #只要出现一次点播限额判断，后面的点播业务都会是限额的。
    report =[0,0,0,0,0,0,0,0]   #0:业务名称行数，1：是否存在业务名，2：是否存在发送指令，3：是否存在10001888资费信息，4：接收SP信息，5：指令不正确，6：产品状态不正常,7:点播限额
    prestr_title = re.compile("(【"+str(sn)+"】"+sname+"（点播）)")         #1判断当前业务名
    prestr_send = re.compile("(【发送】"+str(smsno)+":"+str(command)+")")      #2判断当前业务发送指令
    prestr_10000 = re.compile("(【接收】10001888:感谢您使用).*(提供的"+str(sname)+")")     #3判断10001888资费信息，需要正则表达式了
    prestr_reciver = re.compile("(【接收】"+str(smsno)+")")      #4判断接收SP信息
    prestr_badcommand = re.compile("(【接收】10001888:对不起，您发送的指令或号码不正确)")     #5判断指令不正确
    prestr_badstatus = re.compile("(【接收】10001888:尊敬的客户，您申请的业务产品服务已由SP商暂停注销)")     #6判断产品状态不正常
    prestr_limit = re.compile("(【接收】10001888:你当日的点播上限)")   #判断点播限额

    for b in range(len(logfile)):
       record=prestr_title.search(logfile[b]) #1 业务名称处理
       if record:
           report[0] = b
           report[1] = 1
       record=prestr_send.search(logfile[b]) #2 发送指令处理
       if record: report[2] = 1
       record=prestr_10000.search(logfile[b]) #3 10001888资费信息处理
       if record: report[3] = 1
       record=prestr_reciver.search(logfile[b]) #4 SP接收的信息处理
       if record and report[0]!=0: report[4] = 1  #相同接入号的情况下，要在指定的业务名称出现后的接收信息才算。
       record=prestr_badcommand.search(logfile[b]) #5 指令不正确的信息处理
       if record and b-report[0]<3:report[5] = 1                 #只有紧接着发送指令记录的不正确指令信息才有关联关系
       record=prestr_badstatus.search(logfile[b]) #6 产品状态不正常的信息处理
       if record and b-report[0]<3:report[6] = 1                 #只有紧接着发送指令记录的产品状态不正常信息才有关联关系
       record=prestr_limit.search(logfile[b]) #6 点播限额常的信息处理
       if record and b-report[0]<3:
           report[7] = 1                 #只有紧接着发送指令记录的点播限额信息才有关联关系
           limitflag = 1
           return 9                     #返回sms_status(9)  其他：测试卡点播限额

       #报告最终状态判断
#    print("判断结果是：%s %i %i %i %i %i %i"%(sn,report[1],report[2],report[3],report[4],report[5],report[6]))
    #彩信业务判断SP下行的情况不同，sp下行的是彩信，在日志中未体现
    if   report[1]== 1 and report[2]== 1 and report[3]==1 :return 0  #业务正常
    elif report[1]== 1 and report[2]== 1 and report[3]==0  and report[5]==0 and report[6]==0:return 1  #上行无响应
    elif report[1]== 1 and report[2]== 1 and report[3]==0 :return 2  #无资费提醒
    elif report[1]== 1 and report[2]== 1 and report[3]==0  and report[5]==1:return 4  #指令不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==0  and report[6]==1:return 5  #产品状态不正确
    elif report[1]== 0:return 10   #该业务未测试
    else:
        return 8    #数据异常
def smsby(sn,smsno,command,sname):
    global logfile
    report =[0,0,0,0,0,0,0,0]   #0:业务名称行数，1：是否存在业务名，2：是否存在发送指令，3：是否存在10001888定购成功信息，4：接收SP信息，5：指令不正确，6：产品状态不正常,7:10000二次确认信息
    prestr_title = re.compile("(【"+str(sn)+"】"+sname+"（包月）)")         #1判断当前业务名
    prestr_send = re.compile("(【发送】"+str(smsno)+":"+str(command)+")")      #2判断当前业务发送指令
    prestr_10000 = re.compile("(您已成功定制).*(提供的"+str(sname)+")")     #3判断10001888的定购成功信息，需要正则表达式了
    prestr_reciver = re.compile("(【接收】"+str(smsno[:8])+")")      #4判断接收SP信息,取接入号的前8位
    prestr_badcommand = re.compile("(【接收】10001888:对不起，您发送的指令或号码不正确)")     #5判断指令不正确
    prestr_badstatus = re.compile("(【接收】10001888:尊敬的客户，您申请的业务产品服务已由SP商暂停注销)")     #6判断产品状态不正常
    prestr_10000confirm = re.compile("(您即将定制).*(提供的"+str(sname)+")")     #7判断10001888的二次确认信息，需要正则表达式了
    for b in range(len(logfile)):
       record=prestr_title.search(logfile[b]) #1 业务名称处理
       if record:
           report[0] = b
           report[1] = 1
       record=prestr_send.search(logfile[b]) #2 发送指令处理
       if record: report[2] = 1
       record=prestr_10000.search(logfile[b]) #3 10000定购成功信息处理
       if record: report[3] = 1
       record=prestr_reciver.search(logfile[b]) #4 SP接收的信息处理，只取接入号的前8位
       if record and report[0]!=0: report[4] = 1  #相同接入号的情况下，要在指定的业务名称出现后的接收信息才算。
       record=prestr_badcommand.search(logfile[b]) #5 指令不正确的信息处理
       if record and b-report[0]<3:report[5] = 1                 #只有紧接着发送指令记录的不正确指令信息才有关联关系
       record=prestr_badstatus.search(logfile[b]) #6 产品状态不正常的信息处理
       if record and b-report[0]<3:report[6] = 1                 #只有紧接着发送指令记录的产品状态不正常信息才有关联关系
       record=prestr_10000confirm.search(logfile[b]) #7 10000二次确认信息
       if record :report[7] = 1
       #报告最终状态判断
#    print("判断结果是：%s %i %i %i %i %i %i %i"%(sn,report[1],report[2],report[3],report[4],report[5],report[6],report[7]))
    if   report[1]== 1 and report[2]== 1 and report[3]==1 and report[4]==1 and report[7]==1:return 0  #业务正常
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[5]==0 and report[6]==0 and report[7]==0:return 1  #上行无响应
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[5]==0 and report[6]==0 and report[7]==0 :return 7  #无包月业务二次确认信息
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[5]==1:return 4  #指令不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[6]==1:return 5  #产品状态不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==1 and report[4]==0 and report[5]==0 and report[6]==0 and report[7]==1:return 6  #其他：无SP下行信息
    elif report[1]== 0:return 10   #该业务未测试
    else:
        return 8    #数据异常

def mmsby(sn,smsno,command,sname):
    global logfile
    report =[0,0,0,0,0,0,0,0]   #0:业务名称行数，1：是否存在业务名，2：是否存在发送指令，3：是否存在10001888定购成功信息，4：接收SP信息，5：指令不正确，6：产品状态不正常,7:10000二次确认信息
    prestr_title = re.compile("(【"+str(sn)+"】"+sname+"（包月）)")         #1判断当前业务名
    prestr_send = re.compile("(【发送】"+str(smsno)+":"+str(command)+")")      #2判断当前业务发送指令
    prestr_10000 = re.compile("(您已成功定制).*(提供的"+str(sname)+")")     #3判断10001888的定购成功信息，需要正则表达式了
    prestr_reciver = re.compile("(【接收】"+str(smsno[:8])+")")      #4判断接收SP信息,取接入号的前8位
    prestr_badcommand = re.compile("(【接收】10001888:对不起，您发送的指令或号码不正确)")     #5判断指令不正确
    prestr_badstatus = re.compile("(【接收】10001888:尊敬的客户，您申请的业务产品服务已由SP商暂停注销)")     #6判断产品状态不正常
    prestr_10000confirm = re.compile("(您即将定制).*(提供的"+str(sname)+")")     #7判断10001888的二次确认信息，需要正则表达式了
    for b in range(len(logfile)):
       record=prestr_title.search(logfile[b]) #1 业务名称处理
       if record:
           report[0] = b
           report[1] = 1
       record=prestr_send.search(logfile[b]) #2 发送指令处理
       if record: report[2] = 1
       record=prestr_10000.search(logfile[b]) #3 10000定购成功信息处理
       if record: report[3] = 1
       record=prestr_reciver.search(logfile[b]) #4 SP接收的信息处理，只取接入号的前8位
       if record and report[0]!=0: report[4] = 1  #相同接入号的情况下，要在指定的业务名称出现后的接收信息才算。
       record=prestr_badcommand.search(logfile[b]) #5 指令不正确的信息处理
       if record and b-report[0]<3:report[5] = 1                 #只有紧接着发送指令记录的不正确指令信息才有关联关系
       record=prestr_badstatus.search(logfile[b]) #6 产品状态不正常的信息处理
       if record and b-report[0]<3:report[6] = 1                 #只有紧接着发送指令记录的产品状态不正常信息才有关联关系
       record=prestr_10000confirm.search(logfile[b]) #7 10000二次确认信息
       if record :report[7] = 1
       #报告最终状态判断
#    print("判断结果是：%s %i %i %i %i %i %i %i"%(sn,report[1],report[2],report[3],report[4],report[5],report[6],report[7]))
    if   report[1]== 1 and report[2]== 1 and report[3]==1 and report[7]==1:return 0  #业务正常
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[5]==0 and report[6]==0 and report[7]==0:return 1  #上行无响应
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[5]==0 and report[6]==0 and report[7]==0 :return 7  #无包月业务二次确认信息
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[5]==1:return 4  #指令不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[6]==1:return 5  #产品状态不正确
    elif report[1]== 0:return 10   #该业务未测试
    else:
        return 8    #数据异常

def log_analys():               #Android版日志文件分析
   global logfile
   global hasreport
   global proviceID
   global phonenumber
   global sms_report
   global service_count
   global provicename
   global proviceKey
   logfile = selectlog()

   if logfile:
       provicename = logfile[0].strip()                 #读取省分信息
       proviceID = provice.get(provicename)             #对应省分ID
       if not proviceID:
           proviceID = 0
           provicename = ""
       elif proviceID<10:                               #为上传报告时的省份ID赋值
            proviceKey ='0'+str(proviceID)
       else:
            proviceKey = str(proviceID)
       phonenumber = logfile[1].strip()                 #读取电话号码
       if not re.search("[0-9]",phonenumber):phonenumber =0
       smsdata = splitdata(getData(smstesturl))  #取得待测业务数据
       service_count = len(smsdata)
       for a in range(sms_count):    #逐条指令处理短信业务len(smsdata)
         if smsdata[a][4] == "0":
            s = smsdb(smsdata[a][0],smsdata[a][2],smsdata[a][1],smsdata[a][5])             #点播业务结果判断
            sms_rs=[smsdata[a][0],smsdata[a][5],sms_status[s],s]
            sms_report.append(sms_rs)
         else:
            s = smsby(smsdata[a][0],smsdata[a][2],smsdata[a][1],smsdata[a][5])             #包月业务结果判断
            sms_rs=[smsdata[a][0],smsdata[a][5],sms_status[s],s]
            sms_report.append(sms_rs)
       for a in range(sms_count,service_count):    #逐条指令处理彩信业务len(smsdata)
         if smsdata[a][4] == "0":
            s = mmsdb(smsdata[a][0],smsdata[a][2],smsdata[a][1],smsdata[a][5])             #点播业务结果判断
            sms_rs=[smsdata[a][0],smsdata[a][5],sms_status[s],s]
            sms_report.append(sms_rs)
         else:
            s = mmsby(smsdata[a][0],smsdata[a][2],smsdata[a][1],smsdata[a][5])             #包月业务结果判断
            sms_rs=[smsdata[a][0],smsdata[a][5],sms_status[s],s]        #序号，业务名，报告状态，报告状态的序号
            sms_report.append(sms_rs)

       wfile=open('report.txt','w')         #报告写成文件
       lt = lambda x:(len(x)<4 and "\t") or ""
       print("             【短信业务测试结果】\n")
       for i in range(sms_count):                             #输出最终测试结果
            print("【%s】\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2]))
            wfile.write("%s\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2])+"\n")
       print("\n\n              【彩信业务测试结果】\n")
       for i in range(sms_count,service_count):                             #输出最终测试结果
            print("【%s】\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2]))
            wfile.write("%s\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2])+"\n")
       wfile.close()
       hasreport = True
   else:
       print("打开文件错误，或未选择文件。请重新选择")

def win_smsdb(sn,smsno,command,sname):
    #判断短信业务成功条件
    #返回成功或者错误信息。成功是0，错误有代码表
    global logfile
    report =[0,0,0,0,0,0,0]   #0:业务名称行数，1：是否存在业务名，2：是否存在发送指令，3：是否存在10001888资费信息，4：接收SP信息，5：指令不正确，6：产品状态不正常
    prestr_title = re.compile("(开始测试业务:"+sname+")")         #1判断当前业务名
    prestr_send = re.compile("(发送短信:"+str(command)+"至"+str(smsno)+")")      #2判断当前业务发送指令
    prestr_10000 = re.compile("(收到10001888成功点播短信:感谢您使用).*(提供的"+str(sname)+")")     #3判断10001888资费信息，需要正则表达式了
    prestr_reciver = re.compile("(收到SP下发短信,接入号:"+str(smsno)+")")      #4判断接收SP信息
    prestr_badcommand = re.compile("(【接收】10001888:对不起，您发送的指令或号码不正确)")     #5判断指令不正确
    prestr_badstatus = re.compile("(【接收】10001888:尊敬的客户，您申请的业务产品服务已由SP商暂停注销)")     #6判断产品状态不正常

    for b in range(len(logfile)):
       record=prestr_title.search(logfile[b]) #1 业务名称处理
       if record:
           report[0] = b
           report[1] = 1
       record=prestr_send.search(logfile[b]) #2 发送指令处理
       if record: report[2] = 1
       record=prestr_10000.search(logfile[b]) #3 10001888资费信息处理
       if record: report[3] = 1
       record=prestr_reciver.search(logfile[b]) #4 SP接收的信息处理
       if record and report[0]!=0: report[4] = 1  #相同接入号的情况下，要在指定的业务名称出现后的接收信息才算。
       record=prestr_badcommand.search(logfile[b]) #5 指令不正确的信息处理
       if record and b-report[0]<3:report[5] = 1                 #只有紧接着发送指令记录的不正确指令信息才有关联关系
       record=prestr_badstatus.search(logfile[b]) #6 产品状态不正常的信息处理
       if record and b-report[0]<3:report[6] = 1                 #只有紧接着发送指令记录的产品状态不正常信息才有关联关系

       #报告最终状态判断
#    print("判断结果是：%s %i %i %i %i %i %i"%(sn,report[1],report[2],report[3],report[4],report[5],report[6]))
    if   report[1]== 1 and report[2]== 1 and report[3]==1 and report[4]== 1:return 0  #业务正常
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]== 0 and report[5]==0 and report[6]==0:return 1  #上行无响应
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==1:return 2  #无资费提醒
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[5]==1:return 4  #指令不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[6]==1:return 5  #产品状态不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==1 and report[4]==0 and report[5]==0 and report[6]==0:return 6  #其他：无SP下行信息
    elif report[1]== 0:return 10   #该业务未测试
    else:
        return 8    #数据异常

def win_mmsdb(sn,smsno,command,sname):
    #判断彩信业务成功条件
    #返回成功或者错误信息。成功是0，错误有代码表
    global logfile
    report =[0,0,0,0,0,0,0]   #0:业务名称行数，1：是否存在业务名，2：是否存在发送指令，3：是否存在10001888资费信息，4：接收SP信息，5：指令不正确，6：产品状态不正常
    prestr_title = re.compile("(开始测试业务:"+sname+")")         #1判断当前业务名
    prestr_send = re.compile("(发送短信:"+str(command)+"至"+str(smsno)+")")      #2判断当前业务发送指令
    prestr_10000 = re.compile("(收到10001888成功点播短信:感谢您使用).*(提供的"+str(sname)+")")     #3判断10001888资费信息，需要正则表达式了
    prestr_reciver = re.compile("(收到SP下发短信,接入号:"+str(smsno)+")")      #4判断接收SP信息
    prestr_badcommand = re.compile("(【接收】10001888:对不起，您发送的指令或号码不正确)")     #5判断指令不正确
    prestr_badstatus = re.compile("(【接收】10001888:尊敬的客户，您申请的业务产品服务已由SP商暂停注销)")     #6判断产品状态不正常

    for b in range(len(logfile)):
       record=prestr_title.search(logfile[b]) #1 业务名称处理
       if record:
           report[0] = b
           report[1] = 1
       record=prestr_send.search(logfile[b]) #2 发送指令处理
       if record: report[2] = 1
       record=prestr_10000.search(logfile[b]) #3 10001888资费信息处理
       if record: report[3] = 1
       record=prestr_reciver.search(logfile[b]) #4 SP接收的信息处理
       if record and report[0]!=0: report[4] = 1  #相同接入号的情况下，要在指定的业务名称出现后的接收信息才算。
       record=prestr_badcommand.search(logfile[b]) #5 指令不正确的信息处理
       if record and b-report[0]<3:report[5] = 1                 #只有紧接着发送指令记录的不正确指令信息才有关联关系
       record=prestr_badstatus.search(logfile[b]) #6 产品状态不正常的信息处理
       if record and b-report[0]<3:report[6] = 1                 #只有紧接着发送指令记录的产品状态不正常信息才有关联关系

       #报告最终状态判断
#    print("判断结果是：%s %i %i %i %i %i %i"%(sn,report[1],report[2],report[3],report[4],report[5],report[6]))
    #彩信业务判断SP下行的情况不同，sp下行的是彩信，在日志中未体现
    if   report[1]== 1 and report[2]== 1 and report[3]==1 :return 0  #业务正常
    elif report[1]== 1 and report[2]== 1 and report[3]==0  and report[5]==0 and report[6]==0:return 1  #上行无响应
    elif report[1]== 1 and report[2]== 1 and report[3]==0 :return 2  #无资费提醒
    elif report[1]== 1 and report[2]== 1 and report[3]==0  and report[5]==1:return 4  #指令不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==0  and report[6]==1:return 5  #产品状态不正确
    elif report[1]== 0:return 10   #该业务未测试
    else:
        return 8    #数据异常
def win_smsby(sn,smsno,command,sname):
    global logfile
    report =[0,0,0,0,0,0,0,0]   #0:业务名称行数，1：是否存在业务名，2：是否存在发送指令，3：是否存在10001888定购成功信息，4：接收SP信息，5：指令不正确，6：产品状态不正常,7:10000二次确认信息
    prestr_title = re.compile("(开始测试业务:"+sname+")")         #1判断当前业务名
    prestr_send = re.compile("(发送短信:"+str(command)+"至"+str(smsno)+")")      #2判断当前业务发送指令
    prestr_10000 = re.compile("(您已成功定制).*(提供的"+str(sname)+")")     #3判断10001888的定购成功信息，需要正则表达式了
    prestr_reciver = re.compile("(收到"+str(smsno[:8])+")[0-9]*(成功点播短信)")      #4判断接收SP信息,取接入号的前8位
    prestr_badcommand = re.compile("(【接收】10001888:对不起，您发送的指令或号码不正确)")     #5判断指令不正确
    prestr_badstatus = re.compile("(【接收】10001888:尊敬的客户，您申请的业务产品服务已由SP商暂停注销)")     #6判断产品状态不正常
    prestr_10000confirm = re.compile("(您即将定制).*(提供的"+str(sname)+")")     #7判断10001888的二次确认信息，需要正则表达式了
    for b in range(len(logfile)):
       record=prestr_title.search(logfile[b]) #1 业务名称处理
       if record:
           report[0] = b
           report[1] = 1
       record=prestr_send.search(logfile[b]) #2 发送指令处理
       if record: report[2] = 1
       record=prestr_10000.search(logfile[b]) #3 10000定购成功信息处理
       if record: report[3] = 1
       record=prestr_reciver.search(logfile[b]) #4 SP接收的信息处理，只取接入号的前8位
       if record and report[0]!=0: report[4] = 1  #相同接入号的情况下，要在指定的业务名称出现后的接收信息才算。
       record=prestr_badcommand.search(logfile[b]) #5 指令不正确的信息处理
       if record and b-report[0]<3:report[5] = 1                 #只有紧接着发送指令记录的不正确指令信息才有关联关系
       record=prestr_badstatus.search(logfile[b]) #6 产品状态不正常的信息处理
       if record and b-report[0]<3:report[6] = 1                 #只有紧接着发送指令记录的产品状态不正常信息才有关联关系
       record=prestr_10000confirm.search(logfile[b]) #7 10000二次确认信息
       if record :report[7] = 1
       #报告最终状态判断
#    print("判断结果是：%s %i %i %i %i %i %i %i"%(sn,report[1],report[2],report[3],report[4],report[5],report[6],report[7]))
    if   report[1]== 1 and report[2]== 1 and report[3]==1 and report[4]==1 and report[7]==1:return 0  #业务正常
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[5]==0 and report[6]==0 and report[7]==0:return 1  #上行无响应
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[5]==0 and report[6]==0 and report[7]==0 :return 7  #无包月业务二次确认信息
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[5]==1:return 4  #指令不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[4]==0 and report[6]==1:return 5  #产品状态不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==1 and report[4]==0 and report[5]==0 and report[6]==0 and report[7]==1:return 6  #其他：无SP下行信息
    elif report[1]== 0:return 10   #该业务未测试
    else:
        return 8    #数据异常

def win_mmsby(sn,smsno,command,sname):
    global logfile
    report =[0,0,0,0,0,0,0,0]   #0:业务名称行数，1：是否存在业务名，2：是否存在发送指令，3：是否存在10001888定购成功信息，4：接收SP信息，5：指令不正确，6：产品状态不正常,7:10000二次确认信息
    prestr_title = re.compile("(开始测试业务:"+sname+")")         #1判断当前业务名
    prestr_send = re.compile("(发送短信:"+str(command)+"至"+str(smsno)+")")      #2判断当前业务发送指令
    prestr_10000 = re.compile("(您已成功定制).*(提供的"+str(sname)+")")     #3判断10001888的定购成功信息，需要正则表达式了
    prestr_reciver = re.compile("(收到"+str(smsno[:8])+")[0-9]*(成功点播短信)")      #4判断接收SP信息,取接入号的前8位
    prestr_badcommand = re.compile("(【接收】10001888:对不起，您发送的指令或号码不正确)")     #5判断指令不正确
    prestr_badstatus = re.compile("(【接收】10001888:尊敬的客户，您申请的业务产品服务已由SP商暂停注销)")     #6判断产品状态不正常
    prestr_10000confirm = re.compile("(您即将定制).*(提供的"+str(sname)+")")     #7判断10001888的二次确认信息，需要正则表达式了
    for b in range(len(logfile)):
       record=prestr_title.search(logfile[b]) #1 业务名称处理
       if record:
           report[0] = b
           report[1] = 1
       record=prestr_send.search(logfile[b]) #2 发送指令处理
       if record: report[2] = 1
       record=prestr_10000.search(logfile[b]) #3 10000定购成功信息处理
       if record: report[3] = 1
       record=prestr_reciver.search(logfile[b]) #4 SP接收的信息处理，只取接入号的前8位
       if record and report[0]!=0: report[4] = 1  #相同接入号的情况下，要在指定的业务名称出现后的接收信息才算。
       record=prestr_badcommand.search(logfile[b]) #5 指令不正确的信息处理
       if record and b-report[0]<3:report[5] = 1                 #只有紧接着发送指令记录的不正确指令信息才有关联关系
       record=prestr_badstatus.search(logfile[b]) #6 产品状态不正常的信息处理
       if record and b-report[0]<3:report[6] = 1                 #只有紧接着发送指令记录的产品状态不正常信息才有关联关系
       record=prestr_10000confirm.search(logfile[b]) #7 10000二次确认信息
       if record :report[7] = 1
       #报告最终状态判断
#    print("判断结果是：%s %i %i %i %i %i %i %i"%(sn,report[1],report[2],report[3],report[4],report[5],report[6],report[7]))
    if   report[1]== 1 and report[2]== 1 and report[3]==1 and report[7]==1:return 0  #业务正常
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[5]==0 and report[6]==0 and report[7]==0:return 1  #上行无响应
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[5]==0 and report[6]==0 and report[7]==0 :return 7  #无包月业务二次确认信息
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[5]==1:return 4  #指令不正确
    elif report[1]== 1 and report[2]== 1 and report[3]==0 and report[6]==1:return 5  #产品状态不正确
    elif report[1]== 0:return 10   #该业务未测试
    else:
        return 8    #数据异常
def log_analys2():              #windows 版日志文件分析
   global logfile
   global hasreport
   global proviceID
   global phonenumber
   global sms_report
   global service_count
   global provicename
   global logfileversion
   global servicename
   global proviceKey
   logfile = selectlogutf()

   if logfile:
       provicename = logfile[0].strip()
       proviceID = provice.get(provicename)
       if not proviceID:
           proviceID = 0
           provicename = ""
       elif proviceID<10:                               #为上传报告时的省份ID赋值
            proviceKey ='0'+str(proviceID)
       else:
            proviceKey = str(proviceID)
       phonenumber = logfile[1].strip()
       if not re.search("[0-9]",phonenumber):phonenumber =0
       smsdata = splitdata(getData(smstesturl))  #取得待测业务数据
       service_count = len(smsdata)
       for a in range(sms_count):    #逐条指令处理短信业务len(smsdata)
         if smsdata[a][4] == "0":
            s = win_smsdb(smsdata[a][0],smsdata[a][2],smsdata[a][1],smsdata[a][5])             #点播业务结果判断
            sms_rs=[smsdata[a][0],smsdata[a][5],sms_status[s],s]
            sms_report.append(sms_rs)
         else:
            s = win_smsby(smsdata[a][0],smsdata[a][2],smsdata[a][1],smsdata[a][5])             #包月业务结果判断
            sms_rs=[smsdata[a][0],smsdata[a][5],sms_status[s],s]
            sms_report.append(sms_rs)
       for a in range(sms_count,service_count):    #逐条指令处理彩信业务len(smsdata)
         if smsdata[a][4] == "0":
            s = win_mmsdb(smsdata[a][0],smsdata[a][2],smsdata[a][1],smsdata[a][5])             #点播业务结果判断
            sms_rs=[smsdata[a][0],smsdata[a][5],sms_status[s],s]
            sms_report.append(sms_rs)
         else:
            s = win_mmsby(smsdata[a][0],smsdata[a][2],smsdata[a][1],smsdata[a][5])             #包月业务结果判断
            sms_rs=[smsdata[a][0],smsdata[a][5],sms_status[s],s]
            sms_report.append(sms_rs)

       wfile=open('report.txt','w')         #报告写成文件
       lt = lambda x:(len(x)<4 and "\t") or ""
       print("             【短信业务测试结果】\n")
       for i in range(sms_count):                             #输出最终测试结果
            print("【%s】\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2]))
            wfile.write("%s\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2])+"\n")
       print("\n\n              【彩信业务测试结果】\n")
       for i in range(sms_count,service_count):                             #输出最终测试结果
            print("【%s】\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2]))
            wfile.write("%s\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2])+"\n")
       wfile.close()
       hasreport = True
       logfileversion="Windows"
   else:
       print("打开文件错误，或未选择文件。请重新选择")

def textmenu():
    menu=""
    global logfileversion
    global myname
    global mypwd
    global myprovice
    global proviceID
    global provicename
    global myproviceID
    if myname =="" or mypwd =="" or myprovice == "":
        print("\n                 可用性测试结果分析上传工具\n\n")
        print("验证可用性测试网站账号密码......\n\n ")
        myname = input("请输入可用性测试网站账号：")
        print("\n")
        mypwd = input("请输入可用性测试网站密码：")
        print("\n")
        myprovice = input("请输入测试的省份：")
        try:
            myproviceID = provice.get(myprovice)
        except Exception as e:
            print("省份输入错误！")
    else:
        try:
            myproviceID = provice.get(myprovice)
            if not myproviceID:
                myproviceID =0
                print(" 省份信息填写错误！")
        except Exception as e:
            print("省份信息错误！")
    os.system("cls")
    if login():
        if myproviceID:
            getwebdata()
            while True:
                os.system("mode con cols=60 lines=30 &color F0 &title=可用性测试结果分析上传工具")
                print("\n                 可用性测试结果分析上传工具\n\n")
                print(" [1]选择日志文件（Android版）  ",end="")
                if hasreport and logfileversion =="Android":
                    print("完成日志分析按[v]查看\n")
                else:
                    print("\n")
                print(" [2]选择日志文件（Windows Mobile版）  ",end="")
                if hasreport and logfileversion =="Windows":
                    print("完成日志分析按[v]查看\n")
                else:
                    print("\n")
                print(" [3]上传报告\n")
                print(" [X]退出\n\n")
                print("------------上传报告前请核对以下信息：--------------")
                print("当前批次：%s    "%batch,end="")
                if service_count !=0:
                    print("%i条短信业务，"%sms_count,end="")
                    print("%i条彩信业务"%(service_count-sms_count))
                if proviceID != 0 :print("报告省分：%s"%provicename)
                if phonenumber != 0:print("测试号码：%s"%phonenumber)
                print("\n----------------------------------------------------\n")
                menu = input('    请输入菜单编号:')
                if menu == 'x'or menu == 'X':
                    print('成功退出')
                    break
                elif (menu == 'v'or menu == 'V')and hasreport:
                   os.system("cls")
                   os.system("mode con cols=80 lines=45")
                   lt = lambda x:(len(x)<4 and "\t") or ""
                   print("              【短信业务测试结果】\n")
                   for i in range(sms_count):                             #输出报告供查看
                        print("【%s】\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2]))
                   print("\n\n           【彩信业务测试结果】\n")
                   for i in range(sms_count,service_count):
                        print("【%s】\t%s%s\t%s"%(sms_report[i][0],sms_report[i][1],lt(sms_report[i][1]),sms_report[i][2]))
                   os.system("pause  &cls")
                elif  menu.isdigit()and int(menu)==1:
                  os.system("cls")
                  os.system("mode con cols=80 lines=45")
                  log_analys()
                  os.system("pause  &cls")
                elif  menu.isdigit()and int(menu)==2:
                  os.system("cls")
                  os.system("mode con cols=80 lines=45")
                  log_analys2()
                  os.system("pause  &cls")
                elif  menu.isdigit()and int(menu)==3:
                   print( "上传数据处理")
                   if proviceID==0 or phonenumber ==0:
                       print("测试号码或报告省分信息缺失，请检查日志文件，重新分析生成报告")
                   elif sms_count==0:
                       print("  网站测试数据异常，请检查当前测试状态")
                   else:
                        sendreport()
                   os.system("pause  &cls")
                else:
                    print( '输入错误，请重新选择菜单对应的数字')
                    os.system("pause  &cls")
        else:
            print("省份信息错误，无法进行数据分析")
            os.system("pause")
    else:
        print("登录失败，退出程序")
        os.system("pause")

def login():
    global batch
    getData(loginurl)
    par={
        "loginId":myname,
        "loginCd":mypwd
    }
    islogin = postData(loginposturl,par)
    if islogin[3:7]=="html":
        return  True
    else:
        return False

def getwebdata():
    global batch
    global sms_count
    global sms_startID
    global myproviceID
    if myproviceID<10:
        myproviceKey ='0'+str(myproviceID)
    else:
        myproviceKey = str(myproviceID)
    batch_url = "http://219.143.33.58:8891/TestManage/query4list.action?serviceType=SMS&servicePth=1411&provinceKey=%s"%myproviceKey  #为获取批次读取的数据
    smsdata = getData(batch_url)      #登录后点短信,获取当前批次信息
    prestr_batch = re.compile(r'(?<=2014年-第)\d+(?=批)')
    prestr_serviceno = re.compile(r'(?<=title=")([\u4e00-\u9fa5a-zA-Z0-9]*)(?="><span style)')  #([\u4e00-\u9fa5]+)是检测汉字的代码，找出业务名称
    prestr_serviceid = re.compile(r'(?<=popWin\(\')[0-9]+(?=\', \')')
    batch = prestr_batch.search(smsdata).group()        #获取最新批次
    sms_url = "http://219.143.33.58:8891/TestManage/query4list.action?servicePth=%s&provinceKey=%s&serviceType=SMS&testPhone=&resultN1=&resultN2="%(batch,myproviceKey)
    smsdata = getData(sms_url)      #补全参数后访问页面，获取短信业务数量
    serviceno = prestr_serviceno.findall(smsdata)   #找出所有匹配的业务名称
    sms_tmp = prestr_serviceid.search(smsdata)
    if sms_tmp:
        sms_startID = int(sms_tmp.group())          #获取短信业务起始的ID值
    else:
        print("省份与账号对应关系错误，无法正确读取数据")
    sms_count = len(serviceno)  #短信业务数量

def sendreport():

    cdata={
        "btValue":"%E6%8F%90%E4%BA%A4",    #提交的urlencoder
        "bugPhenmN1":"",   #故障现象
        "bugReasonN2":"",
        "bugTypeN2":"",
        "comment":"",
        "dataId":0,         #短信业务ID，本期起始ID7478
        "provinceKey":0,       #省分ID
        "result":"fail",        #pass和fail
        "serviceType":"SMS",    #业务类型
        "stage":"N1",
        "testPhone":0,   #测试号码
        "trNo":0
    }
    #提交短信业务测试报告
    ft = lambda x:(x==0 and "pass") or "fail"         #根据报告的第四字段判断是否成功
    for i in range(sms_count):      #上传短信业务测试报告
        if sms_report[i][3]!=10:           #10表示该业务在选择的日志文件中未测试
            print("上传短信测试报告【%s】%s............."%(sms_report[i][0],sms_report[i][1]),end="")
            if sms_report[i][3]<6:          #状态编号大于6的问题类型是其他，然后再分sp无下行等详细原因。即其他:xxxxxx
                cdata.update({"bugPhenmN1":encoder_smsurl[sms_report[i][3]],
                              "dataId":str(sms_startID+i),
                              "result":ft(sms_report[i][3]),
                              "provinceKey":proviceKey,
                              "testPhone":str(phonenumber)})
            else:
                cdata.update({"comment":encoder_smsurl[sms_report[i][3]],
                              "bugPhenmN1":encoder_smsurl[8],
                              "dataId":str(sms_startID+i),
                              "result":ft(sms_report[i][3]),
                              "provinceKey":proviceKey,
                              "testPhone":str(phonenumber)})
            postData(confirm_url,cdata)
            cdata.update({"comment":""})
            print("OK！")

    for i in range(sms_count,service_count):      #上传彩信业务测试报告
        if sms_report[i][3]!=10:           #10表示该业务在选择的日志文件中未测试
            print("上传彩信测试报告【%s】%s............."%(sms_report[i][0],sms_report[i][1]),end="")
            if sms_report[i][3]<6:
                cdata.update({"bugPhenmN1":encoder_smsurl[sms_report[i][3]],
                              "dataId":str(sms_startID+i),
                              "result":ft(sms_report[i][3]),
                              "provinceKey":proviceKey,
                              "testPhone":str(phonenumber)})
            else:
                cdata.update({"comment":encoder_smsurl[sms_report[i][3]],
                              "bugPhenmN1":encoder_smsurl[8],
                              "dataId":str(sms_startID+i),
                              "result":ft(sms_report[i][3]),
                              "provinceKey":proviceKey,
                              "testPhone":str(phonenumber)})
            postData(confirm_url,cdata)
            cdata.update({"comment":""})
            print("OK！")

if __name__ == "__main__":
    os.system("mode con cols=60 lines=30 &color F0 &title=可用性测试结果分析上传工具")
    textmenu()