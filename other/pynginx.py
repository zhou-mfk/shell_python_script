# coding=utf-8

import os
from pynginxconfig import NginxConfig

"""
分析nginx配置目录下的.conf结尾的配置文件
"""
nc = NginxConfig()
#nginxdir = "/root/python_nginx_conf/conf/"
#nginxconf = "/root/python_nginx_conf/conf/nginx.conf"
nginxdir = "/opt/config_file/2017-03-23_1/10.201.96.7/2017-03-23/nginx/conf"
nginxconf = "/opt/config_file/2017-03-23_1/10.201.96.7/2017-03-23/nginx/conf/nginx.conf"
# nginxdir = "/root/python_nginx_conf/new_conf"
# nginxconf = "/root/python_nginx_conf/new_conf/nginx.conf"

read_conf = " "


def get_read(nginxconf):
    global read_conf
    if os.path.exists(nginxconf):
        with open(nginxconf) as fs:
            f = fs.readlines()
            for line in f:
                if "#" in line or "mime.types" in line or \
                        "proxy_set_header_group" in line:
                    continue
                elif "include" in line and "conf" in line:
                    fp = line.split()[1].strip(';')
                    if fp.endswith("*.conf"):
                        if fp.startswith("/"):
                            if "/conf/" in fp:
                                fp_dir = os.path.join(nginxdir, fp.split("/conf/")[-1].split("*.")[0])
                                if os.path.exists(fp_dir):
                                    for i in os.listdir(fp_dir):
                                        if i.endswith(".conf"):
                                            fp_path = os.path.join(fp_dir, i)
                                            get_read(fp_path)
                        else:
                            fp_dir = os.path.join(nginxdir, fp.split("/")[0])
                            if os.path.exists(fp_dir):
                                for i in os.listdir(fp_dir):
                                    if i.endswith(".conf"):
                                        fp_path = os.path.join(fp_dir, i)
                                        get_read(fp_path)
                    else:
                        if fp.startswith("/"):
                            fp_conf = fp.split("/")[-1]
                            fp_path = os.path.join(nginxdir, fp_conf)
                            get_read(fp_path)
                        else:
                            fp = os.path.join(nginxdir, fp)
                            get_read(fp)
                else:
                    read_conf = read_conf + line
    else:
        read_conf = read_conf


def format_data():
    ss = []
    ul = []
    get_read(nginxconf)
    if read_conf:
        read_conf = read_conf.replace("\t", " ")
        nc.load(read_conf)
        format_start = nc.get_value(nc.get(('http',)))
        for line in format_start:
            sd = {}
            local_list = []
            if isinstance(line, dict):
                if line['name'] == 'server':
                    server_value = line['value']
                    for s in server_value:
                        if 'server_name' in s:
                            sd['server_name'] = s[1]
                        elif 'listen' in s:
                            sd['port'] = s[1]
                        elif "rewrite" in s:
                            sd['rewrite'] = s[1]
                        elif 'location' in str(s):
                            temp_dict = {}
                            temp_pass = s['value']
                            for t in temp_pass:
                                if 'proxy_pass' in t:
                                    temp_dict['name'] = s['param']
                                    temp_dict['proxy_pass'] = t[1]
                                else:
                                    temp_dict['name'] = s['param']
                                    temp_dict['config'] = s['value']
                            if temp_dict:
                                local_list.append(temp_dict)
                    if local_list:
                        sd['location'] = local_list
                    ss.append(sd)
                elif line['name'] == 'upstream':
                    temp_udict = {}
                    temp_udict['name'] = line['param']
                    temp_udict['server'] = line['value']
                    if temp_udict:
                        ul.append(temp_udict)
    return ss, ul

s, u = format_data()
#
print "=======server_name->location->proxy_pass======================"
print s
print "=======upstream->server_list=================================="
print u
# get_read(nginxconf)
# print read_conf

