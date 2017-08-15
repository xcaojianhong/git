# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/26 14:47
# @Author  : Cao jianhong
# @File    : Permission.py
# @Software: PyCharm Edu
# =================================================

from flask_principal import Permission, RoleNeed , UserNeed, identity_loaded
from flask_login import current_user

'''
# 添加授权群
# 看到一教程反过来写的，也不是到是我理解错了，还是他写错了，先试验一下
# 确实需要反过来写，理解起来比较难
reader_permission = Permission(RoleNeed('reader'))
writer_permission = Permission(RoleNeed('writer')).union(reader_permission)
editor_permission = Permission(RoleNeed('editor')).union(writer_permission)
admin_permission = Permission(RoleNeed('admin')).union(editor_permission)
su_permission = Permission(RoleNeed('su')).union(admin_permission)
'''

# 添加授权群
su_permission = Permission(RoleNeed('su'))
admin_permission = Permission(RoleNeed('admin')).union(su_permission)
editor_permission = Permission(RoleNeed('editor')).union(admin_permission)
writer_permission = Permission(RoleNeed('writer')).union(editor_permission)
reader_permission = Permission(RoleNeed('reader')).union(writer_permission)



@identity_loaded.connect # 等价与下面的写法，自动绑定当前app
# @identity_loaded.connect_via(current_app)
def on_identity_loaded(sender, identity):
        # 设置当前用户身份为login登录对象
        identity.user = current_user

        # 添加UserNeed到identity user对象
        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        # 将Role添加到identity user对象
        if hasattr(current_user, 'role'):
            identity.provides.add(RoleNeed(current_user.role))

        if hasattr(current_user, 'is_su_user') and current_user.is_su_user:
            identity.provides.add(RoleNeed('su'))


        # 把身份添加到权限里面
        identity.allow_su = su_permission.allows(identity)
        identity.allow_admin = admin_permission.allows(identity)
        identity.allow_edit = editor_permission.allows(identity)
        identity.allow_write = writer_permission.allows(identity)
        identity.allow_read = reader_permission.allows(identity)



