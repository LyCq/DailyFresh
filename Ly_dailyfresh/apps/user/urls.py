from django.conf.urls import url
# 导入视图的模块
from apps.user.views import UserRegister,UserLogin,Active
urlpatterns = [
    # 跳转注册界面
    url(r'^register$',UserRegister.as_view(),name='register'),
    #　跳转登录界面
    url(r'^login$',UserLogin.as_view(),name='login'),
    # 验证码激活
    url(r'^active/(?P<token>.*)$',Active.as_view(),name='active'),

]