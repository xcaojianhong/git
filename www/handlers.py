from coroweb import get, post
from aiohttp import web
import time
import json
from apis import APIError, APIValueError, APIResourceNotFoundError, APIPermissionError
from models import User, Comment, Blog, next_id
from markdown2 import markdown
from apis import Page
import hashlib
from aiohttp import web
from config import configs
import logging
import re
__author__ = 'CJH'

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.serect

def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p

def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        # 过期时间小于当前时间，返回None
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if User is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None



# url handlers

# 访问首页
@get('/')
async def index(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    page = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = await Blog.findall(orderBy='created_at',limit=(page.offset, page.limit))

    return {
        '__template__': 'blogs.html',
        'blogs': blogs,
        'page': page,
    }

# 访问博客详情
@get('/blog/{id}')
async def blog(id):
    blog = await Blog.find(id)
    comments = await Comment.findall('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown(blog.content)
    return {
        '__template__':'blog.html',
        'blog':blog,
        'comments':comments
    }

# 修改博客
@get('/manage/blogs/edit')
async def manage_edit_blog(*, id):
    return{
        '__template__':'manage_blog_edit.html',
        'id':id,
        'action':'/api/blogs/%s' % id
    }

# 管理评论
@get('/manage/comments')
async def manage_conments(*, page='1'):
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }

# 管理用户
@get('/manage/users')
async def manage_users(*, page='1'):
    return {
        '__template__':'manage_users.html',
        'page_index':get_page_index(page)
    }


@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name, user_image=user.image, content=content.strip())
    await comment.save()
    return comment

'''
@get('/api/users')
async def api_get_users():
    users = await User.findall(orderBy='created_at desc')
    for u in users:
        u.passwd = '******'
    return dict(users=users)
'''
@get('/register')
async def register():
    return{
        '__template__': 'register.html',
    }

@get('/signin')
async def signin():
    return{
        '__template__': 'signin.html',
    }

# email和哈希码的规则
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise  APIValueError('passwd')
    users = await User.findall('email=?', [email])
    if len(users):
        raise APIValueError('register:failed', 'email', 'Email is already in use.')
    uuid = next_id()
    sha1_password = '%s:%s' % (uuid, passwd)
    user = User(id=uuid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_password.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email')
    if not passwd:
        raise APIValueError('passwd', 'Invalid passwd')
    Users = await User.findall('email=?', [email])
    if len(Users) == 0:
        raise APIValueError('email', 'email not exist')
    user = Users[0]

    # check passwd
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid passwd')

    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }

# 管理博客
@get('/manage/blogs')
def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }

@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    blog = await Blog.find(id)
    return blog

@post('/api/blogs')
async def create_blog(request, *, name, summary, content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content connot be empty')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog

# 修改博客api
@post('/api/blogs/{id}')
async def api_update_blog(id, request, *, name, summary, content):
    check_admin(request)
    blog = await Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content connot be empty')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog

# 删除博客
@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
    check_admin(request)
    blog = await Blog.find(id)
    await blog.remove()
    return dict(id=id)

# 删除评论
@post('/api/comments/{id}/delete')
async def api_delete_comments(request, *, id):
    check_admin(request)
    comment = await Comment.find(id)
    await comment.remove()
    return dict(id=id)


# 获得博客的api
@get('/api/blogs')
async def aip_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findall(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p,blogs=blogs)

# 获得评论的api
@get('/api/comments')
async def api_comments(*, page='1'):
    page_index = get_page_index(page)
    num = await Comment.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findall(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p,comments=comments)

# 获得用户的api
@get('/api/users')
async def api_users(*, page='1'):
    page_index = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = await User.findall(orderBy='created_at desc', limit=(p.offset, p.limit))
    for uer in users:
        uer.passwd = '******'
    return dict(page=p, users=users)
