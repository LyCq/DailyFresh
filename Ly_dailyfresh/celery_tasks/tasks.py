from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
# 初始化celery的实例
# 初始化celery 需要的环境配置
# import os,django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE','Ly_dailyfresh.settings')
# django.setup()

app = Celery('celery_tasks.tasks',broker='redis://10.211.55.3:6379/1')


@app.task
def send_redister_active_email(email,username,token):
    """定义发送邮件的处理函数"""

    subject = '天天生鲜欢迎你'
    message = ''
    recv_list = [email]
    html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击以下链接激活您的账号<br/>' \
                   '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' \
                   % (username, token, token)

    sender = settings.EMAIL_FROM
    send_mail(subject, message, sender, recv_list, html_message=html_message)
