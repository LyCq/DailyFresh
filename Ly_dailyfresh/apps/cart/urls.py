from django.conf.urls import url
from apps.cart.views import CartInfoView,CartInfoAdd
urlpatterns = [
    # 添加到购物车
    url(r'^add$',CartInfoAdd.as_view(), name='add'),
    # 显示购物车页
    url(r'^$', CartInfoView.as_view(),name='show'),
]