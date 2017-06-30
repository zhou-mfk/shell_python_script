# coding=utf-8

import json
import urllib2
from get_data_from_cmdb import get_host_info

class ZabbixTools:
    def __init__(self):
        self.url = "http://10.201.33.103/api_jsonrpc.php"
        self.header = {"Content-Type": "application/json"}
        self.authID = self.user_login()
        self.enf = u'运维区'

    def user_login(self):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": "zhoulishan",
                    "password": "zhoulishan332"
                },
                "id": 1
            }
        )

        request = urllib2.Request(self.url, data)
        for key in self.header:
            request.add_header(key, self.header[key])
        try:
            result = urllib2.urlopen(request)
        except urllib2.URLError as e:
            print 'Auth Failed, Please Check Your Name And Password:', e.reason
        else:
            response = json.loads(result.read())
            result.close()
            authID = response['result']
            return authID

    def get_data(self, data):
        request = urllib2.Request(self.url, data)
        for key in self.header:
            request.add_header(key, self.header[key])
        try:
            result = urllib2.urlopen(request)
        except urllib2.URLError as e:
            if hasattr(e, 'reason'):
                print 'We Failed to reach a server'
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server could not fulfill the request.'
                print 'Error code: ', e.code
            return 0
        else:
            response = json.loads(result.read())
            result.close()
            return response

    def get_host_group_id(self, hostip):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                    "output": ["hostid", "name", "host"],
                    "selectGroups": ["groupid"],
                    "filter": {"host": [hostip]}
                },
                "auth": self.authID,
                "id": 1
            }
        )
        res = self.get_data(data)['result']
        tempdict = {}
        if res != 0 and len(res) != 0:
            for i in res:
                tempdict['hostid'] = i['hostid']
                tempdict['host'] = i['host']
                tempdict['name'] = i['name']
                glist = [g['groupid'] for g in i['groups']]
                tempdict['groupids'] = glist
        return tempdict

    def get_groupid(self, groupname):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": {
                    "output": ["groupid", "name"],
                    "filter": {"name": [groupname]}
                },
                "id": 1,
                "auth": self.authID
            }
        )
        res = self.get_data(data)['result']
        if res != 0 and len(res) != 0:
            for i in res:
                if i['name'] == groupname:
                    return i['groupid']

    def get_hostid(self, hostip):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                    "output": ["hostid", "name", "host"],
                    "selectGroups": ["groupid"],
                    "filter": {"host": [hostip]}
                },
                "auth": self.authID,
                "id": 1
            }
        )
        res = self.get_data(data)['result']
        if res != 0 and len(res) != 0:
            for h in res:
                if h['host'] == hostip:
                    return h['hostid']

    def group_create(self, groupname):
        print 'group name is : %s |||' % groupname
        groupname = groupname.strip('\n')
        if groupname:
            groupid = self.get_groupid(groupname)
            if groupid:
               print '主机组已存在'
               return groupid
            else:
               data = json.dumps(
                   {
                       "jsonrpc": "2.0",
                       "method": "hostgroup.create",
                       "params": {
                           "name": groupname
                       },
                       "auth": self.authID,
                       "id": 1
                   }
               )
               ref = self.get_data(data)
               if isinstance(ref, dict):
                   print ref
                   res = ref['result']
                   if res != 0 and len(res) != 0:
                       return res['groupids'][0]
               else:
                   print ref

    def host_update(self, hostip, groupnamelist):
        hostid = self.get_hostid(hostip)
        if not hostid:
            print u'主机: %s 在zabbix server中没有找到。请检查zabbix服务器中是否有此主机' % hostip
            return {hostip: 'nohost'}
        else:
            groupidlist = []
            for name in groupnamelist:
                groupid = self.get_groupid(name)
                if groupid:
                    groupidlist.append(groupid)
                else:
                    groupid = self.group_create(name)
                    if groupid:
                        groupidlist.append(groupid)
            if groupidlist:
                groups = [{'groupid': x} for x in groupidlist]
                data = json.dumps({
                    "jsonrpc": "2.0",
                    "method": "host.update",
                    "params": {
                        "hostid": hostid,
                        "groups": groups
                    },
                    "auth": self.authID,
                    "id": 1
                })

                res = self.get_data(data)['result']
                if res != 0 and len(res) != 0:
                    if len(res['hostids']) == 1 and res['hostids'][0] == hostid:
                        print u'主机:%s已修改主机组:%s' % (hostip, ','.join(groupnamelist))
                        return {hostip: "update"}
                    else:
                        print u"修改可能未成功: %s" % res
                        return {hostip: "error"}
            else:
                return {hostip: 'grouperr'}

    def get_cmdb_data(self):
        cmdb_data = get_host_info(self.enf)
        if cmdb_data:
            return cmdb_data

    def get_all_group(self):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "oupput": ["groupid", "name"]
            },
            "id": 1,
            "auth": self.authID
        })
        res = self.get_data(data)['result']
        if res != 0 and len(res) != 0:
            grouplist = [x['groupid'] for x in res]
            return grouplist


if __name__ == '__main__':
    # pass
    # a = ZabbixTools()
    # a.get_all_group()
    # a.del_group(groupname=u'DB_Oracle')
    a = ZabbixTools()
    # res = a.host_update(u'zls-183', ['GSP', 'GEK'])
    # print res
    # print a.get_hostid(u'zls-183')

    cmdb_data = a.get_cmdb_data()
    for t in cmdb_data:
        if len(t.keys()) == 4:
            host_ip = t['host_ip']
            hostname = t['hostname']
            server_group = t['server_group']
            if server_group:
                groupnamelist = server_group.strip().split()
                if groupnamelist:
                    print groupnamelist
                    res = a.host_update(hostname, groupnamelist)
                    if res:
                         if res[hostname] == 'update':
                             with open(u'a.log', 'a') as f:
                                 f.write('host:%s add to hostgroup: %s \n' % (host_ip, ','.join(groupnamelist)))
                         elif res[hostname] == 'ok':
                             with open(u'a.log', 'a') as f:
                                 f.write('host:%s hostgroup no change \n' % host_ip)
                         elif res[hostname] == 'error':
                             with open(u'a.log', 'a') as f:
                                 f.write('host:%s hostgroup update failed \n' % host_ip)
                         elif res[hostname] == 'nohost':
                             with open(u'a.log', 'a') as f:
                                 f.write('host:%s No found from Zabbix Server \n' % host_ip)
                         elif res[hostname] == 'grouperr':
                             with open(u'a.log', 'a') as f:
                                 f.write('group:%s create Failed' % ','.join(groupnamelist))
            else:
                print u'%s group name 空'
