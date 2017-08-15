# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/8/13 23:20
# @Author  : Cao jianhong
# @File    : errors.py
# @Software: PyCharm
# =================================================
from flask import render_template

def page_not_found(error):
    # return render_template('404.html'), 404
    return render_template('404.html'), 404

def handle_unauthorized(error):
    return render_template('401.html'), 401

def handle_forbidden(error):
    return render_template('403.html'), 403
