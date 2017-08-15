# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/27 19:51
# @Author  : Cao jianhong
# @File    : forms.py
# @Software: PyCharm Edu
# =================================================
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length

class CommentForm(FlaskForm):
    raw = TextAreaField('评论', validators=[DataRequired()])

