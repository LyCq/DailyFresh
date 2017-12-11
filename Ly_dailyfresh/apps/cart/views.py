from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
# Create your views here.
# 在前端使用ajax发起请求， 获取数据使用get方式，涉及到数据的修改使用post方式

# 在这使用post方式
class CartInfoAdd(View):
    '''添加购物车'''
    def post(self, request):
        # 获取user对象，判断用户是否已经登陆

        user = request.user

        if not user.is_authenticated():
            # 用户没有登陆,返回json
            return JsonResponse({'res':0, 'errmsg':'用户没有登陆'})

        # 用户已经登陆，开始接受参数
        sku_id = request.POST['sku_id']
        count = request.POST['count']
        # 参数校验
        if not all([sku_id, count ]):
            return JsonResponse({'res':1, 'errmsg':'参数不完整'})


        # 开始校验商品的id
        try:

            sku = GoodsSKU.objects.get(id = sku_id)
        except Exception as e :
            # 商品不存在
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 校验商品的数目
        try:
            count = int(count)
        except Exception as e:
            # 商品数目不是一个数字
            return JsonResponse({'res': 3, 'errmsg': '商品数目不合法'})

        if count <= 0:
            return JsonResponse({'res': 3, 'errmsg': '商品数目不合法'})

        # 业务处理：添加购物车记录 cart_1: {'1':2, '2':3}
        # sku_id已经被添加过，商品数目做累加, 否则加一个新的元素
        # 获取reids的连接，保存记录到redis
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 先获取sku_id的值
        cart_count = conn.hget(cart_key, sku_id)

        if cart_count:
            # redis中存在该商品，进行数量累加
            count += int(cart_count)
        # 判断商品的库存
        if count > sku.stock:
            # 库存不足
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
        # 库存数量足够，开始添加数据

        conn.hset(cart_key,sku_id, count)

        # 获取用户购物车中的条目数
        cart_count = conn.hlen(cart_key)

        # 返回json数据回前台界面
        return JsonResponse({'res':5, 'cart_count':cart_count, 'message':'添加成功'})


class CartInfoView(View):
    """购物车页面显示"""
    def get(self, request):
        """显示页面"""
        # 获取登陆的用户
        user = request.user
        # 连接redis
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_dict = conn.hgetall(cart_key)

        # 定义一个商品的空列表
        skus = []
        # 定义总价和总数量
        total_count = 0
        total_price = 0

        # 获取对应的商品信息,redis中的值是字符串类型
        for sku_id, count  in cart_dict.items():
            # 根据sku_id 获取商品信息
            sku = GoodsSKU.objects.get(id=sku_id)
            count = int(count)
            # 计算商品的小计
            amount = sku.price * count
            # 给商品动态的添加小计和数量
            sku.count = count
            sku.amount = amount

            # 将商品信息添加到列表中
            skus.append(sku)

            # 累计总的商品数量和总价
            total_price += amount
            total_count += count


        # 组织上下文
        context = {
            'skus': skus,
            'total_price': total_price,
            'total_count': total_count,
        }

        return render(request,'cart.html', context)


class CartInfoUpdate(View):
    """"""
    def post(self, request):
        user = request.user
        if user.is_authenticated():
            pass
        # 