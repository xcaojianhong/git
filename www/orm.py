__author__ = 'CaoJianhong'

# 基于协程的自定义orm框架
# ***一处协程，处处协程***

'''
本orm选择MySQL最为网站的后台数据库
执行SQL语句进行操作数据库，并将常用SELECT、INSERT等语句进行函数封装
在异步框架的基础上，采用aiomysql作为数据库的异步io驱动
将数据库中表的操作，映射成一个类的操作，也就是数据库表的一行映射成一个对象（orm）
orm：object relation mappings
整个orm操作也是异步操作

# __*__整体思路__*__
    如何定义一个user类，这个类和数据库中的表User构成映射关系，二者应该关联起来，对User类的操作映射成对数据库表的User表的SQL操作
    通过Field类将user类的属性映射到User表的列，其中每一列的字段又有自身的属性：数据的类型，列名，主键和默认值
'''


import asyncio # 导入协程模块
import logging # 导入日子模块，方面调试代码
import aiomysql # 导入基于协程的mysql驱动

def log(sql,args=()):
    logging.info('SQL: %s' % (sql)) #测试控制台无法输出info级别的logging，有什么用？



async def create_pool(loop, **kw):
    logging.info('creat database connection pool ...')

    global __pool
    __pool = await aiomysql.create_pool(
        # **kw参数包含所以连接需要用到的关键字参数
        # 默认为本机的ip localhost
        # 默认端口为3306
        # 默认开启自动连接
        # 默认的最大的连接数为10，最小的连接数为1
        host = kw.get('host','localhost'),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        port = kw.get('port',3306),
        charset = kw.get('charset','utf8'),
        autocommit = kw.get('autocommit',True),
        maxsize = kw.get('maxsize',10),
        minsize = kw.get('minszie',1),

        # 接收一个event_loop实例
        loop = loop
    )

# 封装SELECT SQL语句为select函数
# SELECT 语句的标准语法 select * from *
async def select(sql, args, size=None):
    # 调用自定义的日志函数log（）
    log(sql,args)
    global __pool

    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 执行SQL语句
            # SQL的占位符为？，MySQL的占位符为%
            await cur.execute(sql.replace('?', '%s'), args or ())

            # 根据指定的size，返回查询的结果
            if size:
                # 返回size条查询的结果
                rs = await cur.fetchmany(size)
            else:
                # 返回全部的查询结果
                rs = await cur.fetchall()
        logging.info('rows return: %s' % (len(rs)))
        return rs

# 封装 INSETRT，UPDATE，DELETE
# 语句操作的参数一样，所用定义一个通用的函数
# 返回操作影响的行号
async def execute(sql,args,autocommit=True):
    log(sql,args)
    global __pool
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace('?', '%s'), args)
                # 返回操作的行数
                affectedLine = cur.rowcount
                if not autocommit:
                    # 提交数据库连接
                    await cur.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
        return affectedLine

# 根据输入的参数生成占位符列表
def create_args_srting(num):
    L = []
    for u in range(num):
        L.append('?')

    # 以','为分隔符号，将列表合成字符串
    return ','.join(L)

# 定义Field类，负责保存（数据库）表的字段名和字段类型
class Field(object):
    # 表的字段包含名字、类型、是否为主键和默认值
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    # 当打印（数据库）表时，输出（数据库）表的信息：类名，字段类型和名字
    def __str__(self):
        return ('<%s, %s, %s>' % (self.__class__.__name__, self.column_type, self.name))

# 定义不同类型的衍生Field类
# 数据库不同列的数据类型不同

class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, column_type='Varchar(100)'):
        super(StringField, self).__init__(name, column_type, primary_key, default)

class BooleanField(Field):
    def __init__(self, name=None, primary_key=False, default=False):
        super(BooleanField, self).__init__(name,'boolean',primary_key,default)

class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super(IntegerField, self).__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super(FloatField, self).__init__(name, 'real', primary_key, default)

class TextField(Field):
    def __init__(self, name=None, primary_key=False, default=None):
        super(TextField, self).__init__(name, 'Text', primary_key, default)


# 定义Model的元类ModelMetaclass

# 所有的元类都继承自type
# ModelMetaclass的工作是一个数据库的操作映射成一个python的类



class ModelMetaclass(type):
    # __new__方法控制__init__方法的实现，在穿件类的时候实现
    # cls:代表类本身
    # bases：代表继承父类的集合
    # attrs: 代表类方法的合集

    # 固定写法，用别的参数代替也行
    def __new__(cls, name, bases, attrs):

        # 排除Model
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)

        # 获取table名词,如果有__table__属性就调用，没有就用类名
        tablename = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name,tablename))

        # 获得Field和主键名
        mappings = dict() # 创建一个空字典，用来存放数据库列和类属性的对应关系
        fields = []
        primaryKey = None

        for k,v in attrs.items():
            # k代表类 属性的名称(字符串)，v代表对应的Field属性
            if isinstance(v ,Field):
                logging.info('found mappings: %s ---> %s' % (k,v))
                mappings[k] = v # 保存列和属性的映射关系

                # 找到主键，
                if v.primary_key:

                    # 如果此时类的实例已经存在主键，说明主键重复了
                    if primaryKey:
                        raise StandardError('DUPlicate primary key for field: %s' % k)
                    primaryKey = k # 保存主键名
                else:
                    fields.append(k) # 保存非主键名
        if not primaryKey:
            raise StandardError('primary key not fount')

        # 从类属性中删除Field属性，避免与实例属性重名
        for k in mappings.keys():
            attrs.pop(k)

        # 保存除主键外的属性名为``(运算处字符串，SQL语句中要求)列表形式
        escaped_fields = list(map(lambda f:'`%s`' %f, fields))

        # 保存类属性和数据库列的映射关系
        attrs['__mappings__'] = mappings
        # 保存表名
        attrs['__table__'] = tablename
        # 保存主键名
        attrs['__primary_key__'] = primaryKey
        # 保存除主键外的属性名
        attrs['__fields__'] = fields

        # 够着默认的SELECT、INSERT、UPDATE、DELETE语句
        # ``反引号在SQL中有用，转化为字符串的意思
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tablename)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values(%s)' % (tablename, ', '.join(escaped_fields), primaryKey, create_args_srting(len(escaped_fields)+1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tablename, ', '.join(map(lambda f:'`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tablename, primaryKey)
        return type.__new__(cls, name, bases, attrs)

# 定义了ORM所有映射的基类：Model
# Model 类的人员子类可以映射一个数据库表
# Model 类可以看作是对所有数据库表操作的基本定义的映射关系

# Model基于字典查询形式
# Model类从dict继承，拥有字典的所有功能，同时自定义了特使方法__getattr__和__setattr__，能够实现属性操作
# 实现数据库的操作的所有方法，定义为class方法，所有继承子Model的类都具有数据库操作方法

class Model(dict, metaclass=ModelMetaclass):
    def __init__(self,**kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'"Model" object has no attribute: %s' % key)

    def __setattr__(self, key, value):
        self[key] =value

    def getValue(self, key):
        # 函数会自定执行__getattr__
        return getattr(self, key, None)

    def getVauleOrDefault(self,key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    # classmethod 是方法变成类方法
    async def findall(cls, where=None, args=None, **kw):
        sql = [cls.__select__]

        if where:
            sql.append('where')
            sql.append(where)

        if args is None:
            args = []

        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)

        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?,?')
                args.extend(limit) # 合并args和limit
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs] # #返回cls类的一个实例,初始化的参数是r

    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        sql = ['select %s __num__ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args , 1)
        if len(rs) == 0:
            return None
        return rs[0]['__num__']

    @classmethod
    async def find(cls, primaryKey):
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), primaryKey, 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0]) #返回cls类的一个实例,初始化的参数是rs[0]

    async def save(self):
        args = list(map(self.getVauleOrDefault, self.__fields__)) #args 所有非主键的属性
        args.append(self.getVauleOrDefault(self.__primary_key__)) # args 添加主键属性
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows !=1:
            logging.warn('failed to remove by primayr key: affected rows: %s' % rows)


if __name__ == '__main__':
    class User(Model):
        # 定义类的属性到列的映射：
        id66 = IntegerField('id',primary_key=True)
        name = StringField('name')
        email = StringField('emali')
        password = StringField('password')

    u = User(id=12345, name='CJH', email='xacoajinhong@gmail.com', password='password')
    print(u)
    u.save()
    print(u)
