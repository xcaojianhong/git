import logging;logging.basicConfig(level=logging.INFO) #此部分还未学习，照搬

import asyncio
import os
import json
import time
from datetime import datetime
from aiohttp import web

import orm # 测试
from models import User, Blog, Comment # 测试

def index(requset):
    return web.Response(body=b'<h1>Welecome Guys', content_type='text/html', charset='UTF-8')

async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET','/',index)
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()

async def test():
    await orm.create_pool(loop=loop, host='localhost', port=3306, charset='utf8', user='root', password='password', db='awesome')
    u = User(id='11', name='Test', email='test3@example.com', passwd='1234567890', image='about:blank')
    await u.save()

loop.run_until_complete(test())
loop.close()


'''import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

def index(request):
    return web.Response(body=b'<h1>Awesome</h1>', content_type='text/html', charset='UTF-8')

@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
'''
