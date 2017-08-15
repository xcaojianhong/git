# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/26 14:11
# @Author  : Cao jianhong
# @File    : views.py
# @Software: PyCharm Edu
# =================================================


from flask import render_template, redirect, flash, request, url_for, g, abort
from flask_login import current_user, login_required
from flask.views import MethodView
import Blog.Permission as permission
from Blog.Permission import reader_permission, writer_permission, editor_permission, admin_permission, su_permission
from config import PER_PAGE

from .forms import PostForm, RoleForm
from Blog.auth.models import User
from Blog.common.models import Comment
from .models import Post, Draft, PostStatistics, Tracker
import math

class AdminIndexView(MethodView):
    decorators = [login_required]
    user = current_user
    def get(self):
        return render_template('admin/index.html', user=self.user)

class AddPostView(MethodView):
    decorators = [login_required, permission.writer_permission.require(401)]
    # get()和post()不能公用类属性，猜测可能是每次访问的时候都会实例化一个类
    # from_draft =False
    # g.from_draft = False
    # g.user = current_user
    def __init__(self):
        self.form = PostForm()
        # mongodb 的distinct去重
        self.categorys = Post.objects.all().distinct('category')
        self.tags = Post.objects.all().distinct('tags')
        self.data={
            'form': self.form,
            'categorys': self.categorys,
            'tags': self.tags,
        }

    def get(self, id=None):
        if not id:
            return render_template('admin/post.html', **self.data)
        else:
            # get 方法和Draft.objects(id=id).first() 方法不同，get方法当id不存在会报错，first()方法返回None
            # post = Draft.objects.get(id=id)
            post = Draft.objects(id=id).first() or Draft.objects(post=Post.objects(id=id).first()).first()
            if not post:
                post = Post.objects(id=id).first()
            else:
                # 通过前端传递给post()
                post.from_draft = True
                # g.from_draft = True
                # self.from_draft = True
            # 验证该文章是否是本人，否则返货401
            if str(post.author.id) != current_user.get_id():
                abort(401)

            post.tags_ = ', '.join(post.tags)
            self.form = PostForm(obj=post)
            self.data['form'] = self.form
            return render_template('admin/post.html', **self.data)

    def post(self, id=None):
        if request.form.get('publish') and not id:
            post = Post()
        elif request.form.get('draft') and not id:
            post = Draft()
        elif request.form.get('publish') and id:
            post = Post.objects(id=id).first()
            if not post:
                post = Post()
        elif request.form.get('draft') and not id:
            post = Draft.objects(id=id).first() or Draft.objects(post=Post.objects(id=id).first()).first()
            if not post:
                post = Draft()
        if self.form.validate_on_submit():
            if request.form.get('draft'):
                post.title = self.form.title.data
                post.abstract =self.form.abstract.data
                post.raw = self.form.raw.data
                post.author = User.objects(id=current_user.get_id()).first()
                post.category = self.form.category.data
                post.tags = [tag.strip() for tag in self.form.tags_.data.split(',')]
                if id:
                    post.post = Post.objects(id=id).first()
                post.save()
            if request.form.get('publish'):
                post.title = self.form.title.data
                post.abstract = self.form.abstract.data
                post.raw = self.form.raw.data
                post.author = User.objects(id=current_user.get_id()).first()
                post.category = self.form.category.data
                post.tags = [tag.strip() for tag in self.form.tags_.data.split(',')]
                post.save()
            # 创建博客统计表
            if request.form.get('publish') and post.id != id :
                post_statistics = PostStatistics()
                post_statistics.post = post
                post_statistics.save()
                tracker = Tracker()
                tracker.post = post
                tracker.save()

            if request.form.get('publish') and self.form.from_draft.data:
                draft = Draft.objects(id=id).first() or Draft.objects(post=Post.objects(id=id).first()).first()
                draft.delete()
                return redirect(url_for('common.post_detail', id=post.id))
            elif request.form.get('publish'):
                return redirect(url_for('common.post_detail', id=post.id))
            elif not id and request.form.get('draft'):
                return redirect(url_for('admin.add_post'))
            return self.get()
        return self.get()

class DelPostView(MethodView):
    decorators = [login_required, permission.admin_permission.require(401)]

    def delete(self, id):
        if request.args.get('is_draft') == 'false':
            post = Post.objects(id=id).first()
            # 删除post 需要删除他的评论和统计数据
            Comment.objects(post=post).all().delete()
            PostStatistics.objects(post=post).all().delete()
            Tracker.objects(post=post).all().delete()
        elif request.args.get('is_draft') == 'true':
            post = Draft.objects(id=id).first()
        else:
            return redirect(url_for('common.index'))
        post.delete()
        if request.args.get('ajax'):
            return 'success'
        if request.args.get('is_draft') == 'false':
            return redirect(url_for('admin.posts'))
        else:
            return redirect(url_for('admin.drafts'))

class PostListview(MethodView):
    decorators = [login_required]
    def __init__(self):
        self.post = Post.objects.order_by('-update_time')

    def get(self):
        post = self.post
        if g.identity.can(admin_permission):
            post = self.post
        else:
            post = self.post.filter(author=User.objects(id=current_user.get_id()).first())

        # page 不写道路由中，作为参数访问
        try:
            current_page = request.args.get('page', 1, type=int)
        except:
            current_page = 1

        # paginate能实现分页显示
        posts = post.paginate(page=current_page, per_page=PER_PAGE)

        total = math.ceil(len(post) / PER_PAGE)

        return render_template('admin/posts.html', posts=posts, total=total)

class DraftListView(PostListview):
    decorators = [login_required]
    def __init__(self):
        self.post = Draft.objects.order_by('-update_time')

    def get(self):
        post = self.post
        if g.identity.can(admin_permission):
            post = self.post
        else:
            post = self.post.filter(author=User.objects(id=current_user.get_id()).first())

        try:
            current_page = request.args.get('page', 1, type=int)
        except:
            current_page = 1

        posts = post.paginate(page=current_page, per_page=PER_PAGE)

        total = math.ceil(len(post) / PER_PAGE)

        return render_template('admin/posts.html', posts=posts, is_draft=True, total=total)

class UsersView(MethodView):
    decorators = [login_required, permission.admin_permission.require(401)]
    def get(self):
        user = User.objects.all()
        try:
            current_page = request.args.get('page', 1, type=int)
        except:
            current_page = 1
        users = user.paginate(page=current_page, per_page=PER_PAGE)
        total = math.ceil(len(user) / PER_PAGE)

        return render_template('admin/users.html', users=users, total=total)

class ChangeRoleView(MethodView):
    decorators = [login_required, permission.admin_permission.require(401)]

    def __init__(self):
        self.form = RoleForm()

    def get(self, username):
        user = User.objects(username=username).first()
        data = {'user':user}
        data['form'] = self.form
        return render_template('admin/role.html', **data)

    def post(self, username):
        user = User.objects(username=username).first()
        if self.form.validate_on_submit():
            user.role = self.form.role.data
            user.save()
            flash('修改权限成功')
            return redirect(url_for('admin.role', username=username))
        return self.get(username)

class DelUserView(MethodView):
    decorators = [login_required, permission.admin_permission.require(401)]
    def delete(self, username):
        user = User.objects(username=username).first()

        # 删除 user 指向它的 post 和 comment 都需要修改
        posts = Post.objects(author=user).all()
        if posts:
            for post in posts:
                post.author = None
                post.save()

        commemts = Comment.objects(author=user).all()
        if commemts:
            for comment in commemts:
                comment.author = None
                comment.save()

        user.delete()
        if request.args.get('ajax'):
            return 'success'
        return redirect(url_for('admin.users'))

class CommentView(MethodView):
    decorators = [login_required, permission.admin_permission.require(401)]
    def __init__(self):
        self.comment = Comment.objects.order_by('-update_time')

    def get(self):
        try:
            current_page = request.args.get('page', 1, type=int)
        except:
            current_page = 1

        comments = self.comment.paginate(page=current_page, per_page=PER_PAGE)
        total = math.ceil(len(self.comment)/PER_PAGE)

        data = {'comments':comments,
                'total':total}
        return render_template('admin/comments.html', **data)

    def delete(self):
        id = request.args.get('id', None)
        if id:
            comment = Comment.objects.get_or_404(id=id)
            comment.delete()

        if request.args.get('ajax'):
            return 'success'

        return redirect(url_for('admin.comments'))



