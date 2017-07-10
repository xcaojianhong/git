# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/10 15:01
# @Author  : Cao jianhong
# @File    : profile.py
# @Software: PyCharm Edu
# =================================================

from flask import Blueprint, render_template

profile = Blueprint('profile', __name__)

@profile.route('/<name>')
def hello(name):
    return 'hello %s' % name
