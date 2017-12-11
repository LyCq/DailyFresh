from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

from apps.goods.models import GoodsType, IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner

from  django.template import loader,RequestContext
# 初始化celery的实例
# 初始化celery 需要的环境配置
import os,django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','Ly_dailyfresh.settings')
django.setup()


# 导入商品模块的模型
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
# 导入模板对应的包
from django.template import loader,RequestContext
# 导入项目的配置文件
from django.conf import settings
import os

# 使用redis 的数据库1，作为中间人
app = Celery('celery_tasks.tasks',broker='redis://10.211.55.4:6379/1')


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

@app.task

def generate_static_index():
    """生成静态的首页"""
    # 查询商品的分类信息
    types = GoodsType.objects.all()
    # 获取首页轮播的商品的信息
    index_banner = IndexGoodsBanner.objects.all().order_by('index')
    # 获取首页促销的活动信息
    promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品信息展示
    for type in types:
        # 查询首页显示的type类型的文字商品信息
        title_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        # 查询首页显示的图片商品信息
        image_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 动态给type对象添加两个属性保存数据
        type.title_banner = title_banner
        type.image_banner = image_banner

    # 获取登录用户的额购物车中的商品的数量
    cart_count =  0

    # 组织上下文
    context = {
        'types': types,
        'index_banner': index_banner,
        'promotion_banner': promotion_banner,
        'cart_count': cart_count
    }

    # 生成静态首页的内容 render 》 HttpResponse对象
    # 1. 加载模板文件
    template  = loader.get_template('static_index.html')
    # 2. 渲染模板,生成HTML
    static_index_html = template.render(context)
    # 3.保存生成的静态页面,保存在static文件夹下面
    static_path = os.path.join(settings.BASE_DIR,'static/index.html')

    # 开始保存数据
    with open(static_path, 'w') as file:
        file.write(static_index_html)




