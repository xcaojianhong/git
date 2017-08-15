# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/23 12:49
# @Author  : Cao jianhong
# @File    : forms.py
# @Software: PyCharm Edu
# =================================================
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
# wtforms.validators 内置了很多验证器，主要用来验证输入的字符串的
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, URL, Optional, ValidationError
from flask_login import current_user
msg={
        'username_D':'用户名不能为空',
        'username_L':'用户名不能少于4个字符',
        'nickname_D':'昵称不能为空',
        'nickname_L':'昵称不能少于1个字符',
        'email_D':'邮件不能为空',
        'email_E':'请输入合法的邮件',
        'password_D':'密码不能为空',
        'password_L':'密码不能少于6位'
    }

class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(message=msg['username_D']),Length(4,64,message=msg['username_L']),
                           Regexp('^[A-Za-z0-9_.]*$', 0, '只能输入字母，数字和下划线')])
    nickname = StringField('昵称')
    email = StringField('邮件', validators=[DataRequired(message=msg['email_D']), Email(message=msg['email_E'])])
    passworld = PasswordField('密码', validators=[DataRequired(message=msg['password_D']), Length(6,64,message=msg['password_L']),
                            EqualTo('passworld2', message='请保证两次输入的密码一致')])
    passworld2 = PasswordField('确认密码', validators=[DataRequired(message=msg['password_L'])])


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(message=msg['username_D'])])
    password = PasswordField('密码', validators=[DataRequired(message=msg['username_L'])])
    remember_me = BooleanField('保持登录')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('原密码', validators=[DataRequired(message=msg['password_D'])])
    new_password = PasswordField('新密码', validators=[DataRequired(message=msg['password_D']),Length(6,64, message=msg['password_L']),
                            EqualTo('new_password2', message='请保证两次输入的密码一致')])
    new_password2 = PasswordField('确认密码', validators=[DataRequired(message=msg['password_D'])])

    # 'validate_' + '字段名'会在views中调用validate_on_submit()的时候自动执行，字段名必须正确
    # 参数current_password可以替换成任何名称
    def validate_current_password(self, current_password):
        if not current_user.verify_current_password(current_password.data):
            raise ValidationError('原密码错误')

class ProfileForm(FlaskForm):
    email = StringField('邮件', validators=[DataRequired(message=msg['email_D']), Email(message=msg['email_E'])])
    nickname = StringField('昵称', validators=[DataRequired(message=msg['nickname_D']), Length(1,128, message=msg['nickname_L'])])
    biography = StringField('作者简介')
    github = StringField('github', validators=[URL(message='请填入合法的url')])
