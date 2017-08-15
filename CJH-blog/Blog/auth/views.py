# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/23 12:49
# @Author  : Cao jianhong
# @File    : views.py
# @Software: PyCharm Edu
# =================================================
import datetime, time
from flask import render_template, url_for, redirect, flash
from flask import g, current_app, request, abort, session
from flask_login import current_user
from flask.views import MethodView
from .forms import RegisterForm, LoginForm, ChangePasswordForm, ProfileForm
from .models import User
from flask_login import login_user, logout_user, login_required
from flask_principal import identity_changed, Identity, AnonymousIdentity
import Blog.Permission as permission


class RegisterView(MethodView):
    def __init__(self):
        self.form = RegisterForm()

    def get(self):
        return render_template(('auth/register.html'), form=self.form)

    def post(self):
        if self.form.validate_on_submit():
            if User.objects(username=self.form.username.data):
                flash('用户名已经存在, 请重新注册')
                return redirect(url_for('auth.register'))
            user = User()
            user.username = self.form.username.data
            user.nickname = self.form.nickname.data
            user.email = self.form.email.data
            user.password = self.form.passworld.data
            user.save()
            return redirect(url_for('auth.login'))
        # return redirect(url_for('auth.register')) #重定向无法显示验证错误
        return self.get()

class LoginView(MethodView):
    def __init__(self):
        self.form = LoginForm()

    def get(self):
        return render_template('auth/login.html', form=self.form)

    def post(self):
        if self.form.validate_on_submit():
            try:
                user = User.objects(username=self.form.username.data).first()
            except User.DoesNotExist:
                user = None

            if user and user.verify_password(self.form.password.data):
                login_user(user,self.form.remember_me.data)
                user.last_login = datetime.datetime.now
                user.last_login_stamp = str(time.time())
                user.save()

                # 登录时的身份变化
                identity_changed.send(current_app._get_current_object(),
                identity=Identity(str(user.id)))

                # flash('登录成功')

                # 官网说必须验证 next 参数的值。如果不验证的话，应用将会受到重定向的攻击。
                next = request.args.get('next')
                # if not next:
                #     return abort(400)

                return redirect(next or url_for('common.index'))
        flash('密码或者用户名错误')
        # return redirect(url_for('auth.login'))
        return self.get()

class LogoutView(MethodView):
    @login_required
    def get(self):
        logout_user()
        # session中删除flask_principal
        for key in ('identity.name', 'identity.auth_type'):
            session.pop(key, None)

        #注销后身份变成匿名
        identity_changed.send(current_app._get_current_object(),
        identity=AnonymousIdentity())
        flash('您已经登出')
        return redirect(url_for('auth.login'))

class ChangePasswordView(MethodView):
    # 相当于@login_requierd,但是对类中的函数都器作用
    decorators = [login_required]

    def __init__(self):
        self.form = ChangePasswordForm()

    def get(self):
        return render_template('auth/password.html', form=self.form)


    def post(self):
        if self.form.validate_on_submit():
            # if self.form.current_password and current_user.verify_current_password(self.form.current_password.data):
            current_user.password = self.form.new_password.data
            current_user.save()
            flash('修改密码成功')
            return redirect(url_for('auth.password'))
            # else:
            #     flash('原密码错误')
        return self.get()

class ProfileView(MethodView):
    decorators = [login_required]
    user = current_user

    def __init__(self):
        # obj=self.user是form获得当前用户的属性，可以传给前端模板渲染，没有的话就是数据就是空
        self.form = ProfileForm(obj=self.user)

    def get(self):
        form = self.form
        '''
        # 先给user添加github属性，然后在创建一个form也是可以的
        self.user.github = self.user.social_networks.get('GitHub').get('url')
        self.form = ProfileForm(obj=self.user)
        '''
        # 应为User类在数据库中没有github属性，需要单独给form表单赋值
        form.github.data = self.user.social_networks.get('GitHub').get('url')
        return render_template('auth/profile.html', form=form)

    def post(self):
        form =self.form
        if form.validate_on_submit():
            self.user.email = form.email.data
            self.user.nickname = form.nickname.data
            self.user.biography = form.biography.data
            self.user.social_networks['GitHub']['url'] = form.github.data or None
            self.user.save()
            flash('个人简介已经更新成功')
            return redirect(url_for('auth.profile'))
        return self.get()

class add_userView(MethodView):
    decorators = [login_required, permission.admin_permission.require(401)]
    user = current_user
    def __init__(self):
        self.form = RegisterForm()

    def get(self):
        # if self.user.is_su_user:
        return render_template('admin/add_user.html', form=self.form)
        # else:
        #     flash('您没有权限添加用户')
        #     return redirect(url_for('auth.index'))

    def post(self):
        # if self.user.is_su_user:
        if self.form.validate_on_submit():
            # 注意这里的user和self.user是不同的
            if User.objects(username=self.form.username.data):
                flash('用户名已经存在, 请修改用户名')
                return redirect(url_for('auth.add_user'))
            user = User()
            user.username = self.form.username.data
            user.email = self.form.email.data
            user.password = self.form.passworld.data
            user.save()
            flash('添加用户成功')
            return redirect(url_for('auth.add_user'))
        # else:
        #     flash('您没有权限添加用户')
        return self.get()


