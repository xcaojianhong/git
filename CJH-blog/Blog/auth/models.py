# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/23 15:31
# @Author  : Cao jianhong
# @File    : models.py
# @Software: PyCharm Edu
# =================================================
import datetime, time
from flask_login import UserMixin
# 用来处理密码加密 加盐哈希方法
from werkzeug.security import generate_password_hash, check_password_hash
from Blog import db
from Blog import login_manager
from flask_login import current_user

SOCIAL_NETWORKS = {'GitHub':{'url':None}}
ROLES = (('su','su'),
            ('admin', 'admin'),
            ('editor', 'editor'),
            ('writer', 'writer'),
            ('reader', 'reader'))


# 继承了UserMixin，使其获得了is_active()等方法，用flask_login必要
class User(UserMixin,db.Document):
    username = db.StringField(max_length=255, required=True, unique=True) #用户名
    is_su_user = db.BooleanField(default=False) # 是否是superuser
    email = db.EmailField(max_length=255, required=True) # 邮件
    password_hash = db.StringField(required=True) # 密加密码
    nickname = db.StringField(max_length=255, default=None) #昵称
    biography = db.StringField() # 作者简介
    role = db.StringField(max_length=64, default='reader', choices=ROLES) # 权限
    create_time = db.DateTimeField(default=datetime.datetime.now, required=True) # 创建时间
    create_time_stamp = db.StringField(default=str(time.time()), required=True)  # 创建时间-时间戳格式
    last_login = db.DateTimeField(default=datetime.datetime.now, required=True) # 最后登录时间
    last_login_stamp = db.StringField(default=str(time.time()), required=True)  # 最后登录时间-时间戳格式
    social_networks = db.DictField(default=SOCIAL_NETWORKS) # 社交网站

    # property装饰器实现passworld到passworld_hash的转化
    @property
    def password(self):
        raise AttributeError('密码无法直接访问')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    # 定义检验密码是否正确的函数verify_password
    def verify_password(self,password):
        return check_password_hash(self.password_hash, password)

    # 修改密码的时候检验原密码是否正确
    def verify_current_password(self, password):
        return self.verify_password(password)


    def get_id(self):
        try:
            # return self.username
            # print(type(self.id))
            return str(self.id)
        except:
            return None

@login_manager.user_loader
def load_user(id):
    try:
        user = User.objects(id=id).first()
    except User.DoesNotExist:
        user = None
    return user

