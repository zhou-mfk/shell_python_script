#!/bin/bash
#
#获得Nginx或openresty 和 Tomcat配置文件路径信息

if [ ! -f /opt/app/appPorts.properties ];then
	echo "此服务器上没有配置文件存在"
	exit 4
fi

st=`egrep -v "^#|^$|stop|start" /opt/app/appPorts.properties`
if [ "st"X != X ];then
	echo $st | grep nginx >> /dev/null
	if [ $? -eq 0 ];then
		nginx_pid=`ps aux | grep nginx | grep master | grep -v grep | grep -v $0 | awk '{print $2}'`
		#下面这个命令需要root权限或者nginx用户能执行
		nginx_cmd=`ls -l /proc/$nginx_pid | grep exe | awk '{print $NF}'`
		nginx_sbin=`dirname $nginx_cmd`
		nginx_dir=`dirname $nginx_sbin`
		grep 'openresty' $nginx_cmd >> /dev/null
		if [ $? -eq 0 ];then
			echo "{'openresty': '$nginx_dir/conf'}"
			
		else
			echo "{'nginx': '$nginx_dir/conf'}"
		fi
	fi
fi

#tomcat
sst=`egrep -v "^#|^$|stop|start|nginx" /opt/app/appPorts.properties`
if [ "sst"X != X ];then
	for s in $sst;do
		project_name=`echo $s | awk -F "=" '{print $1}'`
		project_port=`echo $s | awk -F "=" '{print $2}'`
		tomcat_dir="/opt/app/server/apache-tomcat-$project_port"
		echo "{'tomcat_conf': '$tomcat_dir/conf','tomcat_bin': '$tomcat_dir/bin'}"
	done
fi
