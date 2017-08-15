# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/27 19:52
# @Author  : Cao jianhong
# @File    : views.py
# @Software: PyCharm Edu
# =================================================
from flask import render_template, redirect, g, abort, request, url_for
from flask_login import current_user
from flask.views import MethodView
from Blog.auth.models import User
from Blog.admin.models import Post, PostStatistics, Tracker
from .forms import CommentForm
from .models import Comment
from Blog.Permission import reader_permission, writer_permission, editor_permission, admin_permission
from config import PER_PAGE, CJH_BLOG_SETTINGS
import uuid
import math
from mongoengine.queryset.visitor import Q

def get_base_data():
    data = {
        'blog_meta': CJH_BLOG_SETTINGS['blog_meta']
    }
    return data

class Post_detailView(MethodView):

    def get(self, id):
        form = CommentForm()
        # if not g.identity.can(reader_permission):
        #     abort(401)
        # 字段必须唯一，不然返回404错误
        post = Post.objects.get_or_404(id=id)
        # post = Post.objects(id=id).first()

        # 统计访问博客访问数据
        post_statistics = PostStatistics.objects(post=post).first()
        post_statistics.visit_count += 1
        post_statistics.save()

        tracker = Tracker()
        tracker.post = post
        tracker.ip = request.remote_addr
        tracker.user_agent = request.headers.get('User-Agent')
        tracker.save()

        comments = Comment.objects(post=post).all()
        data= get_base_data()
        data['post'] = post
        data['form'] = form
        data['comments'] = comments
        return render_template('common/post_detail.html', **data)

class Author_detailView(MethodView):
    def get(self, username):
        user = User.objects.get_or_404(username=username)
        post = Post.objects(author=user).order_by('-pub_time')
        try:
            current_page = request.args.get('page', 1, type=int)
        except:
            current_page = 1
        posts = post.paginate(page=current_page, per_page=PER_PAGE)
        total = math.ceil(len(post)/PER_PAGE)
        return render_template('common/author_detail.html', user=user, posts=posts, total=total)

class IndexView(MethodView):
    def get(self):
        post = Post.objects.order_by('-update_time')

        # page 不写道路由中，作为参数访问
        try:
            current_page = request.args.get('page', 1, type=int)
        except:
            current_page = 1

        keywords = request.args.get('keywords', None)
        category = request.args.get('category', None)
        tag = request.args.get('tag', None)
        # 全文搜索
        if keywords:
            post = post.filter(Q(raw__contains=keywords) | Q(title__contains=keywords) | Q(abstract__contains=keywords))
        if category:
            post = post.filter(category=category)
        if tag:
            post = post.filter(tags=tag)

        # 聚合分组操作，aggregate
        category_zu=[
            {'$group':
                 {'_id': {'category': '$category'}, #
                  'name': {'$first': '$category'}, # $first，获取第一个文档数据
                  'count': {'$sum': 1}, # $sum，求和
                  }
             }
        ]
        # 这里的_get_collection是受保护对象
        # category_group = Post._get_collection().aggregate(category_zu)
        category_group = Post.objects.aggregate(*category_zu) # 与上面等价
        tags = Post.objects.all().distinct('tags')
        # paginate能实现分页显示
        posts = post.paginate(page=current_page, per_page=PER_PAGE)
        total = math.ceil(len(post)/PER_PAGE)

        post_statistics = PostStatistics.objects.order_by('-visit_count')[:10]

        data = get_base_data()
        data['posts'] = posts
        data['total'] = total
        data['cur_category'] = category
        data['cur_tag'] = tag
        data['keywords'] = keywords
        data['category_group'] = category_group
        data['tags'] = tags
        data['post_statistics'] = post_statistics
        return render_template('common/index.html', **data)

class AddCommentView(MethodView):
    def post(self, id):
        form = CommentForm()
        if form.validate_on_submit():
            comment = Comment()
            comment.raw = form.raw.data
            # comment.author = User.objects(username=current_user.get('username', None)).first() or None
            comment.post = Post.objects.get_or_404(id=id)
            if not current_user.get_id():
                comment.guest_user = '游客%s' % uuid.uuid1()
                comment.author = None
            else:
                comment.author = User.objects(id=current_user.get_id()).first()
            comment.save()
        return redirect(url_for('common.post_detail', id=id))

