#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#抓取应用节点信息以及节点信赖
#输出为json {'status':1 ,'tomcat':tomcat, 'netty':netty}
# status=1 成功  status=0失败

import os,subprocess,re

class AppNode(object):

    def __init__(self):
        self.file_path = '/opt/app/appPorts.properties'
        self.str_rule = re.compile(' +')
        self.port = re.compile(':+')

    def readfile(self):
        if os.path.isfile(self.file_path):
            f = open(self.file_path, 'r')
            file_list = f.readlines()
            if file_list:
                netty_dict = {}
                tomcat_dict = {}
                for i in file_list:
                    one_line = i.strip()
                    if one_line not in ['mongodb', 'nxstatus=', 'nginxstatus=', '#', 'redis-server=', 'mysqld=']:
                        if '-start=' in one_line:
                            appname = one_line.split('-start=')
                            if not netty_dict.has_key(appname[0]):
                                netty_dict[appname[0]] = {}
                            netty_dict[appname[0]]['start'] = appname[1]
                        elif '-stop=' in one_line:
                            appname = one_line.split('-stop=')
                            if not netty_dict.has_key(appname[0]):
                                netty_dict[appname[0]] = {}
                            netty_dict[appname[0]]['stop'] = appname[1]
                        else:
                            appname = one_line.split('=')
                            if not tomcat_dict.has_key(appname[0]):
                                tomcat_dict[appname[0]] = {'stop':0}
                            tomcat_dict[appname[0]]['start'] = appname[1]
                process_info = self.readprocess('ps -ef |grep java|grep -v grep')
                for i in process_info:
                    process = re.split(self.str_rule, i)
                    pid = int(process[1])
                    parameter = ''
                    if 'spring.profiles.active' in i:
                        for sp in process:
                            if 'spring.profiles.active' in sp:
                                parameter = sp.split('=')[1]
                        app_type = 'spring'
                    elif 'apache-tomcat-' in i:
                        app_type = 'tomcat'
                    else:
                        app_type = 'netty'
                    if 'apache-tomcat' in i or 'server.port' in i:
                        for tomcat in tomcat_dict:
                            port = tomcat_dict[tomcat]['start']
                            if '/apache-tomcat-%s/' % port in i or ' --server.port=%s' % port in i:
                                tomcat_dict[tomcat]['pid'] = pid
                                tomcat_dict[tomcat]['app_type'] = app_type
                                tomcat_dict[tomcat]['spring_name'] = parameter
                                tomcat_dict[tomcat]['connection_number'] = []
                    else:
                        for netty in netty_dict:
                            if netty in i and netty_dict[netty]['start'] in i:
                                netty_dict[netty]['pid'] = pid
                                netty_dict[netty]['app_type'] = app_type
                                netty_dict[netty]['spring_name'] = parameter
                                netty_dict[netty]['connection_number'] = []
                if netty_dict or tomcat_dict:
                    self.apprely(netty_dict, tomcat_dict)
            else:
                print {'status': 0, 'msg': 'No Data'}
        else:
            print {'status':0, 'msg':'No Data'}

    def apprely(self, netty, tomcat):
        for n in netty:
            if netty[n].has_key('pid') and netty[n]['pid']:
                connection_number = self.readprocess("sudo netstat -apn |grep %s|grep tcp|grep -vE '127.0.0.1|10.201.32.88|10.201.241.1'|grep ESTABLISHED|awk '{print $5}'|uniq" % netty[n]['pid'])
                if connection_number:
                    for i in connection_number:
                        ip_port = re.split(self.port, i)
                        netty[n]['connection_number'].append([ip_port[-2],ip_port[-1]])
        for t in tomcat:
            if tomcat[t].has_key('pid') and tomcat[t]['pid']:
                connection_number = self.readprocess("sudo netstat -apn |grep %s|grep tcp|grep -vE '127.0.0.1|10.201.32.88|10.201.241.1'|grep ESTABLISHED|awk '{print $5}'|uniq" % tomcat[t]['pid'])
                if connection_number:
                    for i in connection_number:
                        ip_port = re.split(self.port, i)
                        tomcat[t]['connection_number'].append([ip_port[-2],ip_port[-1]])
        print {'status':1 ,'tomcat':tomcat, 'netty':netty}

    def readprocess(self, command):
        '''抓取进程'''
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        process_info = out.splitlines()
        return process_info

if __name__ == '__main__':
    read_app = AppNode()
    read_app.readfile()