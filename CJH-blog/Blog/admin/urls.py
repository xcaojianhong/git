# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/26 14:11
# @Author  : Cao jianhong
# @File    : urls.py
# @Software: PyCharm Edu
# =================================================
from flask import Blueprint
from .views import (AdminIndexView, AddPostView, PostListview, DraftListView, UsersView, ChangeRoleView,
                    DelUserView, DelPostView, CommentView)
from Blog import errors

site = Blueprint('admin', __name__)
site.add_url_rule('/', view_func=AdminIndexView.as_view('index'))
site.add_url_rule('/add_post', view_func=AddPostView.as_view('add_post'))
site.add_url_rule('/edit_post/<id>', view_func=AddPostView.as_view('edit_post'))
site.add_url_rule('/posts/', view_func=PostListview.as_view('posts'))
site.add_url_rule('/posts/drafts/', view_func=DraftListView.as_view('drafts'))
site.add_url_rule('/users/', view_func=UsersView.as_view('users'))
site.add_url_rule('/change-role/<username>', view_func=ChangeRoleView.as_view('role'))
site.add_url_rule('/user/<username>/delete', view_func=DelUserView.as_view('user_delete'))
site.add_url_rule('/post/<id>/delete', view_func=DelPostView.as_view('post_delete'))
site.add_url_rule('/posts/comments/', view_func=CommentView.as_view('comments'))


site.app_errorhandler(404)(errors.page_not_found)
site.app_errorhandler(401)(errors.handle_unauthorized)

