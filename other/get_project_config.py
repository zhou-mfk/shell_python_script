#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: Zhoulishan
# email : zhou_mfk@163.com
# date  : 17/06/08 09:28:56

import os
import xmltodict
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


BASEDIR = '/jenkinsHome/jenkinsHome/jobs'


class GetProjectConfig(object):
    def __init__(self, projectname, env):
        self.projectname = projectname
        if env in ['prd', 'pre', 'sit', 'dev', 'func']:
            self.env = env
        else:
            print '环境找不到'
            sys.exit(0)

    def __GetAllPath(self):
        pathlist = []
        if os.path.exists(BASEDIR):
            if os.path.isdir(BASEDIR):
                for p in os.listdir(BASEDIR):
                    path = os.path.join(BASEDIR, p)
                    pathlist.append(path)
        return pathlist

    def __GetPomFileToDict(self, projecpath):
        xmlfile = ''
        dp = {}
        if os.listdir(projecpath):
            if 'pom.xml' in os.listdir(projecpath):
                xmlfile = os.path.join(projecpath, 'pom.xml')
            elif 'workspace' in os.listdir(projecpath):
                xmlfile = os.path.join(projecpath, 'workspace/pom.xml')
        if xmlfile:
            if os.path.exists(xmlfile):
                with open(xmlfile) as f:
                    fs = f.read()
                d = xmltodict.parse(fs, xml_attribs=True)
                if d:
                    dp = d['project']
        return dp

    def __GetJarConfFile(self, projecpath, dp):
        tempdict = {}
        if 'profiles' in dp.keys():
            en = dp['profiles']['profile']
            for i in en:
                if 'id' in i.keys():
                    if 'build' in i.keys():
                        src = i['build']['filters']['filter']
                        w = os.path.join(projecpath, 'workspace')
                        if isinstance(src, list):
                            templist = []
                            for j in src:
                                temppath = os.path.join(w, j)
                                templist.append(temppath)
                            tempdict[i['id']] = templist
                        else:
                            propath = os.path.join(w, src)
                            tempdict[i['id']] = propath
                    elif 'properties' in i.keys():
                        envstr = i['properties']['profiles.activation']
                        for st in os.walk(projecpath):
                            if envstr in st[0] and \
                                    'resources' in st[0] and \
                                    '.svn' not in st[0]:
                                templist = []
                                for l in os.listdir(st[0]):
                                    if '.svn' in l:
                                        continue
                                    else:
                                        templist.append(os.path.join(st[0], l))
                                tempdict[i['id']] = templist
        return tempdict

    def __FindWarConfigPath(self, strs, projecpath):
        templist = []
        for st in os.walk(projecpath):
            if strs in st[0] and \
                    'resources' in st[0] and \
                    '.svn' not in st[0]:
                for l in os.listdir(st[0]):
                    if '.svn' in l:
                        continue
                    else:
                        templist.append(os.path.join(st[0], l))
                return templist

    def __GetWarConfigFile(self, projecpath, dp):
        tempdict = {}
        if 'profiles' in dp.keys():
            en = dp['profiles']['profile']
            if isinstance(en, list):
                for i in en:
                    if 'properties' in i.keys():
                        if isinstance(i['properties'], dict) and \
                                'profiles.activation' in i['properties'].keys():
                            envstr = i['properties']['profiles.activation']
                            templist = self.__FindWarConfigPath(envstr,
                                                                projecpath)
                            if templist:
                                tempdict[i['id']] = templist
                        elif isinstance(i['properties'], dict) and \
                            'datagram.config.path.home' in i['properties'].keys():
                            envstr = i['properties']['datagram.config.path.home']
                            templist = self.__FindWarConfigPath(envstr, projecpath)
                            if templist:
                                tempdict[i['id']] = templist
            if isinstance(en, dict):
                if 'properties' in en.keys():
                    if 'profiles.activation' in en['properties'].keys():
                        envstr = en['properties']['profiles.activation']
                        templist = self.__FindWarConfigPath(envstr,
                                                            projecpath)
                        if templist:
                            tempdict[i['id']] = templist
        return tempdict

    def __GetModuleConfig(self, projecpath, dp):
        if isinstance(dp['modules'], dict):
            mds = dp['modules']['module']
            if isinstance(mds, list):
                for md in mds:
                    if 'workspace' in projecpath:
                        mdpath = os.path.join(projecpath, md)
                    else:
                        md = os.path.join('workspace', md)
                        mdpath = os.path.join(projecpath, md)
                    return self.__GetAllPomXml(mdpath)
            else:
                if 'workspace' in projecpath:
                    mdpath = os.path.join(projecpath, mds)
                else:
                    md = os.path.join('workspace', mds)
                    mdpath = os.path.join(projecpath, md)
                return self.__GetAllPomXml(mdpath)

    def __GetAllPomXml(self, projecpath):
        infodict = {}
        dp = self.__GetPomFileToDict(projecpath)
        if not dp:
            return infodict
        if 'packaging' in dp.keys():
            if 'name' in dp.keys():
                infodict['projectName'] = dp['name']
            else:
                infodict['projectName'] = dp['artifactId']
            if dp['packaging'] == 'jar':
                infodict['packaging'] = 'jar'
                tempdict = self.__GetJarConfFile(projecpath, dp)
                if tempdict:
                    infodict = dict(infodict, **tempdict)
                return infodict
            elif dp['packaging'] == 'war':
                infodict['packaging'] = 'war'
                tempdict = self.__GetWarConfigFile(projecpath, dp)
                if tempdict:
                    infodict = dict(infodict, **tempdict)
                return infodict
            elif dp['packaging'] not in ['jar', 'war'] and \
                    'modules' in dp.keys():
                return self.__GetModuleConfig(projecpath, dp)
        return infodict

    def __GetAllConfigFile(self):
        pathlist = self.__GetAllPath()
        dictlist = []
        if pathlist:
            for i in pathlist:
                infodict = self.__GetAllPomXml(i)
                if infodict:
                    dictlist.append(infodict)
        return dictlist

    def __GetConfigInfo(self):
        dictlist = self.__GetAllConfigFile()
        configfile = ''
        if dictlist:
            for d in dictlist:
                if d:
                    if self.projectname == d['projectName']:
                        if self.env == 'prd':
                            if 'prd' in d.keys():
                                configfile = d['prd']
                            elif 'prod' in d.keys():
                                configfile = d['prod']
                        if self.env == 'pre':
                            if 'pre' in d.keys():
                                configfile = d['pre']
                            elif 'pression' in d.keys():
                                configfile = d['pression']
            if configfile:
                return configfile
            else:
                return None

    def GetOracle(self, strs, fs, prefix=None):
        tempdict = {}
        tempdict['ip'] = strs.split('@')[1].split(':')[0]
        tempdict['port'] = strs.split(':')[4].split('/')[0]
        tempdict['dbname'] = strs.split('/')[1]
        if prefix is None:
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                if mline.startswith('jdbc.username'):
                    tempdict['username'] = mline.split('=')[1]
        else:
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                if mline.split('=')[0] == prefix + '.jdbc.username':
                    tempdict['username'] = mline.split('=')[1]
        return tempdict

    def GetMySQL(self, strs, fs, prefix=None):
        tempdict = {}
        tempdict['ip'] = strs.split('/')[2].split(':')[0]
        tempdict['port'] = strs.split('/')[2].split(':')[1]
        tempdict['dbname'] = strs.split('/')[3].split('?')[0]
        if prefix is None:
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                if mline.startswith('jdbc.username'):
                    tempdict['username'] = mline.split('=')[1]
        else:
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                if mline.split('=')[0] == prefix + '.username.mysql':
                    tempdict['username'] = mline.split('=')[1]
        return tempdict

    def GetRedis(self, strs0, strs1, fs):
        tempdict = {}
        tempdict['ip'] = strs1
        if len(strs0.split('.')) == 2:
            num = strs0[-1]
            if num.isdigit():
                port = 'redis.port' + str(num)
                for mline in fs:
                    mline = mline.strip('\n').strip('\r')
                    if mline.split('=')[0] == port:
                        tempdict['port'] = mline.split('=')[1]
                return tempdict
            else:
                port = 'redis.port'
                for mline in fs:
                    mline = mline.strip('\n').strip('\r')
                    if mline.split('=')[0] == port:
                        tempdict['port'] = mline.split('=')[1]
                return tempdict
        elif len(strs0.split('.')) > 2:
            endfix = '.'.join(strs0.split('.')[2:])
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                if mline.split('=')[0] == 'redis.port.' + endfix:
                    tempdict['port'] = mline.split('=')[1]
            return tempdict

    def GetMongodb(self, strs0, strs1, fs):
        tempdict = {}
        if strs0 == 'mongo.host':
            tempdict['ip'] = strs1
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                st = mline.split('=')
                if st[0] == 'mongo.port':
                    tempdict['port'] = st[1]
                elif st[0] == 'mongo.dbname':
                    tempdict['dbname'] = st[1]
                elif st[0] == 'mongo.credentials':
                    tempdict['username'] = st[1].split(':')[0]
                elif st[0] == 'mongo.replicaset':
                    tempdict['replicaset'] = st[1]
            return tempdict
        elif strs0 == 'mongo.replicaset':
            tempdict['replicaset'] = strs1
            tempdict['port'] = strs1.split(',')[0].split(':')[1]
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                st = mline.split('=')
                if st[0] == 'mongo.credentials':
                    tempdict['username'] = st[1].split(':')[0]
                elif st[0] == 'mongo.dbname':
                    tempdict['dbname'] = st[1]
            return tempdict
        elif strs0 == 'mongo.gateway.replicaset':
            tempdict['replicaset'] = strs1
            tempdict['port'] = strs1.split(',')[0].split(':')[1]
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                st = mline.split('=')
                if st[0] == 'mongo.gateway.credentials':
                    tempdict['username'] = st[1].split(':')[0]
                elif st[0] == 'mongo.gateway.dbname':
                    tempdict['dbname'] = st[1]
            return tempdict

    def GetMQ(self, strs0, strs1, fs):
        tempdict = {}
        if len(strs0.split('.')) > 2:
            tempdict['queue'] = strs1
            pre = '.'.join(strs0.split('.')[-2:])
            h = pre + '.mq.host'
            p = pre + '.mq.port'
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                st = mline.split('=')
                if st[0] == h:
                    tempdict['ip'] = st[1]
                elif st[0] == p:
                    tempdict['port'] = st[1]
            return tempdict
        elif len(strs0.split('.')) == 2:
            tempdict['queue'] = strs1
            for mline in fs:
                mline = mline.strip('\n').strip('\r')
                st = mline.split('=')
                if st[0] == 'mq.host':
                    tempdict['ip'] = st[1]
                elif st[0] == 'mq.port':
                    tempdict['port'] == st[1]
            return tempdict

    def GetAppNode(self, strs):
        tempdict = {}
        st = strs.split('/')
        nums = len(st)
        if ':' in st[2]:
            tempdict['ip'] = st[2].split(':')[0]
            tempdict['port'] = st[2].split(':')[1]
        else:
            tempdict['ip'] = st[2]
            tempdict['port'] = 80
        if nums == 3:
            tempdict['location'] = ''
        elif nums > 3:
            tempdict['location'] = '/' + '/'.join(st[3:])
        return tempdict

    def GetFtp(self, strs, fs):
        tempdict = {}
        tempdict['ip'] = strs
        for mline in fs:
            mline = mline.strip('\n').strip('\r')
            st = mline.split('=')
            if st[0] == 'ftp.port':
                tempdict['port'] = st[1]
            elif st[0] == 'ftp.username':
                tempdict['username'] = st[1]
        return tempdict

    def GetData(self):
        oraclelist = []
        mysqllist = []
        redislist = []
        mongodblist = []
        appnodelist = []
        mqlist = []
        ftplist = []

        configfile = self.__GetConfigInfo()
        if configfile is None:
            msgerror = '%s 没有找到工程路径,请检查工程名是否正确' % self.projectname
            fd = {'msg': 0, 'error': msgerror}
            return fd
        else:
            fs = []
            if isinstance(configfile, list):
                for s in configfile:
                    if os.path.exists(s):
                        with open(s) as f:
                            fs = fs + f.readlines()
            else:
                if os.path.exists(configfile):
                    with open(configfile) as f:
                        fs = f.readlines()
            if not fs:
                msgerror = '%s 工程的配置文件为空' % self.projectname
                fd = {'msg': 0, 'error': msgerror}
                return fd
                # sys.exit(3)
            else:
                for line in fs:
                    line = line.strip('\n').strip('\r')
                    if line:
                        strs = line.split("=")
                        if line.startswith('#') or not line.split():
                            continue
                        elif strs[0] == 'jdbc.url':
                            if 'oracle' in strs[1]:
                                tempdict = self.GetOracle(strs[1], fs)
                                if tempdict:
                                    oraclelist.append(tempdict)
                            elif 'mysql' in strs[1]:
                                tempdict = self.GetMySQL(strs[1], fs)
                                if tempdict:
                                    mysqllist.append(tempdict)
                        elif 'jdbc.url' in strs[0] and strs[0] != 'jdbc.url':
                            if 'oracle' in strs[1]:
                                prefix = '.'.join(strs[0].split('.')[:-2])
                                tempdict = self.GetOracle(strs[1], fs, prefix)
                                if tempdict:
                                    oraclelist.append(tempdict)
                            elif 'mysql' in strs[1]:
                                prefix = '.'.join(strs[0].split('.')[:-2])
                                tempdict = self.GetMySQL(strs[1], fs, prefix)
                                if tempdict:
                                    mysqllist.append(tempdict)
                        elif 'redis.host' in strs[0]:
                            tempdict = self.GetRedis(strs[0], strs[1], fs)
                            if tempdict:
                                redislist.append(tempdict)
                        elif 'mongo' in strs[0]:
                            tempdict = self.GetMongodb(strs[0], strs[1], fs)
                            if tempdict:
                                mongodblist.append(tempdict)
                        elif 'mq.queue' in strs[0]:
                            tempdict = self.GetMQ(strs[0], strs[1], fs)
                            if tempdict:
                                mqlist.append(tempdict)
                        elif strs[1].startswith('http'):
                            tempdict = self.GetAppNode(strs[1])
                            if tempdict:
                                appnodelist.append(tempdict)
                        elif strs[0] == 'ftp.url':
                            tempdict = self.GetFtp(strs[1], fs)
                            if tempdict:
                                ftplist.append(tempdict)
                fd = {
                    'mysql': {'param': mysqllist},
                    'oracle': {'param': oraclelist},
                    'mongodb': {'param': mongodblist},
                    'redis': {'param': redislist},
                    'appnode': {'param': appnodelist},
                    'mq': {'param': mqlist},
                    'ftp': {'param': ftplist},
                    'msg': 1,
                    'error': None
                }
                return fd


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print '需要给工程名和环境参数'
        sys.exit(2)
    else:
        p = GetProjectConfig(sys.argv[1], sys.argv[2])
        fd = p.GetData()
        print fd
