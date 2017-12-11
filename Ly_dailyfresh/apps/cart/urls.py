from django.conf.urls import url
from apps.cart.views import CartInfoView,CartInfoAdd, CartInfoUpdate,CartInfoDelete
urlpatterns = [
    # 添加到购物车
    url(r'^add$',CartInfoAdd.as_view(), name='add'),
    # 显示购物车页
    url(r'^$', CartInfoView.as_view(),name='show'),
    # 购物车数据更新
    url(r'^update$', CartInfoUpdate.as_view(), name='update'),
    # 删除购物车中的商品记录
    url(r'^delete$', CartInfoDelete.as_view(), name='delete'),
]