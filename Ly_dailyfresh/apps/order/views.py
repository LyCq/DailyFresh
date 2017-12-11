from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.urlresolvers import reverse
from django_redis import get_redis_connection
from apps.goods.models import GoodsSKU
from apps.user.models import Address
from apps.order.models import OrderInfo, OrderGoods
from django.http import  JsonResponse
from datetime import datetime


class OrderPlaceView(View):
    """显示提交订单的页面"""
    def post(self, request):
        # 获取参数，一键多值 接受到的是列表
        sku_ids = request.POST.getlist('sku_ids')
        # 进行参数校验
        if not all(sku_ids):
            # 没有商品id，重定向到购物车页面进行选择
            return redirect(reverse('cart:show'))
        # 获取登录的用户信息,构建cart_key
        user = request.user
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        skus = []
        # 初始化总的数量和总价
        total_count = 0
        total_price = 0
        # 查询对应的商品信息
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id = sku_id)
            # 查询商品在购物车中的数量
            count = conn.hget(cart_key, sku_id)
            count = int(count)
            # 计算每种商品的小计,redis 中的值是字符串类型，需要转化类型
            amount = sku.price * count
            # 动态的给sku对象添加数量和小计
            sku.count = count
            sku.amount = amount
            # 计算总的数量和总价
            total_count += count
            total_price += amount
            # 最后将sku对象添加到列表中
            skus.append(sku)


        for sku in skus:
            print(sku.name ,sku.price, sku.count, sku.amount)

        # 运费：运费子系统
        transit_price = 10

        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的全部地址
        addrs = Address.objects.filter(user=user)
        # 将sku_id 以逗号间隔拼接成字符串
        sku_ids = ','.join(sku_ids)

        # 构建context上下文
        context = {'addrs': addrs,
                   'total_count': total_count,
                   'total_price': total_price,
                   'transit_price': transit_price,
                   'total_pay': total_pay,
                   'skus': skus,
                   'sku_ids': sku_ids}

        return render(request,'place_order.html',context)


class OrderCommitView(View):
    '''订单提交'''
    def post(self, request):

        # 判断用户是否已经登录
        user = request.user
        if not user:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 获取参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        print(addr_id,pay_method,sku_ids)

        # 校验参数
        if  not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res':1, 'errmsg': '数据不完整'})
        print(1)
        # 检验地址
        addr = Address.objects.get(id= addr_id)
        if not addr:
            return JsonResponse({'res':2, 'errmsg':'地址信息错误'})
        print(2)
        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res':3, 'errmsg':'支付方式无效'})
        print(3)
        # 开始处理业务逻辑,构建参数
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') +  str(user.id)
        # 订单总金额和总数量
        total_count = 0
        total_price = 0
        # 运费
        transit_price = 10
        # 1. 先保存订单信息表
        order = OrderInfo.objects.create(
            order_id = order_id,
            user = user,
            addr = addr,
            pay_method = pay_method,
            total_count = total_count,
            total_price = total_price,
            transit_price = transit_price,
        )

        print(4)
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 获取商品
        sku_ids = sku_ids.split(',')
        for sku_id in sku_ids:
            # 根据id获取商品的信息
            try:
                sku = GoodsSKU.objects.get(id = sku_id)
            except GoodsSKU.DoesNotExist:
                return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

            # 获取用户要购买的商品的数目
            count = conn.hget(cart_key, sku_id)
            # 向订单商品表中添加信息
            OrderGoods.objects.create(
                order = order,
                sku = sku,
                count = count,
                price = sku.price
            )

            # 修改商品表中的数据
            sku.stock -= int(count)
            sku.sales += int(count)
            sku.save()

            # 将每个商品的数量和小计进行累加得到总的金额和件数
            total_price += sku.price * int(count)
            total_count += int(count)


        # 更新订单表中的总金额和总件数
        order.total_count = total_count
        order.total_price = total_price
        order.save()


        # 订单的相关信心写入完成之后删除购物车中的记录信息
        conn.hdel(cart_key,*sku_ids) # sku_ids 列表需要拆包
        # 返回应答
        return JsonResponse({'res':5,'message':'订单创建成功'})




