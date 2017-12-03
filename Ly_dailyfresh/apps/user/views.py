from django.shortcuts import render,redirect
from django.http import HttpResponse
# 认证系统
from apps.user.models import User
# 发送邮件的包
from django.core.mail import send_mail
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.core.urlresolvers import reverse
# 认证系统的认证函数
from django.contrib.auth import authenticate,login

import re
# 使用类视图需要导包
from django.views.generic import View


# /user/register
class UserRegister(View):

    def get(self,request):
        """显示注册页面"""
        return render(request,'register.html')

    def post(self,request):
        # 获取表单传入的数据
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        cpwd  = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 开始进行数据校验, all(列表)　对列表中的数据进行校验，全部数据不为空则返回Ｔｒｕｅ
        if not all([username,pwd,cpwd,email]):
            return render(request,'register.html',{'errormsg':'数据不能为空'})
        if pwd != cpwd:
            return render(request,'register.html',{'errormsg':'两次密码不一致'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
            return render(request,'register.html',{'errormsg':'邮箱格式不正确'})
        if not allow == 'on':
            return render(request,'register.html',{'errormsg':'请同意协议'})

        try:
            user = User.objects.get(username__exact=username)
        except User.DoesNotExist:
            # 没有该用户
            user = None
        if user:
            return render(request,'register.html',{'errormsg':'用户名已经存在'})

        # 开始执行业务逻辑
        # 使用django自带的认证系统,保存到数据库，返回user对象
        user = User.objects.create_user(username,email,pwd)
        user.is_active = 0
        user.save()

        # 加密用户id
        info = {'user_id':user.id}
        serializer = Serializer(settings.SECRET_KEY,3600)
        token = serializer.dumps(info)
        # 字节解码
        token = token.decode()

        # 开始发送邮件,构造数据
        # 标题
        subject = '天天生鲜欢迎你'
        message = ''
        recv_list = [email]
        html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击以下链接激活您的账号<br/>' \
                       '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>'\
                       %(username, token, token)

        sender = settings.EMAIL_FROM
        send_mail(subject,message,sender,recv_list,html_message=html_message)
        return redirect(reverse('goods:index'))


# 激活验证码 /user/active/(token)
class Active(View):

    def get(self,request,token):
        try:
            # 获取传入的信息并解码
            serializer = Serializer(settings.SECRET_KEY,3600)
            info = serializer.loads(token)
            user_id = info['user_id']
            # 根据用户ｉd 查询数据库
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转到登录页面
            return redirect(reverse('goods:index'))
        except SignatureExpired:
            return HttpResponse('激活时间超时')


# /user/login
class UserLogin(View):

    def get(self,request):
        """显示登录页面"""
        return render(request,'login.html')

    def post(self,request):

        # 获取表单提交的数据
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')
        check = request.POST.get('check')

        # 开始校验数据是否完整
        if not all([username,pwd]):
            return render(request,'login.html',{'errormsg':'输入的数据不完整'})
        # 开始处理业务逻辑
        user = authenticate(username=username,password=pwd)

        if user is not None:
            # 正确
            if user.is_active:
                # 将用户信息保存到session 使用login（）
                login(request,user)
                # 重定向到首页
                response = redirect(reverse('goods:index'))

                if check== 'on':
                    # 记住用户名，设置cookie保存到浏览器
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    # 不需要记住密码
                    response.delete_cookie('username')
                # 重定向到首页
                return response

            else:
                return render(request, 'login.html', {'errormsg': '该用户没有激活'})

        else:
            # 不正确
            return render(request,'login.html',{'errormsg':'用户名或者密码错误'})






