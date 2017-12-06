from django.shortcuts import render
from django.views.generic import View
from apps.goods.models import GoodsType, IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner

from django_redis import get_redis_connection
# Create your views here.


class IndexView(View):
    """首页"""
    def get(self, request):
        """显示"""
        # 查询商品的分类信息
        types = GoodsType.objects.all()
        # 获取首页轮播的商品的信息
        index_banner = IndexGoodsBanner.objects.all().order_by('index')
        # 获取首页促销的活动信息
        promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

        # 获取首页分类商品信息展示
        for type in types:
            # 查询首页显示的type类型的文字商品信息
            title_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type = 0).order_by('index')
            # 查询首页显示的图片商品信息
            image_banner = IndexTypeGoodsBanner.objects.filter(type= type, display_type = 1).order_by('index')
            # 动态给type对象添加两个属性保存数据
            type.title_banner = title_banner
            type.image_banner = image_banner

        # 获取user
        user= request.user
        # 获取登录用户的额购物车中的商品的数量
        cart_count =  0
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            # 获取用户购物车中国的商品条目数
            cart_count = conn.hlen(cart_key)

        # 组织上下文
        context = {
            'types': types,
            'index_banner': index_banner,
            'promotion_banner': promotion_banner,
            'cart_count': cart_count
        }

        return render(request, 'index.html', context)