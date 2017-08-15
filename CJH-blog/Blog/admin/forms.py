# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/26 14:10
# @Author  : Cao jianhong
# @File    : forms.py
# @Software: PyCharm Edu
# =================================================
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, BooleanField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length
from Blog.auth import models
class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(0,128)])
    abstract = TextAreaField('摘要', validators=[Length(0,256)])
    # update_time= DateTimeField('更新时间')
    raw = TextAreaField('正文', validators=[DataRequired()])
    # author = StringField('作者')
    category = StringField('分类')
    tags_ = StringField('标签')
    # 用来在get()和post()之间传递参数
    from_draft = HiddenField('from_draft')

class RoleForm(FlaskForm):
    role = SelectField('Role', choices=models.ROLES)
