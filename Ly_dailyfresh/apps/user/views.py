from django.shortcuts import render
# 认证系统
from user.models import User
from django.contrib.auth.models import User
import re

# 使用类视图需要导包
from django.views.generic import View

# /user/register
class UserRegister(View):
    def get(self,request):
        """显示注册页面"""


        return  render(request,'register.html')

    def post(self,request):
        # 获取表单传入的数据 wdDWDDSDSDsdd
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

        # 开始发送邮件

        return render(request,'index.html')

# /user/login
class UserLogin(View):
    def get(self,request):
        """显示登录页面"""
        return render(request,'login.html')
    def post(self,request):
        pass



