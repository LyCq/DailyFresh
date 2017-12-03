from django.conf.urls import url
# 导入视图的模块
from user.views import UserRegister,UserLogin
urlpatterns = [
    url(r'^register$',UserRegister.as_view(),name='regisetr'),
    url(r'^login$',UserLogin.as_view(),name='login'),

]