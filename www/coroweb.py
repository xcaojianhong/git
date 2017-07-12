__author__ = 'CJH'

import asyncio
import os
import inspect
import logging
import functools

from urllib import parse
from aiohttp import web
from apis import APIError

def get(path):
    # 定义装饰器 @get(path)
    def decorator(func):
        @functools.wraps(func) # 该装饰实现warpper.__name__ = func.__name__的功能
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

def post(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

def get_required_kw_args(fn):
    args = []
    # inspect是模块是获得函数、类属性模块
    # inspect.signature(fn)获得fn的参数
    # .parameters获得一个有序的字典，key就是参数，valve是参数的信息
    # 详细可以参考http://blog.csdn.net/weixin_35955795/article/details/53053762的博文
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        # .parameters.kind 是参数的类型
        # 。parameters.default 是参数的默认直接，没有就返回.Parmeter.empty
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind ==  inspect.Parameter.KEYWORD_ONLY:
            return True

def has_Var_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True

def has_request_args(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_KEYWORD and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_POSITIONAL):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found

# 请求处理类，因为定义了__call__, 可以把RequestHandler的实例看成是函数
class RequestHandler(object):
    def __init__(self, app, fn):
        self._app = app
        self._fn = fn
        self._get_required_kw_args = get_required_kw_args(fn) # 没有默认值的关键字参数
        self._get_named_kw_args= get_named_kw_args(fn)        # 所有关键字参数
        self._has_named_kw_args = has_named_kw_args(fn)       # 是否存在关键字参数
        self._has_Var_kw_args = has_Var_kw_args(fn)           # 是否有变长字典参数
        self._has_request_args = has_request_args(fn)         # 是否有request参数

    async def __call__(self,request):
        kw = None
        if self._has_Var_kw_args or self._get_named_kw_args or self._get_required_kw_args:
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('missing content_type')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object dict')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)

            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k,v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(request.match_info)
        else:
            if not self._has_Var_kw_args and self._get_named_kw_args:
                # remove all unnamed kw
                copy = dict()
                for name in self._get_named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
                # check named arg
                for k,v in request.match_info.items():
                    if v in kw:
                        logging.warn('Duplicate arg name in named arg and kw args: %s' % k)
                    kw[k] = v

        if self._has_request_args:
            kw['request'] = request
        # check required ke
        if self._get_required_kw_args:
            for name in self._get_required_kw_args:
                if name not in kw:
                    return web.HTTPBadRequest('missing argument: %s' % name)
        logging.info('call with args :%s' %kw)

        try:
            r = await self._fn(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)


# 增加静态文件路径
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))


# 增加路由
def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @ post not defined in %s' %str(fn))
    # asyncio.iscoroutinefunction判断一个函数是否是协程，inspect.isgeneratorfunction判断函数是否为生成器
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        # 把fn函数转化成协程，这个用法未测试过，查资料没有这个用法
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' %(method , path, fn.__name__, '. '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))

def add_routes(app, module_name):
    n = module_name.rfind('.')
    if n == -1:
        # __import__ 功能同import，用来动态加载模块
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)






