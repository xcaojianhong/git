# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/10 14:58
# @Author  : Cao jianhong
# @File    : __init__.py.py
# @Software: PyCharm Edu
# =================================================

from flask import Flask
from .views.profile import profile

app = Flask(__name__)
app.register_blueprint(profile)
