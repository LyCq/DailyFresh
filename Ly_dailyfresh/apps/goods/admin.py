from django.contrib import admin
from apps.goods.models import GoodsType
#注册商品类型
admin.site.register(GoodsType)
