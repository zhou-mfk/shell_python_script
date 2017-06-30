# -*- coding: utf-8 -*-
#分析nginx配置目录下的.conf结尾的配置文件

from models import Base,LoadNginx,AppNode
from pynginxconfig import NginxConfig
from extends import ip_env
import os


class NginxConf(NginxConfig):
    read_conf = ""

    def __init__(self, nginx_dir, sid, ipaddr,offset_char=' '):
        NginxConfig.__init__(self, offset_char=' ')
        self.nginx_dir = nginx_dir
        self.sid = sid
        self.ipaddr = ipaddr
        nginx_conf = os.path.join(nginx_dir, 'nginx.conf')
        self.format_data(nginx_conf)

    def get_read(self, nginx_conf):
        if os.path.exists(nginx_conf):
            with open(nginx_conf) as fs:
                f = fs.readlines()
                for line in f:
                    if "include" in line and "conf" in line and not '#' in line:
                        fp = line.split()[1].strip(';')
                        if fp.endswith("*.conf"):
                            fp_dir = os.path.join(self.nginx_dir, fp.split("/")[0])
                            if os.path.exists(fp_dir):
                                for i in os.listdir(fp_dir):
                                    if i.endswith(".conf"):
                                        fp_path = os.path.join(fp_dir, i)
                                        self.get_read(fp_path)
                        else:
                            fp = os.path.join(self.nginx_dir, fp)
                            self.get_read(fp)
                    else:
                        self.read_conf = self.read_conf + line

    def format_data(self, nginx_conf):
        ss = []
        ul = []
        self.get_read(nginx_conf)
        if self.read_conf:
            self.load(self.read_conf)
            format_start = self.get_value(self.get(('http',)))
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
                            elif 'rewrite' in s:
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
        if ul:
            self.to_db(ss, ul)

    def to_db(self,ss,ul):
        for i in ss:
            if i['port'] == '8089':
                continue
            else:
                if i['server_name'] in 'localhost':
                    server_name = i['server_name'].replace('localhost',str(self.ipaddr))
                else:
                    server_name = i['server_name']
                if i['location'] and isinstance(i['location'],list):
                    node_id = []
                    for l in i['location']:
                        if l['name']:
                            upstream = str(l['proxy_pass']).split('//')[-1]
                            for ups in ul:
                                if ups['name'] == upstream:
                                    for servers in ups['server']:
                                        if str(servers[-1]).count('.') == 3 and str(servers[-1]).startswith('10'):
                                            if 'weight' in servers[-1]:
                                                server = str(servers[-1]).split()[0]
                                                weight = str(servers[-1]).split()[-1].split('=')[-1]
                                            else:
                                                server = servers[-1]
                                                weight = 1
                                            app_one = Base(AppNode,condition={'db_status':1, 'bus_ip':server[-1].split(':')[0], 'bus_port':int(server[-1].split(':')[-1])}).findone()
                                            load_one = Base(LoadNginx, condition={'db_status':1, 'server_ip': self.ipaddr,'nginx_port': int(i['port']),'server_name': server_name,'url_suffix': l['name'],'upstream': upstream,'agent_node_ip': server[-1].split(':')[0],'agent_node_port': int(server[-1].split(':')[-1]),}).findone()
                                            if app_one:
                                                app_info = app_one.server_name
                                            else:
                                                app_info = ''
                                            if load_one:
                                                load_one.environment = ip_env(self.ipaddr)
                                                load_one.agent_node_info = app_info
                                                Base.update()
                                            else:
                                                load_add = {
                                                    'db_status': 1,
                                                    'environment': ip_env(str(self.ipaddr)),
                                                    'server_ip': self.ipaddr,
                                                    'nginx_port': int(i['port']),
                                                    'server_name': server_name,
                                                    'url_suffix': l['name'],
                                                    'upstream': upstream,
                                                    'status': 1,
                                                    'agent_node_ip': server[-1].split(':')[0],
                                                    'agent_node_port': int(server[-1].split(':')[-1]),
                                                    'agent_node_info':app_info,
                                                    'node_weight': weight,
                                                    'node_status': 1,
                                                }
                                                LoadNginx.save_loadnginx(load_add)
                                                load_one = Base(LoadNginx,condition={'db_status': 1, 'server_ip': self.ipaddr,'nginx_port': int(i['port']),'server_name': server_name,'url_suffix': l['name'],'upstream': upstream,'agent_node_ip':server[-1].split(':')[0],'agent_node_port': int(server[-1].split(':')[-1])}).findone()
                                            node_id.append(load_one.id)
                    if node_id:
                        load_all = Base(LoadNginx,condition={'db_status': 1, 'server_ip': self.ipaddr,'nginx_port': int(i['port']),'server_name': server_name}).fetchall()
                        for i in load_all:
                            if i.id not in node_id:
                                i.db_status = 0
                                Base.update()