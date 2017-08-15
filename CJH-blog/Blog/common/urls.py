# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/27 19:52
# @Author  : Cao jianhong
# @File    : urls.py
# @Software: PyCharm Edu
# =================================================
from flask import Blueprint
from .views import Post_detailView, Author_detailView, IndexView, AddCommentView
from Blog import errors

site = Blueprint('common', __name__)
site.add_url_rule('/post/detail/<id>', view_func=Post_detailView.as_view('post_detail'))
site.add_url_rule('/users/<username>/', view_func=Author_detailView.as_view('author_detail'))
site.add_url_rule('/', view_func=IndexView.as_view('index'))
site.add_url_rule('/post/detail/<id>/comment', view_func=AddCommentView.as_view('add_comment'))

# site.app_errorhandler(404)(errors.page_not_found)
# site.app_errorhandler(401)(errors.handle_unauthorized)
