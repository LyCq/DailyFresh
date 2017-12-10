from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.views.generic import View
from apps.user.models import User, Address
from apps.goods.models import GoodsSKU

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_redister_active_email
from utils.Mixin import LoginRequiredMixin
from django_redis import get_redis_connection
import re
# Create your views here.


# /user/register
def register(request):
    '''注册'''
    if request.method == 'GET':
        # 显示注册页面
        return render(request, 'register.html')
    else:
        # 进行注册处理
        # 接收参数
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验参数
        # 校验参数的完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '参数不完整'})

        # 校验是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验邮箱是否合法
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 校验用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 进行业务处理: 进行注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 返回应答: 跳转到首页
        return redirect(reverse('goods:index'))


# /user/register_handle
def register_handle(request):
    '''注册处理'''
    # 接收参数
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')

    # 校验参数
    # 校验参数的完整性
    if not all([username, password, email]):
        return render(request, 'register.html', {'errmsg':'参数不完整'})

    # 校验是否同意协议
    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请同意协议'})

    # 校验邮箱是否合法
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

    # 校验用户名是否存在
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # 用户名不存在
        user = None

    if user:
        # 用户名已存在
        return render(request, 'register.html', {'errmsg': '用户名已存在'})

    # 进行业务处理: 进行注册
    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()

    # 返回应答: 跳转到首页
    return redirect(reverse('goods:index'))


# /user/register
class RegisterView(View):
    '''注册'''
    def get(self, request):
        '''显示'''
        return render(request, 'register.html')

    def post(self, request):
        '''注册处理'''
        # 接收参数
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验参数
        # 校验参数的完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '参数不完整'})

        # 校验是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验邮箱是否合法
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 校验用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 进行业务处理: 进行注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 加密用户的身份信息，生成激活token itsdangerous
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm':user.id}
        token = serializer.dumps(info) # bytes
        token = token.decode() # str

        # 发送激活邮件,邮件中需要有激活链接，需要在激活链接中包含用户的身份信息
        # 激活链接格式: /user/active/用户身份加密后的信息 /user/active/token
        # 找其他人帮助我们发送邮件 celery:异步执行任务
        # 发出任务
        send_redister_active_email.delay(email, username, token)

        # 返回应答: 跳转到首页
        return redirect(reverse('goods:index'))


# /user/active/加密信息token
class ActiveView(View):
    '''激活'''
    def get(self, request, token):
        '''激活'''
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']

            # 获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired:
            # 激活链接已失效
            return HttpResponse('激活链接已失效')


# /user/login
class LoginView(View):
    '''登录'''
    def get(self, request):
        '''显示'''
        # 尝试从cookie中获取username
        if 'username' in request.COOKIES:
            # 记住了用户名
            username = request.COOKIES['username']
            checked = 'checked'
        else:
            # 没记住用户名
            username = ''
            checked = ''

        # 使用模板
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self, request):
        '''登录校验'''
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember') # on

        # 参数校验
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'参数不完整'})

        # 业务处理: 登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态
                login(request, user)

                # 获取所有跳转到的地址, 默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))

                # 判断是否需要记住用户名
                response = redirect(next_url)
                # 设置cookie, 需要通过HttpReponse类的实例对象, set_cookie
                # HttpResponseRedirect JsonResponse
                if remember == 'on':
                    # 需要记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    # 不需要记住用户名
                    response.delete_cookie('username')

                # 跳转到首页
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg':'账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# /user/logout
class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        '''退出登录'''
        # 清除用户的登录状态
        logout(request)

        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user/
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''
    def get(self, request):
        '''显示'''
        # 获取登录用户
        user = request.user
        # 获取用户的个人信息:默认地址
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # from redis import StrictRedis
        # conn = StrictRedis(host='172.16.179.142', db=10)
        conn = get_redis_connection('default')
        history_key = 'history_%d'%user.id
        # 获取用户最新浏览的5个商品的id
        sku_ids = conn.lrange(history_key, 0, 4) # [4, 2, 1, 3]

        # 直接使用范围查询
        # skus = GoodsSKU.objects.filter(id__in=sku_ids)
        # skus_li = []
        # for sku_id in sku_ids:
        #     for sku in skus:
        #         if sku.id == sku_id:
        #             skus_li.append(sku)
        skus = []
        for sku_id in sku_ids:
            # 根据id查询商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 追加到列表中
            skus.append(sku)

        # 组织模板上下文
        context = {
            'skus':skus,
            'address': address,
            'page': 'user'}

        # 使用模板
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''
    def get(self, request):
        '''显示'''
        return render(request, 'user_center_order.html', {'page':'order'})


# 模型管理器类
# /user/address
class AddressView(LoginRequiredMixin, View):
    '''用户中心-地址页'''
    def get(self, request):
        '''显示'''
        # django框架会给request对象添加一个属性user
        # 如果用户已登录，user的类型User
        # 如果用户没登录，user的类型AnonymousUser
        # 除了我们给django传递的模板变量，django还会把user传递给模板文件

        # 获取登录的用户对象
        user = request.user
        # 获取用户的默认地址信息
        address = Address.objects.get_default_address(user)

        # 使用模板
        return render(request, 'user_center_site.html', {'address':address, 'page':'addr'})

    def post(self, request):
        '''添加地址'''
        # 接收参数
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 参数校验
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg':'参数不完整'})

        # 业务处理:地址添加
        # 获取登录的用户对象
        user = request.user
        # 如果用户没有默认地址，新添加的地址作为默认地址，否则不作为默认地址
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答, 刷新地址页面
        return redirect(reverse('user:address')) # get



