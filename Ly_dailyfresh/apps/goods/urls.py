from django.conf.urls import url
from apps.goods.views import IndexView

# 登录装饰器
from django.contrib.auth.decorators import login_required

# /index
urlpatterns = [
    # 跳转到首页显示
    url(r'^index$', IndexView.as_view(),name='index'),
]