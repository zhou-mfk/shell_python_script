百联 CMDB System
===
* 域名 cmdb.bl.com

创建虚拟环境
---

    $ git clone git@gitlab.ops.bl.com:/blcmdb.git
    $ virtualenv env --no-site-packages
    $ source env/bin/activate
    $ python setup.py install
    $ nohup python web.py >/dev/null 2>/var/log/cmdb.log &
    $ nohup celery -A application.celery worker --loglevel=info > /var/log/celery.log &



* 服务器需要安装 redis-server
* 开发环境 Python2.7