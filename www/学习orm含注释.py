__author__ = '曹建洪'
# 本代码为学习案例，主要学习廖雪峰的web教程
# *****一处异步，处处异步*****

import asyncio #协程模块
import logging
import aiomysql #基于协程的mysql
# 自定义一个log函数
def log(sql,args=()):
    logging.info('SQL : %s' %sql)

# 创建链接池
async def create_pool(loop,**kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host = kw.get('host','localhost'),
        port = kw.get('port',3306), # 3306默认端口
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset','utf8'),
        autocommit = kw.get('autocommit',True),
        maaxsize = kw.get('maxsize',10),
        minsize = kw.get('minsize',1),
        loop = loop #loop参数什么用？
    )

# 封装select查询语句，select需要的参数为sql语句和sql参数
# 所有sql操作都用协程（一处异步，处处异步）
async def select(sql,args,size=None):
    log(sql,args)
    global __pool
    with await __pool as conn:
        cur =await conn.cursor(aiomysql.DictCursor) # 打开游标
        await cur.execute(sql.replace('?','%s'),args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned : %s' %len(rs))
        return rs

# 封装DELETE、UPDATE、INSERT操作语句
# 因为这三个操作的参数是一样的，因此定义一个通用的函数
# 这里写的太简单，异常情况未考虑，还需要优化
async def ececute(sql,args):
    log(sql)
    global __pool
    with await __pool as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?','%s'),args)
            affected = cur.rowcount
            await cur.close() # 因为以上操作都涉及到修改数据库，因此需要关闭游标
        except BaseException as e:
            raise
        return affected

# 根据输入的参数生成占位符列表
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)


# --*****-- 下面是orm的部分，比较难理解 --*****--

# 定义Field类型，负责保存（数据库）表的字段名字和字段类型
# 定义各种衍生的Field类
class Field(object):
    # 表的字段包括名字，类型，是否为表的主键，和默认值
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

        # 当打印（数据库表）时，输出（数据库）表的信息：类名，字段类型和名字
        def __str__(self):
            return('<%s,%s:%s>' %(self.__class__.__name__,self.column_type,self.name))

# 定义不同类型的衍生Field
# 表不同列的字段类型是不一样的

class StringField(Field):
    def __init__(self,name=None,primary_key=False,default=None,column_type='varchar(100)'):
        #调用基类的__init__，super()的作用是不用显视的调用基类的名称
        super().__init__(name,column_type,primary_key,default)

# 定义布尔类型
class BooleanField(Field):
    def __init__(self,name=None,default=None):
        super().__init__(name,'boolean',False,default)

class IntergerField(Field):
    def __init__(self,name=None,primary_key=False,default=0):
        super().__init__(name,'bigint',primary_key,default)

class FloatField(Field):
    def __init__(self,name=None,primary_key=False,default=0.0):
        super().__init__(name,'real',primary_key,default)

class TextField(Field):
    def __init__(self,name=None,default=None):
        super().__init__(name,'Text',False,default)

# 定义Model的元类，元类比较难理解
# 元类一定是继承自type
# Model继承自元类ModelMetaclass
# Model继承自元类ModelMetaclass定义了基类Model的子类实现的操作，及子类和数据库的映射关系

#

class ModelMetaclass(type):
    # __new__魔法方法控制__init__的执行，因此在__init__之前执行
    # cls 代表类自身，就像self代表实例自身一样
    # bases 代表父类的集合
    # attrs 代表类的方法的集合
    # 以上写法为惯用写法，我们遵循惯例
    def __new__(cls,name,bases,attrs):
        # 排除Model #什么意思？
        if name == 'Model':
            return type.__new__(cls,name,bases,attrs)

        # 获取table名字
        tableName = attrs.get('__table__', None) or name
        logging.info('Found model : %s (table : %s)' %(name,tableName))

        # 获取Field和主键名
        mappings = dict()
        fields = []
        primaryKey = None
        for k,v in attrs.items():
            # Field 属性
            if isinstance(v,Field):
                #此处答应的k是类的一个属性，v是这个属性在数据库中对应的Field列表属性
                logging.info('found mapping: %s ---> %s' %(k,v))
                mappings[k] =v

                # 找到了主键
                if v.primary_key:

                    #如果此时类的实例的以存在主键，说明主键重复了
                    if primaryKey:
                        raise StandardError('Duplicate primary key for Field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise StandarError('Primary key is not found')

        # 从类属性中删除Field属性，因为实例属性会覆盖类的同名属性，否则可能会造成错误
        for k in mappings.keys():
            attrs.pop(k)

        # 保存除主键外的属性名为``（与str()和repr()功能一样)的列表形式,这里什么用？
        escaped_fields = list(map(lambda f:'`%s`' %f ,fields))

        # 保存属性和列表的映射关系
        attrs['__mappings__'] = mappings
        # 保存表名
        attrs['__table__'] = tableName
        # 保存主键属性属性名
        attrs['__primary_key__'] = primaryKey
        # 保存主键外的属性名,list保存非主键
        attrs['__field__'] =fields

        # 构造默认的SELECT、INSERT、UPPDATE、DELETE语句
        #  ``反引号功能同repr()，但是py3不支持``，因此这里什么用？

        # 选择全部属性
        attrs['__select__'] = 'select `%s`, %s form `%s`' %(primaryKey,', '.join(escaped_fields),tableName)
        # 插入全部属性
        attrs['__insert__'] = 'insert into `%s` (%s,`%s`) values(%s)' %(tableName,', '.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1))
        # 更新表
        attrs['__uppdate__'] = 'uppdate `%s` set %s where `%s`=?' %(tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f),fields)),primaryKey)
        #删除表
        attrs['__delete__'] = 'delete from `%s` where `%s`=? ' %(tableName,primaryKey)
        # 获得当前类的实例，注意元类的实例也是类
        # cls为当前类的自身体
        return type.__new__(cls,name,bases,attrs)

# 定义ORM所有映射的基类：Model
# Model类的任意子类可以映射一个数据库表
# Model类可以看成是对所有数据库表操作的基本定义的映射

# 基于字典查询形式
# 因此Model拥有字典的所有功能，同时有自己定义的功能
class Model(dict,metaclass=ModelMetaclass):
    def __init__(self,**kw):
        super(Model,self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'"Model" object has no attribute: %s' %(key))

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self,key):
        # 内建函数getattr会自动处理,存在实例就返回他的key，否则就返回None
        return getattr(self,key,None)

    def getValueOrDefault(self,key):
        value = getattr(self,key,None)
        if not value:
            field = self.__mappings__[key]
            if field.default is not None:
                # 看上面field是一个属性，不是可调用的对象，因此不需要这样写，不知道有什么用意？
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %S : %S') %(key.str(value))
                setattr(self,key,vaule)
            return value

    # classmethod定义类方法
    # 类方法类自身作为第一个参数（cls）传入，从而可以用cls做一些相关的操作，并且有子类继承时，传入的是子类的cls
    @classmethod
    async def findAll(cls,where=None, args=None,**kw):
        # find objects by where clause
        sql = [cls.__select__]

        if where:
            sql.append('where') # 传入'where=条件'等号前面的where
            sql.append(where) # 传入的是等号后面的where

        if args is None:
            args = []

        orderBy = kw.get('orderBy',None)

        if orderBy:
            sql.append('order by') # 传入'order by=条件'等号前面的order by
            sql.append(orderBy) # 传入'order by=条件'等号后面的order by

        limit = kw.get('limit',None)
        if limit:
            sql.append('limit')
            if isinstance(limit,int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit,tuple) and len(limit) == 2:
                sql.append('?','?')
                sql.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s') %str(limit)
        rs = await select(' '.join(sql),args)
        return [cls(**r) for r in rs]

    @classmethod
    async def findNumber(cls,selectField,where=None,args=None):
        # find Number by select and where
        sql = ['select %s _num_ from `%s`' %(selectField,cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(selectField),args,1)
        if len(rs) == 0:
            return 0
        return rs[0]['_num_']

    @classmethod
    async def find(cls,primaryKey):
        # find object by primary key
        rs = await select('%s where `%s`=?' %s(cls.__select__,cls.__primary_key),[primaryKey],1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault,self.__field__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__,args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    async def update(self):
        args = list(map(slf.getValue,self.__field__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__,args)
        if rows != 1:
            logging.warn('failed to update by primary Key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__,args)
        if rows != 1:
            logging.warn('failed to remove by primary Kye: affected rows: %s' % rows)

if __name__ == '__main__':
    class User(Model):
        # 定义类的属性到列的映射：
        id = IntergerField('id',primary_key=True)
        name = StringField('username')
        email = StringField('email')
        password = StringField('password')

    u = User(id=12345, name='CJH', email='adadad@dada', password='password')
    print(u)
    u.save()
    print(u)

