#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: Zhoulishan
# email : zhou_mfk@163.com
# date  : 17/06/16 15:10:35

import pexpect
import paramiko
import os
import sys
import datetime

DataTime = datetime.datetime.now()
d = datetime.datetime.strftime(DataTime, '%Y%m%d-%H%M')
hosts = ['10.200.32.66:cmdb:cmdb@bl.com']
dirs = '/opt/net_config'
logfile = '/opt/net_config/net.log'

def getnetdata():
    for i in hosts:
        st = i.split(':')
        hostname = st[0]
        username = st[1]
        password = st[2]
        netfile = st[0] + '-' + d
        netpath= os.path.join(dirs, netfile)
        command = "show configuration | display set"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(hostname=hostname, port=22, username=username,password=password,timeout=6)
            stdin, stdout, stderr = ssh.exec_command(command=command)
            with open(netpath, 'w') as f:
                f.write(stdout.read())
            with open(logfile, 'w') as fs:
                log = '''{0}: status : [OK] SSH CONN IP: {1}\n{0}: COMMAND: {2} [OK]\n'''.format(DataTime, hostname, command)
                fs.write(log)
            ssh.close()
        except Exception, e:
            log = '''{0}: status: [ERROR] SSH CONN IP: {1}\n{0}: COMMAND: {2} [ERROR]\n'''.format(DataTime, hostname, command)
            with open(logfile, 'w') as fs:
                fs.write(log)
            ssh.close()

if __name__ == '__main__':
    getnetdata()
    print
