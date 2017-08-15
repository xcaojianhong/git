# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/22 10:14
# @Author  : Cao jianhong
# @File    : __init__.py
# @Software: PyCharm Edu
# =================================================

import os

from flask import Flask
from flask_login import LoginManager
from flask_mongoengine import MongoEngine
# 引入权限管理插件，和flask_login配合
from flask_principal import Principal
# 时间本地话的模块
from flask_moment import Moment

# 初始化数据库
db = MongoEngine()

# 使用 Flask-Login 的应用，最重要的部分就是 LoginManager 类，初始化
login_manager = LoginManager()
principal = Principal()
moment = Moment()

# 设置安全等级
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message = '您未登录,请先登录'

def create_app(config):
    # 指定templates和static的路径
    templates = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, 'templates'))
    static = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, 'static'))
    print(templates)
    app = Flask(__name__, template_folder=templates, static_folder=static)
    # 指定配置文件
    app.config.from_object(config)

    db.init_app(app)
    login_manager.init_app(app)
    principal.init_app(app)
    moment.init_app(app)

    # 注册app应用路由
    register(app)

    return app


# 蓝图必须在创建app之后导入，放在文件开头会发生循环导入的问题
from Blog.auth.urls import site as auth_site
from Blog.admin.urls import site as admin_site
from Blog.common.urls import site as common_site
def register(app):
    app.register_blueprint(auth_site, url_prefix='/auth')
    app.register_blueprint(admin_site, url_prefix='/admin')
    app.register_blueprint(common_site)


