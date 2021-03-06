# coding=utf-8

"""
获得如下应用的配置文件路径，结果输出类似于下面:

{
    'nginx': {'dir':'','file':'','depth':0},
    'zabbix': {'dir':'','file':'','depth':0},
    'varnish': {'dir':'','file':'','depth':0},
    'sysctl': {'dir':'','file':'','depth':0},
    'rsyslog': {'dir':'','file':'','depth':0},
    'dns': {'dir':'','file':'','depth':0},
    'openresty': {'dir':'','file':'','depth':0},
    'sudo': {'dir':'','file':'','depth':0},
    'tomcat':{'param':[{'file': '', 'port': '8089', 'dir': ['/opt/app/apache-tomcat-8089/conf/', '/opt/app/apache-tomcat-8089/bin/'], 'app_name': 'nxstatus'}],'depth':0}

}

此脚本主要是用来获得nginx/openresty tomcat varnish(暂不考虑
"""
import os
import sys
import commands
import socket
from datetime import datetime, timedelta

configname = '/opt/app/appPorts.properties'
myip = sys.argv[1]


def get_ip():
    myname = socket.gethostname()
    myhostip = socket.gethostbyname_ex(myname)
    st = myhostip[2]
    if st:
        for ip in st:
            if ip == "127.0.0.1" or ip.startswith("172") or ip.startswith("192"):
                continue
        else:
            return ip


class GetConfPath():

    d = {
        'sudo': {'dir':'/etc/sudoers.d', 'file': '/etc/sudoers', 'depth':0},
        'dns': {'dir':'', 'file': '/etc/resolv.conf', 'depth':0},
        'sysctl': {'dir':'/etc/sysctl.d', 'file':'/etc/sysctl.conf', 'depth':0},
        'rsyslog': {'file': '/etc/rsyslog.conf', 'dir': '/etc/rsyslog.d/', 'depth':0},
        'zabbix': {'file': '', 'dir': '/etc/zabbix', 'depth':0},
        'nginx': {'dir':'', 'file':'','depth':1},
        'openresty': {'dir':'', 'file':'','depth':1},
        'tomcat': {'param':[],'depth':0},
        'varnish': {'dir':'/etc/varnish', 'file':'','depth':0},
	'msg': 0
    }

    dir_list = ['sudo', 'dns', 'nginx', 'openresty', 'rsyslog', 'sysctl', 'tomcat', 'zabbix', 'varnish']
    basedir = ""
    OldTime = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    DateTime = datetime.now().strftime("%Y-%m-%d")

    # _, LocalIP = commands.getstatusoutput("/usr/sbin/ip addr | grep 'inet' | grep -v 'inet6' | awk '{print $2}' | grep -v '127.0.0.1' | awk -F '/' '{print $1}' | head -n 1")

    def __init__(self, configname):
        self.configname = configname
	if myip:
            self.LocalIP = myip
        else:
            self.LocalIP = get_ip()


    def get_conf_path(self):
        nginx_dict = {'file':'', 'depth':1}
        tomcat_list = []
        if os.path.exists(self.configname):
            with open(self.configname) as f:
                fs = f.readlines()
            for line in fs:
                tomcat_dict = {}
                line = line.strip()
                if line:
                    if line.startswith('#') or "stop" in line or "start" in line or "mongo" in line or "redis" in line:
                        continue
                    if "nginxstatus" in line or "nxstatus" in line:
                        cmd = "ps aux|grep nginx|grep master|grep -v grep"
                        status, strs = commands.getstatusoutput(cmd)
                        if status == 0:
                            nginxpidcmd = "ps aux|grep -v grep|grep nginx|grep master|awk '{print $2}'"
                            st, nginx_pid = commands.getstatusoutput(nginxpidcmd)
                            if st == 0:
                                nginx_cmd = "sudo ls -l /proc/%s|grep ^l|grep exe|awk '{print $NF}'" % nginx_pid
                                stat, nginx_path = commands.getstatusoutput(nginx_cmd)
                                if stat == 0:
                                    nginx_sbin_dir = os.path.dirname(nginx_path)
                                    nginx_dir = os.path.dirname(nginx_sbin_dir)
                                    nginx_dir_conf = nginx_dir + '/conf/'
                                    if os.path.isdir(nginx_dir_conf):
                                        nginx_dict['dir'] = nginx_dir_conf
                                        if "openresty" in nginx_path:
                                            self.d['openresty'] = nginx_dict
                                        else:
                                            self.d['nginx'] = nginx_dict
                    else:
                        app_name, port = line.split("=")
                        tomcat_name = "apache-tomcat-%s" % port
                        cmd = "ps aux | grep %s" % tomcat_name
                        status, _ = commands.getstatusoutput(cmd)
                        if status == 0:
                            tomcat_dict['port'] = port
                            tomcat_dict['app_name'] = app_name
                            tomcat_dir = "/opt/app/server/%s/conf/" % tomcat_name
                            tomcat_bin = "/opt/app/server/%s/bin/" % tomcat_name
                            tomcat_dict['dir'] = [tomcat_dir, tomcat_bin]
                            tomcat_dict['file'] = ''
                            tomcat_list.append(tomcat_dict)
        self.d['tomcat']['param'] = tomcat_list

    def _create_dir(self):
        # self._get_ip()
	if self.LocalIP:
            # 创建之前先清理日期目录
            ipdir = "/home/blsa/%s" % self.LocalIP
            if os.path.exists(ipdir):
                remove_cmd = "rm -rf %s" % ipdir
                os.system(remove_cmd)

	    self.basedir = "/home/blsa/%s/%s" % (self.LocalIP, self.DateTime)
	    create_basedir = "mkdir -p %s" % self.basedir
	    stu, _ = commands.getstatusoutput(create_basedir)
	    if stu == 0:
	        for d in self.dir_list:
	            dir = os.path.join(self.basedir, d)
                    create_dir_cmd = "mkdir -p %s" % dir
	            s, _ = commands.getstatusoutput(create_dir_cmd)
	        return 0
	    else:
	        # print "主目录%s创建失败，请查检相应的用户的权限是否正确" % self.basedir
		return 1
	else:
	    # print "获得IP地址失败,请检查ifconfig命令或ip命令是否存在，或者命令后面的过滤规则有误"
	    return 1

    def _cp_file(self):
	for k in self.dir_list:
	    if k == "tomcat":
	        tomcat_list = self.d[k]['param']
	        if tomcat_list:
	            for t in tomcat_list:
	                tomcat_appname = t['app_name']
	                tomcat_port = t['port']
	                tomcat_dir_list = t['dir']
	                tomcat_file = t['file']
	                bak_tomcat= os.path.join(self.basedir, k)
	                appname_dir = tomcat_appname + '_' + tomcat_port
	                bak_appdir = os.path.join(bak_tomcat, appname_dir)
	                # cmd = "mkdir -p %s" % bak_appdir
                        cmd = "mkdir -p %s/bin %s/conf" % (bak_appdir, bak_appdir)
	                st, _ = commands.getstatusoutput(cmd)
	                if st == 0:
	                    for dd in tomcat_dir_list:
	                        if os.path.exists(dd):
                                    for ff in os.listdir(dd):
                                        if os.path.isfile(os.path.join(dd, ff)):
                                            if "bin" in dd:
	                                        cp_cmd = "sudo cp %s %s/bin" % (os.path.join(dd, ff), bak_appdir)
                                            elif "conf" in dd:
	                                        cp_cmd = "sudo cp %s %s/conf" % (os.path.join(dd, ff), bak_appdir)
	                                    os.system(cp_cmd)
	                if tomcat_file:
	                    if os.path.exists(tomcat_file):
	                        cp_cmd = "sudo cp %s %s" % (tomcat_file, bak_appdir)
	                        os.system(cp_cmd)
            elif k == "sysctl":
                temp_d = self.d[k]
                temp_dir = temp_d['dir']
                temp_file = temp_d['file']
                b_dir = os.path.join(self.basedir, k)
                if temp_dir:
                    if os.path.exists(temp_dir):
                        t_cmd = "sudo cp -r %s %s" % (temp_dir, b_dir)
                        os.system(t_cmd)
                if temp_file:
                    if os.path.exists(temp_file):
                        t_cmd = "sudo cp %s %s" % (temp_file, b_dir)
                        os.system(t_cmd)
                        if os.path.exists('/sbin/sysctl'):
                            tt_cmd = "/sbin/sysctl -a | sort > %s/sysctl_all.conf" % b_dir
                        elif os.path.exists("/usr/sbin/sysctl"):
                            tt_cmd = "/usr/sbin/sysctl -a | sort> %s/sysctl_all.conf" % b_dir
                        else:
                            tt_cmd = "`which sysctl` -a | sort > %s/sysctl_all.conf" % b_dir
                        os.system(tt_cmd)
            elif k == "varnish":
                temp_d = self.d[k]
                temp_dir = temp_d['dir']
                temp_file = temp_d['file']
                b_dir = os.path.join(self.basedir, k)
                if temp_dir:
                    if os.path.exists(temp_dir):
                        t_cmd = "sudo cp -r %s/* %s" % (temp_dir, b_dir)
                        os.system(t_cmd)
                if temp_file:
                    if os.path.exists(temp_file):
                        t_cmd = "sudo cp %s %s" % (temp_file, b_dir)
                        os.system(t_cmd)
	    else:
	        n_dict = self.d[k]
	        n_dir = n_dict['dir']
	        n_file = n_dict['file']
	        bak_dir = os.path.join(self.basedir, k)
	        if n_dir:
	            if os.path.exists(n_dir):
                        cp_cmd = "sudo cp -r %s %s" % (n_dir, bak_dir)
	                os.system(cp_cmd)
	        if n_file:
	            if os.path.exists(n_file):
	                cp_cmd = "sudo cp %s %s" % (n_file, bak_dir)
			os.system(cp_cmd)

    def create_tar(self):
	number = self._create_dir()
	if number == 0:
	    self._cp_file()
        chown_cmd = "sudo chown blsa.blsa %s -R" % self.basedir
        os.system(chown_cmd)
	tar_name = "%s_%s.tar.gz" % (self.LocalIP, self.DateTime)
	tar_gzip_cmd = "tar -zcf %s %s" % (tar_name, self.LocalIP)
	st, _ = commands.getstatusoutput(tar_gzip_cmd)
        if st == 0:
	    clear_dir = "rm -rf %s" % self.LocalIP
	    oldtar_file = "%s_%s.tar.gz" % (self.LocalIP, self.OldTime)
	    clear_oldtar_cmd = "rm -f %s" % oldtar_file
            if os.path.exists(os.path.join("/home/blsa", self.LocalIP)):
		os.system(clear_dir)
	    if os.path.exists(os.path.join("/home/blsa", oldtar_file)):
		os.system(clear_oldtar_cmd)
            self.d["msg"] = 1
	else:
            self.d["msg"] = 0

if __name__ == "__main__":
	get_path = GetConfPath(configname)
	get_path.get_conf_path()
	get_path.create_tar()
	print get_path.d
