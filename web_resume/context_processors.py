# def base_extra(request):
#     from web_resume.models import Category
#     category_slug = request.resolver_match.kwargs.get('category_slug')
#     category = Category.objects.filter(slug=category_slug).first()
#     return {
#         'categories': Category.objects.all(),
#         'category': category,
#     }


from web_resume.models import Category, Series
from django.db.models import Min

def base_extra(request):
    # 当前访问的分类
    category_slug = request.resolver_match.kwargs.get('category_slug') \
                    if request.resolver_match else None
    category = Category.objects.filter(slug=category_slug).first()

    # 当前访问的系列
    series_slug = request.resolver_match.kwargs.get('series_slug') \
                  if request.resolver_match else None
    series = Series.objects.filter(slug=series_slug).first()

    return {
        'categories': Category.objects.all(),
        'category': category,
        'series_list': Series.objects.all(),   # 所有系列
        'series': series,                      # 当前系列（如果有）
    }
