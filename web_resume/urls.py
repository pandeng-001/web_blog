from django.urls import path
# from web_resume.views import show_index, show_resume_index
from . import views


app_name = 'resume'  
urlpatterns = [
    # path("index", show_index),
    # path("index2", show_resume_index),
    path('', views.index, name='index'),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
    path('category/<slug:category_slug>/', views.article_list, name='category'),
    path('series/<slug:series_slug>/', views.series_page, name='series'),       # 系列页
    # 真正的“系列文章正文页”——返回带布局的 HTML
    path('series/<slug:series_slug>/article/<int:pk>/',
         views.series_article_page,                      # ← 新建一个视图
         name='series_article'),
     # 仅给 JS 调用的「单篇文章 JSON」接口
    path('series/<slug:series_slug>/article/<int:pk>/api/',
         views.series_article_api,
         name='series_article_api'),
]