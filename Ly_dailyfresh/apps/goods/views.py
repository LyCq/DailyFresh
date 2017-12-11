from django.shortcuts import render, redirect
from django.views.generic import View
from apps.order.models import OrderGoods
from apps.goods.models import GoodsSKU, GoodsType, IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django.core.urlresolvers import reverse
from django_redis import get_redis_connection

from django.core.paginator import Paginator
# 使用缓存导入相关的包
from django.core.cache import cache


class IndexView(View):
    """首页"""
    def get(self, request):
        """显示"""
        # 先判断缓存中是否有数据,没有数据不会报错返回NONE
        context = cache.get('index_page_data')

        if context is None:

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



            # 组织上下文
            context = {
                'types': types,
                'index_banner': index_banner,
                'promotion_banner': promotion_banner,
            }
            # 设置缓存数据,缓存的名字，内容，过期的时间
            cache.set('index_page_data', context, 3600)

        # 获取user
        user = request.user
        # 获取登录用户的额购物车中的商品的数量
        cart_count = 0
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            # 获取用户购物车中国的商品条目数
            cart_count = conn.hlen(cart_key)

            context.update(cart_count = cart_count)

        return render(request, 'index.html', context)

class DetailView(View):
    """"""
    def get(self,request, sku_id):
        #sku_id = request.get('sku_id')
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # shangping bu cunzai
            return  redirect(reverse('goods:index'))

        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        order_skus =OrderGoods.objects.filter(sku=sku).order_by('-update_time')


        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku.id)

        # 查询类别
        types = GoodsType.objects.all()

        #  获取user
        user = request.user
        # 获取用户购物车中商品的条目数
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            # 获取用户购物车商品条目数
            cart_count = conn.hlen(cart_key)

        conn = get_redis_connection('default')
        history_key = 'history_%d' % user.id

        conn.lrem(history_key, 0 ,sku_id)

        conn.lpush(history_key, sku_id)
        conn.ltrim(history_key, 0 ,4)

        # 组织模板上下文件
        context = {'sku': sku,
                   'new_skus': new_skus,
                   'order_skus': order_skus,
                   'same_spu_skus': same_spu_skus,
                   'cart_count': cart_count,
                   'types': types}

        # 使用模板
        return render(request, 'detail.html', context)


class ListView(View):

    def get(self, request, type_id, page):
        try:
            type = GoodsType.objects.get(id = type_id)

        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取分类信息
        types = GoodsType.objects.all()
        # 获取排序方式，获取分类商品的列表信息
        sort = request.GET.get('sort', 'default')

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')

        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 每页显示一条数据
        paginator = Paginator(skus, 1)

        page = int(page)

        # 进行页面判断
        if page > paginator.num_pages or page <= 0:
            page = 1

        # 获取第page页面的Page对象
        skus_page = paginator.page(page)

        # 页码列表处理
        num_pages = paginator.num_pages # 返回页面总数

        # 分页之后宗页数不足5页
        # 当前页属于前三页，显示1-5页
        # 当前页属于后三页，显示后5页
        # 其他的情况喜爱男士当前页的前2页，当前页，当前页的后2页
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 获取分类的2个新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取user
        user = request.user
        # 获取用户购物车中商品的条目数
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            # 获取用户购物车商品条目数
            cart_count = conn.hlen(cart_key)

        # 组织上下文
        context = {'type': type,
                   'types':types,
                   'skus_page': skus_page,
                   'pages': pages,
                   'new_skus': new_skus,
                   'cart_count': cart_count,
                   'sort': sort}

        # 使用模板
        return render(request, 'list.html', context)