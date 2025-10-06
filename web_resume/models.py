from django.db import models

# Create your models here.

# blog/models.py
from django.db import models
from django.utils.text import slugify
from bs4 import BeautifulSoup  
import itertools

class Category(models.Model):
    name = models.CharField('category_name', max_length=30, unique=True)       # 文章类型——名字
    slug = models.SlugField('url_click', unique=True)                          # url别名

    def save(self, *args, **kwargs):
        if not self.slug:                      # 只在首次为空时生成
            self.slug = slugify(self.name)     # 支持中文->拼音 或保留英文
            # 若担心重复，可循环加后缀
            origin = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exists():
                self.slug = f"{origin}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Series(models.Model):
    """文章系列"""
    name  = models.CharField('series_name', max_length=50, unique=True)
    slug  = models.SlugField('URL_name', unique=True, blank=True)
    desc  = models.TextField('series_info', blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            self.slug = base
            for i in itertools.count(1):
                if not Series.objects.filter(slug=self.slug).exists():
                    break
                self.slug = f'{base}-{i}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    title      = models.CharField('title', max_length=120)                      # 标题
    summary    = models.CharField('abstract', max_length=255, blank=True)       # 摘要
    content_md = models.TextField('content')                                    # 正文
    content_html = models.TextField('con_HTML', editable=False, blank=True)     # 渲染后html
    cover      = models.ImageField('img', upload_to='covers/', blank=True)      # 题图
    category   = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles', null=True) # 文章类别
    series       = models.ForeignKey(Series, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    series_order = models.PositiveSmallIntegerField('series_order', default=0, help_text='0=首位')
    is_pinned    = models.BooleanField('置顶', default=False)
    created_at = models.DateTimeField('create_time', auto_now_add=True, null=True)         # 创建时间
    updated_at = models.DateTimeField('update', auto_now=True)                  # 更新时间
    views      = models.PositiveIntegerField('num_views', default=0)            # 浏览次数

    class Meta:
        ordering = ['is_pinned', '-created_at']


    # def save(self, *args, **kwargs):
    #     # 只要有 md 就重新渲染，空 md 则留空 html
    #     import markdown
    #     if self.content_md:
    #         self.content_html = markdown.markdown(
    #             self.content_md,
    #             extensions=['fenced_code', 'codehilite', 'toc', 'tables'],
    #             safe_mode=False,
    #             enable_attributes=False
    #         )
    #     else:
    #         self.content_html = ''
    #     super().save(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        import markdown
        if self.content_md:
            # 1. 正常渲染
            html = markdown.markdown(
                self.content_md,
                extensions=['fenced_code', 'codehilite', 'toc', 'tables'],
                safe_mode=False,
                enable_attributes=False
            )

            # 2. 用 BS4 加 Layui 类
            soup = BeautifulSoup(html, 'html.parser')

            # 表格
            for table in soup.find_all('table'):
                table['class'] = table.get('class', []) + ['layui-table']

            # 代码块（markdown 产生 <pre><code class="language-xxx">）
            for pre in soup.find_all('pre'):
                # 统一换成 Layui 的 layui-code 容器
                pre['class'] = pre.get('class', []) + ['layui-code']
                # 如果想显示行号，再追加 'layui-code-line-numbers'
                # pre['class'] += ['layui-code-line-numbers']

            # 引用
            for quote in soup.find_all('blockquote'):
                quote['class'] = quote.get('class', []) + ['layui-elem-quote']

            # 图片圆角+响应
            for img in soup.find_all('img'):
                img['class'] = img.get('class', []) + ['img-radius']
                # 可加父级容器实现响应
                wrapper = soup.new_tag('div', **{'class': 'layui-fluid'})
                img.wrap(wrapper)

            self.content_html = str(soup)
        else:
            self.content_html = ''

        super().save(*args, **kwargs)


    def __str__(self):
        return self.title
    

class ArticleImage(models.Model):
    """一篇文章的附加图（支持多图）"""
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='images'                              # 反向取图时用  article.images.all()
    )
    photo = models.ImageField(upload_to='article/%Y/%m/')  # 物理路径 media/article/2025/06/xxx.png
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.article.title} - {self.photo.name}'
