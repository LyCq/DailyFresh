from django.contrib import admin

from apps.user.models import User,Address


# 注册用户和地址模型类
admin.site.register(User)
admin.site.register(Address)