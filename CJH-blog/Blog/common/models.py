# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/27 19:51
# @Author  : Cao jianhong
# @File    : models.py
# @Software: PyCharm Edu
# =================================================
from Blog import db
from Blog.auth.models import User
from Blog.admin.models import Post
import markdown2
import datetime

COMMENT_STATUS = ['approved', 'pending', 'deleted']

def get_content_markdown(raw):
    # extras必须加上，不然代码块无法正常转markdown格式保存
    extras = ['code-friendly', 'fenced-code-blocks', 'tables']
    return markdown2.markdown(raw, extras=extras)

class Comment(db.Document):
    author = db.ReferenceField(User)
    post = db.ReferenceField(Post)
    guest_user = db.StringField() # 用来存匿名用户的
    raw =  db.StringField() # 正文-未加工过的正文
    content = db.StringField() # 正文
    pub_time = db.DateTimeField() # 发表时间
    update_time = db.DateTimeField() # 更新时间
    status = db.StringField(choices=COMMENT_STATUS, default='pending')

    def save(self):
        self.update_time = datetime.datetime.utcnow()
        if not self.pub_time:
            self.pub_time = datetime.datetime.utcnow()


        # raw 转 content
        self.content = get_content_markdown(self.raw)
        return super(Comment, self).save()
