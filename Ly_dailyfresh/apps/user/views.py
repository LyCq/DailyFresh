from django.shortcuts import render,redirect
from django.http import HttpResponse
# 认证系统
from apps.user.models import User
from apps.goods.models import GoodsSKU
# 发送邮件的包
from django.core.mail import send_mail
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.core.urlresolvers import reverse
# 认证系统的认证函数
from django.contrib.auth import authenticate, login,logout
from celery_tasks.tasks import send_redister_active_email
import re
# 使用类视图需要导包
from django.views.generic import View
# 导入地址的类
from apps.user.models import Address

# 使用redis的两种方法
from redis import StrictRedis

from django_redis import get_redis_connection


# 使用登录验证
from utils.Mixin import LoginRequiredMixin


# /user/register
class UserRegister(View):
    """用户注册"""
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
        # # 标题
        # subject = '天天生鲜欢迎你'
        # message = ''
        # recv_list = [email]
        # html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击以下链接激活您的账号<br/>' \
        #                '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>'\
        #                %(username, token, token)
        #
        # sender = settings.EMAIL_FROM
        # send_mail(subject,message,sender,recv_list,html_message=html_message)
        # 调用函数发送邮件给中间人border
        send_redister_active_email.delay(email,username,token)

        return redirect(reverse('goods:index'))


# /user/active/(token)
class Active(View):
    """ 激活验证码"""

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
    """用户登录"""

    def get(self,request):
        """显示登录页面"""
        # 从cookie 中获取用户名
        if 'username' in request.COOKIES:
            # 表示记住了用户名,需要将名字显示在页面上
            username = request.COOKIES['username']
            checked = 'checked'
        else:
            # 没有记住用户名
            username = ''
            checked = ''

        # 拼接上下文
        context = {'username':username,'checked':checked}
        return render(request,'login.html',context)

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

                # 获取next参数,获取不到next会返回None，设置默认值
                next_url = request.GET.get('next', reverse('goods:index'))
                # 重定向到首页
                response = redirect(next_url)

                if check== 'on':
                    # 记住用户名，设置cookie保存到浏览器
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    # 不需要记住用户名
                    response.delete_cookie('username')
                # 重定向到首页
                return response

            else:
                return render(request, 'login.html', {'errormsg': '该用户没有激活'})

        else:
            # 不正确
            return render(request,'login.html',{'errormsg':'用户名或者密码错误'})


# /user/logout
class UserLoginOut(View):
    """用户退出登录"""
    def get(self, request):
        logout(request)
        # 重定向首页显示
        return redirect(reverse('goods:index'))


# /user/center
class UserInfoView(LoginRequiredMixin,View):
    """用户中心"""
    def get(self,request):
        """显示用户页面"""
        # 获取当前用户的信息进行显示
        user = request.user
        # 获取用户的地址信息
        address = Address.objects.get_default_address(user)
        # 从redis中获取浏览的历史记录，redis中保存的是id，使用列表保存
        # 创建redis的链接第一种方式
        conn = StrictRedis(host='localhost',port=6379,db=2)

        # 构建key,查询redis
        history_key = 'history_%d' % user.id
        history_list = conn.lrange(history_key,0,4)

        # 进行遍历
        goods_list = []
        for good_id in history_list:
            good = GoodsSKU.objects.get(good_id = good_id)
            goods_list.append(good)

        # 构建上下文
        context = {'user': user, 'address': address, 'skus': goods_list}
        return render(request, 'user_center_info.html', context)

# user/order
class UserOrderView(LoginRequiredMixin,View):
    """用户中心 订单页面"""
    def get(self,request):
        """显示用户订单页面"""
        return render(request,'user_center_order.html',{'page':'order'})

# user/address
class AddressView(LoginRequiredMixin,View):
    """用户中心 地址页面"""
    def get(self,request):
        """显示默认的地址页面"""
        user = request.user
        try:

            address = Address.objects.get(user=user,is_default=True)
        except Address.DoesNotExist:
            address = None
        return render(request,'user_center_site.html',{'address': address, 'page': 'address'})

    def post(self,request):
        """添加对象"""
        # 接受参数
        receiver = request.POST['receiver']
        address = request.POST['address']

        zip_code = request.POST['zip_code']
        phone = request.POST['phone']

        # 参数校验
        if not  all([receiver, address, zip_code, phone]):
            return render(request,'user_center_site.html',{"errmsg": '参数不完整'})

        # 开始处理业务逻辑
        # 获取登录的用户对象
        user = request.user
        # 先查询是否存在默认的地址，如果没有地址就进行判断，将当前的地址设为默认地址
        default_address = Address.objects.get_default_address(user)
        if default_address:
            is_default = False
        else:
            is_default = True

        # 开始添加地址
        Address.objects.create(
            user= user,
            receiver = receiver,
            addr = address,
            zip_code = zip_code,
            phone = phone,
            is_default = is_default
        )

        # 返回页面，刷新地址页面
        return redirect(reverse('user:address'))