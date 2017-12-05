from django.conf.urls import url
from apps.goods.views import Index

# 登录装饰器
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # 跳转到首页显示
    url(r'^index$',Index.as_view(),name='index'),
]