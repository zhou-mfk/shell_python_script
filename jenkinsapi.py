import jenkins
import json
from xmljson import badgerfish
from xml.etree.ElementTree import fromstring


class JenkinsApi(object):
    """jenkins api"""

    def __init__(self, app_name):
        """
        :param app_name job名称
        """
        self.con_jenkins = jenkins.Jenkins(url='jks url', username='admin', password='admin')
        self.app_name = app_name
    
    def get_job(self):
        """检查app_name在jenkins中是否存在"""
        return self.con_jenkins.get_job_name(self.app_name)

    def get_job_config(self):
        """查询job config"""
        config_dict = {}
        if self.con_jenkins.get_job_name(self.app_name):
            job_config = self.con_jenkins.get_job_config(self.app_name)
            if job_config:
                try:
                    config_dict = xml2json(job_config)
                except Exception as e:
                    print('=======jks config=====')
                    print(e)
                    print('-----------------')
                    print(job_config)
        return config_dict

    # 创建job
    def create_job(self, job_xml):
        if not self.con_jenkins.get_job_name(self.app_name):
            self.con_jenkins.create_job(self.app_name, job_xml)
            return self.con_jenkins.get_job_name(self.app_name)
        else:
            return None

    # 构建job
    def build_job(self):
        if self.con_jenkins.get_job_name(self.app_name):
            self.con_jenkins.build_job(self.app_name)

    # 停止构建job
    def stop_build_job(self):
        if self.con_jenkins.get_job_name(self.app_name):
            # 获得正在build的job_id
            last_build_number = self.con_jenkins.get_job_info(self.app_name)['lastBuild']['number']
            self.con_jenkins.stop_build(self.app_name, last_build_number)
            return 'job: %s 已停止'
        else:
            return 'jks上无此job'

    # 停止所有在queue中的job
    def stop_queue_job(self, job_id=None):
        """
        :param job_id: 指定queue中的job id
        :return: True
        """
        queue_info = self.con_jenkins.get_queue_info()
        if queue_info:
            if job_id is None:
                for i in queue_info:
                    if 'id' in i and i['id']:
                        self.con_jenkins.cancel_queue(i['id'])
            else:
                for i in queue_info:
                    if i['id'] == job_id:
                        self.con_jenkins.cancel_queue(job_id)
            print('已清理queue中的job id')
            return True

    # 删除job
    def del_job(self):
        if self.con_jenkins.get_job_name(self.app_name):
            return self.con_jenkins.delete_job(self.app_name)

    # 获得视图
    def get_view(self, view_name):
        return self.con_jenkins.get_view_name(view_name)

    # 创建视图
    def create_view(self):
        view_configxml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
        <hudson.model.ListView>
          <name>{{ viewname }}</name>
          <description>{{ viewname }}</description>
          <filterExecutors>false</filterExecutors>
          <filterQueue>false</filterQueue>
          <properties class=\"hudson.model.View$PropertyList\"/>
          <jobNames>
            <comparator class=\"hudson.util.CaseInsensitiveComparator\"/>
            {% for app_name in app_list|sort %}<string>{{ app_name }}</string>
            {% endfor %}</jobNames>
          <jobFilters/>
          <columns>
            <hudson.views.StatusColumn/>
            <hudson.views.WeatherColumn/>
            <hudson.views.JobColumn/>
            <hudson.views.LastSuccessColumn/>
            <hudson.views.LastFailureColumn/>
            <hudson.views.LastDurationColumn/>
            <hudson.views.BuildButtonColumn/>
          </columns>
          <recurse>false</recurse>
        </hudson.model.ListView>"""
        temp_dict = {'app_list': ['job1', 'job2'], 'viewname': 'view_name'}
        
        t = Template(view_configxml).render(temp_dict)
        if not self.con_jenkins.get_view_name():
            self.con_jenkins.create_view(temp_dict['viewname'], t)
        else:
            self.con_jenkins.reconfig_view(temp_dict['viewname'], t)
        return '已批量创建视图'
        
    # 删除视图
    def del_view(self, view_name):
        if self.con_jenkins.get_view_name(view_name):
            self.con_jenkins.delete_view(view_name)
            return '已删除视图: %s' % view_name
        else:
            return 'jks上无此视图: %s' % view_name
