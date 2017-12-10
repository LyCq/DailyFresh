from django.contrib import admin
from apps.goods.models import GoodsType

from apps.goods.models import GoodsType,IndexPromotionBanner,IndexTypeGoodsBanner,IndexGoodsBanner

from django.core.cache import cache





class BaseAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        """新增或者更新数据的时候调用"""
        # 调用父类的方法实现数据的更新
        super().save_model(request, obj, form, change)

        # 附加的操作：后台修改数据之后，重新生静态的首页

        # 开始发出任务到celery处理，为何在顶部导入不可以，执行celery会出错
        from celery_tasks.tasks import generate_static_index
        generate_static_index.delay()

        # 删除失效的缓存数据
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """删除数据的时候调用"""
        # 调用父类的方法来实现数据的删除
        super().delete_model(request, obj)

        # 附加的操作：重新生成首页的静态文件
        from celery_tasks.tasks import generate_static_index
        generate_static_index.delay()

        # 删除失效的缓存数据
        cache.delete('index_page_data')



class GoodsTypeAdmin(BaseAdmin):
    pass


class IndexPromotionBannerAdmin(BaseAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseAdmin):
    pass


class IndexGoodsBannerAdmin(BaseAdmin):
    pass


# 注册模型
admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)