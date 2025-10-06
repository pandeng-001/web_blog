from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Category, Article, ArticleImage,Series


class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 1          # 默认出现 1 个空白上传框
    fields = ['photo']


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'series', 'series_order', 'is_pinned', 'created_at', 'created_at', 'views')
    list_filter  = ('category', 'series', 'is_pinned', 'created_at')
    search_fields = ('title', 'summary')
    # 编辑页字段顺序
    list_editable = ('series_order', 'is_pinned') 
    fields = ('title', 'summary', 'cover', 'category', 'series', 'series_order', 'is_pinned',
              'content_md', 'content_html', 'views')
    readonly_fields = ('content_html', 'created_at', 'updated_at')
    inlines = [ArticleImageInline]

admin.site.register(Category)

