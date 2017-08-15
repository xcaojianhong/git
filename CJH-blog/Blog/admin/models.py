# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/26 14:10
# @Author  : Cao jianhong
# @File    : models.py
# @Software: PyCharm Edu
# =================================================
import datetime
from Blog import db
from Blog.auth.models import User
import markdown2

def get_content_markdown(raw):
    # extras必须加上，不然代码块无法正常转markdown格式保存
    extras = ['code-friendly', 'fenced-code-blocks', 'tables']
    return markdown2.markdown(raw, extras=extras)

class Post(db.Document):
    title = db.StringField(max_length=255, required=True) # 标题
    abstract = db.StringField() # 摘要
    pub_time = db.DateTimeField(default=datetime.datetime.now) # 创建时间
    update_time= db.DateTimeField() # 更新时间
    raw = db.StringField(required=True) # 正文-未加工过的正文
    content = db.StringField(required=True) # 正文
    author = db.ReferenceField(User) # 这里的author指向User
    category = db.StringField(max_length=64) # 分类
    tags = db.ListField(db.StringField(max_length=32)) # 标签
    is_draft = db.BooleanField(default=False) # 是否存有草稿

    # post_type = db.StringField(max_length=64, default='post')

    # 自定义save()
    def save(self):
        self.update_time = datetime.datetime.utcnow()
        if not self.pub_time:
            self.pub_time = datetime.datetime.utcnow()

        # raw 转 content
        self.content = get_content_markdown(self.raw)
        return super(Post, self).save()

class Draft(db.Document):
    title = db.StringField(max_length=255, required=True)  # 标题
    abstract = db.StringField()  # 摘要
    pub_time = db.DateTimeField(default=datetime.datetime.now)  # 创建时间
    update_time = db.DateTimeField()  # 更新时间
    raw = db.StringField(required=True)  # 正文-未加工过的正文
    content = db.StringField(required=True)  # 正文
    author = db.ReferenceField(User)  # 这里的author指向User
    category = db.StringField(max_length=64)  # 分类
    tags = db.ListField(db.StringField(max_length=32))  # 标签
    is_draft = db.BooleanField(default=True)  # 是否存有草稿
    post = db.ReferenceField(Post) # 指向Post

    # 自定义save()
    def save(self):
        self.update_time = datetime.datetime.utcnow()
        if not self.pub_time:
            self.pub_time = datetime.datetime.utcnow()

        # raw 转 content
        self.content = get_content_markdown(self.raw)
        return super(Draft, self).save()

# 统计博客的访问数据
class PostStatistics(db.Document):
    post = db.ReferenceField(Post)
    visit_count = db.IntField(default=0)
    verbose_count_base = db.IntField(default=0)

# 跟踪访问博客的具体数据
class Tracker(db.Document):
    post = db.ReferenceField(Post)
    ip = db.StringField()
    user_agent = db.StringField()
    create_time = db.DateTimeField()

    def save(self):
        if not self.create_time:
            self.create_time = datetime.datetime.utcnow()
        return super(Tracker, self).save()


