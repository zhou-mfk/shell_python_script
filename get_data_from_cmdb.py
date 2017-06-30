# coding=utf-8
import urllib2
import json
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


def get_token():
    url = 'https://cmdbapi.bl.com/auth/token/'
    header = {"Content-Type": "application/json"}
    post_data = json.dumps({
        "client_id":"voM6BNtHD39qTamUusxLZ4khzJfcenlFIgER18Vj",
        "client_secret":"254MavTy61Yd7LD2P8KbEaC4BGh51X282ej07dcxf24aq7Fe8f79quIaZfMftA34G82jfm522a1dcWI7bze4X8hf647YcAUet7d07aR8Tc81DrQ4p7iwc679m30v9b3c",
        "grant_type":"password",
        "username":"lishan.zhou@bl.com",
        "password":"1k9m5vspdDwj"
    })
    req = urllib2.Request(url, post_data)
    for key in header:
        req.add_header(key, header[key])

    try:
        res = urllib2.urlopen(req)
    except urllib2.URLError as e:
        if hasattr(e, "code"):
            print e.code
        elif hasattr(e, 'reason'):
            print e.reason
        return 0
    else:
        response = json.loads(res.read())
        access_token = response['access_token']
        return access_token


def get_host_info(env):
    url = 'https://cmdbapi.bl.com/servers/serverlist/'
    token = get_token()
    templist = []
    if token:
        header = {"Authorization": token}
        req = urllib2.Request(url)
        for key in header:
            req.add_header(key, header[key])
        try:
            res = urllib2.urlopen(req)
        except urllib2.URLError as e:
            if hasattr(e, "code"):
                print e.code
            elif hasattr(e, "reason"):
                print e.reason
            return 0
        else:
            response = json.loads(res.read())
            serverlist = response['ServerList']['param']
            for i in serverlist:
                if i['environment'] == env:
                    templist.append(i)
            return templist


# print get_host_info(u'生产环境')