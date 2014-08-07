__author__ = 'syber'

# -*- coding:utf-8 -*-
# python3.3.3
import  os, re, urllib.parse, urllib.request, http.cookiejar, json
myname = "wangjin"
mypwd = "123456"
servicetype = "sms"

batch = 0
loginurl = "http://219.143.33.58:8891/TestManage/login.jsp"
posturl = "http://219.143.33.58:8891/TestManage/login.action"
batch_url = "http://219.143.33.58:8891/TestManage/query4list.action?serviceType=SMS&servicePth=1411&provinceKey=23"
sms_url = "http://219.143.33.58:8891/TestManage/query4list.action?servicePth=1411&provinceKey=23&serviceType=SMS&testPhone=&resultN1=&resultN2="
provice ={
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
cookie.load(cookiefile,True,True)
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

def mylogin():
    global batch
    getData(loginurl)
    par={
        "loginId":myname,
        "loginCd":mypwd
    }
    print(postData(posturl,par))
    smsdata = getData(batch_url)      #登录后点短信
    prestr_batch = re.compile(r'(?<=2014年-第)\d+(?=批)')
    prestr_serviceno = re.compile(r'(?<=title=")([\u4e00-\u9fa5]*)(?="><span style)')  #([\u4e00-\u9fa5]+)是检测汉字的代码，找出业务名称
    prestr_serviceid = re.compile(r'(?<=popWin\(\')7478(?=\', \'23\'\))')
    batch = prestr_batch.search(smsdata).group()        #获取最新批次
    smsdata = getData(sms_url)      #补全参数后访问页面，测试有无必要
    serviceno = prestr_serviceno.findall(smsdata)   #找出所有匹配的业务名称
    serviceid = prestr_serviceid.search(smsdata)
    confirm_url = "http://219.143.33.58:8891/TestManage/save.action"
    cdata={
        "btValue":"提交",
        "bugPhenmN1":"%E5%8F%91%E9%80%81%E5%A4%B1%E8%B4%A5",   #故障现象
        "bugReasonN2":"",
        "bugTypeN2":"",
        "comment":"",
        "dataId":7484,
        "provinceKey":23,       #省分ID
        "result":"fail",        #pass和fail
        "serviceType":"SMS",    #业务类型
        "stage":"N1",
        "testPhone":18048490440,   #测试号码
        "trNo":0
    }
#    response = postData(confirm_url,cdata)
    print(serviceno)
    print(serviceid.group())
#    print(response)

def login(name,pwd):
    url='http://www.baidu.com'
    getData(url)
    par={
        "apiver":'v3',
        "callback":'bd__cbs__oug2fy',
        "class":'login',
        "logintype":'dialogLogin',
        "tpl":'tb',
        "tt":'13911909661'
    }
    url='https://passport.baidu.com/v2/api/?getapi&%s' % urllib.parse.urlencode(par)
    token=re.findall('"token" : "(.*?)"',getData(url))[0]
    par.update({"isphone":'false',"username":name,"token":token})
    url='https://passport.baidu.com/v2/api/?logincheck&?%s' % urllib.parse.urlencode(par)
    data={
        "charset":'GBK',
        "mem_pass":'on',
        "password":pwd,
        "ppui_logintime":'1612376',
        "quick_user":'0',
        "safeflg":'0',
        "splogin":'rate',
        "u":'http://tieba.baidu.com/'
    }
    url='https://passport.baidu.com/v2/api/?login'
    par.update(data)
    postData(url,par)
    print(json.loads(getData('http://tieba.baidu.com/f/user/json_userinfo')))
    print(getData("http://www.baidu.com"))
"""------输入帐号密码------"""

if __name__ == "__main__":
    mylogin()

