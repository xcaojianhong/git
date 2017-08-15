# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/23 12:49
# @Author  : Cao jianhong
# @File    : urls.py
# @Software: PyCharm Edu
# =================================================
from flask import Blueprint
from .views import (RegisterView, LoginView, LogoutView, ChangePasswordView, ProfileView, add_userView)

site = Blueprint('auth', __name__)
site.add_url_rule('/register', view_func=RegisterView.as_view('register'))
site.add_url_rule('/login', view_func=LoginView.as_view('login'))
site.add_url_rule('/logout', view_func=LogoutView.as_view('logout'))
site.add_url_rule('/password', view_func=ChangePasswordView.as_view('password'))
site.add_url_rule('/profile',view_func=ProfileView.as_view('profile'))
site.add_url_rule('/add_user', view_func=add_userView.as_view('add_user'))

# @site.route('/test')
# @login_required
# def test():
#     return 'test logged or not'
