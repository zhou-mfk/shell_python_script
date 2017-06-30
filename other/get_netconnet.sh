#!/bin/bash

localip=$(ip addr | grep "inet " | awk '{print $2}' | awk -F"/" '{print $1}' | grep -v '127.0.0.1' | head -1)

if [ -f /opt/app/appPorts.properties ];then
  ports=$(cat /opt/app/appPorts.properties | grep -v stop | grep -Ev "^#|^$" | grep -v nginx | awk -F'=' '{print $2}')
  if [ X"$ports" = X ];then
    echo "{\"sourceip\":\"$localip\",\"info\":\"no ports\"}"
    exit 0
  else
    for port in $ports;do
        #根据配置文件读取相关应用的pid
        pid=$(ps -ef | grep -w $port | grep -v grep | grep -v $0 | awk '{print $2}')
	if [ X"$pid" = X ];then
	    echo "{\"sourceip\":\"$localip\",\"$port\",\"info\":\"no pid\"}"
	    exit 0
        else
            #根据pid获取该应用的连接信息
            dest=$(sudo netstat -anp | grep $pid |grep tcp | grep -v '127.0.0.1' | grep ESTABLISHED | awk '{print $5}' | uniq)
            destjson=$(echo $dest | sed "s/ /\;/g" )
            name=$(cat /opt/app/appPorts.properties | grep -v stop | grep -Ev "^#|^$" | grep -w $port | awk -F '=' '{print $1}' | sed 's/-start//')
            echo "{\"sourceip\":\"$localip\",\"app_name\":\"$name\",\"dest\":\"$destjson\"}" 2> /dev/null
	fi
    done
  fi
else
  echo "{\"sourceip\":\"$localip\",\"info\":\"no appPorts.properties\"}"
  exit 0
fi
