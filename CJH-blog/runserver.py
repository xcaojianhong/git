# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =================================================
# @Time    : 2017/7/22 10:15
# @Author  : Cao jianhong
# @File    : runserver.py
# @Software: PyCharm Edu
# =================================================
from Blog import create_app

# 创建应用对象
app = create_app('config')

if __name__ == '__main__':
    app.run(debug=True)
