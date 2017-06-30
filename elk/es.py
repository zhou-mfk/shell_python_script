#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: Zhoulishan
# email : zhou_mfk@163.com
# date  : 17/04/06 11:48:49

import time
import sys
import datetime
from elasticsearch import Elasticsearch

host = "10.201.240.3"
port = 9200
timeout = 60


class GetData(object):

    def __init__(self, index, query, aggs={}, timestart=None, timeend=None):
        self.index = index
        self.query = query
        self.timestart = timestart
        self.timeend = timeend
        self.aggs = aggs
        self.hours = 2
        self.d = {}
        self.p = {}
        self.es = Elasticsearch(host, port=port, timeout=timeout)

    def _istimeformat(self, date):
        if ":" in date:
            if len(date.split(":")) == 3:
                if time.strptime(date, '%Y-%m-%d %H:%M:%S'):
                    return date
                else:
                    return False
            elif len(date.split(":")) == 2:
                if time.strptime(date, '%Y-%m-%d %H:%M'):
                    return date + ":00"
                else:
                    return False
        else:
            if time.strptime(date, '%Y-%m-%d'):
                return date.strip(" ") + " 00:00:00"
            else:
                return False
    def get_time(self):
        if self.timestart is not None and self.timeend is not None:
            t1 = self._istimeformat(self.timestart)
            t2 = self._istimeformat(self.timeend)
            if t1:
                st = int(time.mktime(time.strptime(t1, "%Y-%m-%d %H:%M:%S")))
                if t2:
                    et = int(time.mktime(time.strptime(t2, "%Y-%m-%d %H:%M:%S")))
                    if st > et:
                        print "开始时间超过结束时间。"
                        sys.exit(2)
                    else:
                        return st, et
                else:
                    print "结束时间格式不对，请检查后再用"
                    sys.exit(1)
            else:
                print "开始时间格式不对"
                sys.exit(1)
        elif self.timestart is not None and self.timeend is None:
            t1 = self._istimeformat(self.timestart)
            temp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            t2 = self._istimeformat(temp)
            if t1:
                st = int(time.mktime(time.strptime(t1, "%Y-%m-%d %H:%M:%S")))
                et = et = int(time.mktime(time.strptime(t2, "%Y-%m-%d %H:%M:%S")))
                return st, et
            else:
                print "开始时间格式不对"
                sys.ext(1)
        elif self.timestart is None and self.timeend is None:
            et = datetime.datetime.now()
            end_time = et.strftime("%Y-%m-%d %H")
            end_time = end_time + ":00:00"
            start_time = (datetime.datetime.now() - datetime.timedelta(hours=self.hours)).strftime("%Y-%m-%d %H")
            start_time = start_time + ":00:00"
            st = int(time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S")))
            et = int(time.mktime(time.strptime(end_time, "%Y-%m-%d %H:%M:%S")))
            return st, et
        else:
            print "时间格式不对"
            sys.exit(3)

    def get_body(self, aggs={}):
        start_time, end_time = self.get_time()
        start_time = str(start_time) + '000'
        end_time = str(end_time) + '000'
        body = {
            "size": 0,
            "query": {
                "filtered": {
                    "query": {
                        "query_string": {
                            "query": self.query,
                            "analyze_wildcard": "true"
                        }
                    },
                    "filter": {
                        "bool": {
                            "must": [{
                                "range": {
                                    "timestamp": {
                                        "gte": start_time,
                                        "lte": end_time,
                                        "format": "epoch_millis"
                                    }
                                }
                            }],
                            "must_not": []
                        }
                    }
                }
            },
            "aggs": aggs
        }
        return body

    def get_total(self):
        total_boby = self.get_body()
        res_total = self.es.search(index=self.index, body=total_boby)
        total_num = res_total['hits']['total']
        return total_num

    def get_data(self):
        c_body = self.get_body(self.aggs)
        res = self.es.search(index=self.index, body=c_body)
        return res
