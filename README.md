# storybook_server app客户端和网页管理前端共用一个工程
1、运行`pip install -r htproject.txt`安装环境

2、初次部署环境时，
运行`python manage.py makemigrations` 

3、运行`python manage.py migrate`迁移数据库

4、检查数据库环境的时区是否是北京时间，在数据库中运行`select now()`,
如果不是，则在数据库配置文件my.cnf中添加如下信息：
 ```
 [mysqld]
default-time-zone = '+8:00'
```
 
5、重启mysql服务。

6、运行`python manage.py init`初始化基础数据库信息

（初始数据涉及标签表  后台管理员初始电话号码：13333333333 登录密码：123456）