import hashlib
import time
import pandas as pd
import requests
import re
import speedtest

tpLink = '192.168.0.1'
userName = 'admin'
pcPassword = '123456c789fgh'
pingTimeOut = 10  # second
DEBUG = True
login_status = False

baseHeaders = {
    'Host': tpLink,
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'close',
    'Referer': 'http://192.168.0.1/userRpm/Index.htm',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
}

ml = pd.read_csv('maclist.csv')


def getMacWanList(cookieStr):
    headers = {
        'Cookie': cookieStr
    }
    headers.update(baseHeaders)
    res = requests.get(
        'http://{}/userRpm/Interface_MACCfg.htm'.format(tpLink), headers=headers)

    wan1Mac = re.search(
        r"\"wan1\",\"(?P<wan1>([0-9]|\-|[A-F])+)\"", res.text).group('wan1')
    wan2Mac = re.search(
        r'wan2","(?P<wan2>([0-9]|-|[A-F])+)"', res.text).group('wan2')
    wan3Mac = re.search(
        r'wan3","(?P<wan3>([0-9]|-|[A-F])+)"', res.text).group('wan3')
    wan4Mac = re.search(
        r'wan4","(?P<wan4>([0-9]|-|[A-F])+)"', res.text).group('wan4')

    return [wan1Mac, wan2Mac, wan3Mac, wan4Mac]


def encodeLoginData(cookie):
    tmp_pwd_md5 = hashlib.md5(pcPassword.encode('utf-8')).hexdigest()
    submitStr_md5 = hashlib.md5(
        (tmp_pwd_md5.upper() + ":" + cookie).encode('utf-8')).hexdigest()

    encoded = userName + ':' + submitStr_md5.upper()

    return {'encoded': encoded, 'nonce': cookie, 'URL': '../logon/loginJump.htm'}


def checkMacsActive(cookieStr, activeWan=4):
    wanIfce = ['wan1', 'wan2', 'wan3', 'wan4']

    resList = []
    timeCheckStart = time.time()
    for i in range(3):
        wanState = pingMac(cookieStr, wanIfce[i])
        resList.append(wanState)
    timeCheckStop = time.time()
    if DEBUG:
        print("Check active Wan total: ", timeCheckStop - timeCheckStart)
    return resList


# use for get ping result
def pingMac(cookieStr, macInterface):
    return pingMacWithTimout(cookieStr, macInterface, pingTimeOut)

# ping mac of wan  with timout


def pingMacWithTimout(cookieStr, macInterface, timeOut):
    headers = {
        'Cookie': cookieStr
    }

    headers.update(baseHeaders)
    requests.get(
        'http://{}/userRpm/DiagnosticPingIframe.htm'.format(tpLink), headers=headers,
        params={
            'btn_ping': 'btn_ping',
            'txt_ping_host': 'fb.com',
            'slct_p_interface': macInterface
        })

    resPing = []
    i = 0

    pingStartTime = time.time()

    while True:

        # sleep 250 ms for each check
        time.sleep(0.25)
        if i == 0:
            resPing = pingKeyMac(cookieStr, 1)
        else:
            resPing = pingKeyMac(cookieStr, 0)
        i += 1

        if(resPing[0]):
            break
        pingEndTime = time.time()
        if pingEndTime - pingStartTime > timeOut:
            break

    pingEndTime = time.time()

    if DEBUG:
        print('Ping '+macInterface+' time ', pingEndTime - pingStartTime)

    if int(resPing[1][0]) == 0 and len(resPing[1]) > 2:
        return True
    else:
        return False


def changeMac(cookieStr, list4Macs):
    headers = {
        'Cookie': cookieStr
    }

    headers.update(baseHeaders)
    requests.get(
        'http://{}/userRpm/Interface_MACCfg.htm'.format(tpLink), headers=headers,
        params={
            'txt_if_0': list4Macs[0],
            'txt_if_1': list4Macs[1],
            'txt_if_2': list4Macs[2],
            'txt_if_3': list4Macs[3],
            'txt_if_4': 'F4-F2-6D-EC-04-4A',
            'txt_if_5': 'F4-F2-6D-EC-04-4F',
            'btn_save': 'Save',
            'btn_clone': ''
        })


def pingKeyMac(cookieStr, key):
    headers = {
        'Cookie': cookieStr
    }

    headers.update(baseHeaders)
    res = requests.get(
        'http://{}/userRpm/DiagnosticPingIframe.htm'.format(tpLink), headers=headers,
        params={
            key: key
        })
    resultArray = re.search(
        r'var\spingResult\s=\snew\sArray\(\n(?P<arrayR>(\d+|,|"|\.|\n)+)\s\)', res.text).group('arrayR') \
        .replace("\"", "").replace("\n", "").split(",")
    infoArray = re.search(
        r'var\spingInfo\s=\snew\sArray\((?P<arrayIn>(\d|,|"|\.|\w)+)', res.text.replace("\n", "")).group('arrayIn') \
        .replace("\"", "").split(",")

    total_count = int(infoArray[8])
    current_count = int(infoArray[9])

    if(total_count == current_count):
        return [True, resultArray]
    else:
        return [False, resultArray]


def login(data, cookieStr):

    headers = {
        'Cookie': cookieStr,
        'Cache-Control': 'max-age=0',
        'Content-Length': '102',
        'Origin': 'http://192.168.0.1',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    headers.update(baseHeaders)

    postReults = requests.post(
        'http://{}/logon/loginJump.htm'.format(tpLink), data=data, headers=headers)

    if 'location.href= "/userRpm/Index.htm";' in postReults.text:
        return 'login success'
    return 'login fail'


def logout(cookieStr):
    headers = {
        'Cookie': cookieStr,

    }
    headers.update(baseHeaders)

    res = requests.get(
        'http://{}/logon/logout.htm'.format(tpLink), headers=headers)


def speedTest():
    st = speedtest.Speedtest()
    print('INTERNET SPEED')
    print(' Download: {} MB/s'.format(round(st.download()*1.25*10**(-7), 2)))
    print(' Upload: {} MB/s'.format(round(st.upload()*1.25*10**(-7), 2)))
    print(' Ping: {} ms'.format(st.results.ping))


if __name__ == '__main__':

    cookie = requests.get('http://{}/'.format(tpLink)).cookies.get('COOKIE')

    cookieStr = 'COOKIE={}'.format(cookie)

    dataAuth = encodeLoginData(cookie)

    print(login(dataAuth, cookieStr))

    macArray = ml['MAC'].to_numpy()
    macStates = checkMacsActive(cookieStr, 3)
    macWans = getMacWanList(cookieStr)
    currCheckMac = 0

    print('current wan state', macStates)

    # change auto

    for i in range(len(macStates)):
        if(macStates[i]):
            continue
        while currCheckMac < macArray.size:
            # prevent that have same mac in update list
            if macArray[currCheckMac] in macWans:
                currCheckMac += 1
                continue
            # scan in list and change mac
            macWans[i] = macArray[currCheckMac]

            print('Try apply mac {} to wan{}'.format(macWans[i], i+1))
            # change mac
            changeMac(cookieStr, macWans)
            currCheckMac += 1
            # check status of new mac
            time.sleep(10)
            nState = pingMacWithTimout(cookieStr, 'wan{}'.format(i+1), 5)
            if(nState):
                print('Applied new mac {} to wan{}'.format(macWans[i], i+1))
                break
        if(currCheckMac >= macArray.size):
            print("Sorry mac array reach limit before done task ,at wan{}".format(i+1))

    logout(cookieStr)
    print("Job done logout !")
    # speed test internet
    speedTest()
