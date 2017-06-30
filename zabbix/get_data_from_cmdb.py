# coding=utf-8
import urllib2
import json
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


def get_token():
    url = 'https://xxxxx/auth/token/'
    header = {"Content-Type": "application/json"}
    post_data = json.dumps({
        "client_id":"....................",
        "client_secret":"25............c",
        "grant_type":"password",
        "username":"...om",
        "password":"1k...j"
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
    url = 'https://c...../servers/serverlist/'
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
