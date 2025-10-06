from django.shortcuts import render, get_object_or_404

# Create your views here.

from django.http import HttpResponse
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 展示 index 页面
# def show_index(request):
#     return render(request, "index.html")

# def show_resume_index(request):
#     return render(request, "resume/index.html")

from .models import Article, Category, Series
import markdown
from django.core.paginator import Paginator
from django.http import JsonResponse

# def index(request):
#     articles = Article.objects.all()
#     return render(request, 'resume/index.html', {'articles': articles})


def index(request):
    pinned = Article.objects.filter(is_pinned=True)[:3]          # 最多 3 篇置顶
    latest = Article.objects.filter(is_pinned=False)[:2]        # 普通最新
    return render(request, 'resume/index.html', {'pinned': pinned, 'latest': latest})

# —— 系列首页 ——
def series_page(request, series_slug):
    series    = get_object_or_404(Series, slug=series_slug)
    articles  = series.articles.all()          # 约定 related_name="articles"
    first_art = articles.first()
    return render(request, 'resume/series_page.html', {
        **base_extra(request),
        'series':   series,
        'articles': articles,
        'article':  first_art,      # 右侧默认展示第一篇
    })



# —— 系列首页 ——
def series_page(request, series_slug):
    series    = get_object_or_404(Series, slug=series_slug)
    articles  = series.articles.all()          # 约定 related_name="articles"
    first_art = articles.first()
    return render(request, 'resume/series_page.html', {
        **base_extra(request),
        'series':   series,
        'articles': articles,
        'article':  first_art,      # 右侧默认展示第一篇
    })

# —— 系列正文页（整页直出）——
def series_article_page(request, series_slug, pk):
    series   = get_object_or_404(Series, slug=series_slug)
    article  = get_object_or_404(Article, pk=pk, series=series)
    articles = series.articles.all()
    return render(request, 'resume/series_page.html', {
        **base_extra(request),
        'series':   series,
        'articles': articles,
        'article':  article,
    })


# —— 给 JS 调用的纯数据接口 ——
def series_article_api(request, series_slug, pk):
    article = get_object_or_404(Article, pk=pk, series__slug=series_slug)
    return JsonResponse({
        'id':          article.id,
        'title':       article.title,
        'content_html': article.content_html,
    })


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.views += 1
    article.save(update_fields=['views'])
    return render(request, 'resume/detail.html', {'article': article})



def article_list(request, category_slug=None):
    qs = Article.objects.all()
    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        qs = qs.filter(category=category)

    paginator = Paginator(qs, 5)
    page_obj = paginator.get_page(request.GET.get('page'))

    # 手动把分类数据写进 context
    return render(request, 'resume/list.html', {
        'page_obj': page_obj,
        'category': category,
        'categories': Category.objects.all(),   # ← 必须手动传
    })

def base_extra(request):
    return {'categories': Category.objects.all(), 'category': None}   # 默认无分类