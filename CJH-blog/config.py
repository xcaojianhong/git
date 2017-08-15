# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/22 10:27
# @Author  : Cao jianhong
# @File    : config.py
# @Software: PyCharm Edu
# =================================================
import os

MONGODB_SETTINGS = {'DB':'XCJ_blog'}
SECRET_KEY = 'you-will-never-guess'

# 每页的博客数
PER_PAGE =3


CJH_BLOG_SETTINGS={
    'blog_meta':{
        'title': 'CJH Blog',
        'name':'CJH Blog',
        'author': '曹建洪',
        'description': '知识是有力量的！',
        'keywords': 'python, flask, MongoDB',
        'copyright': 'Copyright © CJH Blog 2017',
        'generator': 'Flask',
        'google_site_verification': os.environ.get('google_site_verification') or 'cjh123456',
        'baidu_site_verification': os.environ.get('baidu_site_verification') or 'cjh123456',
        'sogou_site_verification': os.environ.get('sogou_site_verification') or 'cjh123456',
    }
}
