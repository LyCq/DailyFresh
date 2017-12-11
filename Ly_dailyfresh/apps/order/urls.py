from django.conf.urls import url
from  apps.order.views import OrderPlaceView,OrderCommitView

urlpatterns = [
    # 显示提交订单页面
    url(r'^place$', OrderPlaceView.as_view(), name='place'),
    # 订单提交
    url(r'^commit$', OrderCommitView.as_view(), name='commit'),

]