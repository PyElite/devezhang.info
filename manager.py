"""
from config import Config
import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
"""
import logging

from flask import current_app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from info import create_app, db

"""
大致框架：
1、创建配置类Config：MySQL/redis/session三大配置信息
2、注册配置/开启CSRF保护/绑定Session
3、实例MySQL连接对象/redis存储对象
4、一切搞定后：Manager管理app/迁移类关联MySQL连接对象与app：实现迁移时的数据库更新
5、给manager添加迁移命令

"""

# app = Flask(__name__)


'''
class Config(object):
    """一般添加工程配置信息"""
    DEBUG = True
    
    # mysql相关配置信息
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/web_news'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # redis相关配置信息
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = '6379'
    
    # flask_session相关配置信息
    SESSION_TYPE = 'redis'  # 1.指定session保存到的数据库类型
    SESSION_USE_SIGNER = True  # 2.将session_id加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 3.使用redis实例
    PERMANENT_SESSION_LIFETIME = 86400  # 4.设置session有效期，单位s
'''

"""
# 从对象中添加配置
app.config.from_object(Config)

# 包含请求体的请求都需要开启CSRF;CSRFProtect只完成校验，csrf_token仍需自己实现
CSRFProtect(app)

# 绑定要设置session的应用对象
Session(app)

# 实例化mysql连接对象
db = SQLAlchemy(app)

# 实例化redis连接存储对象：用来保存session
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
"""

# 通过传入配置参数初始化app对象
app = create_app('development')
# 一切配置已完毕，使用Flask-Script与数据库迁移扩展
manager = Manager(app)  # 实例Manager管理对象

# 迁移类关联数据库存储对象和当前应用
Migrate(db, app)
manager.add_command('db', MigrateCommand)  # 迁移命令添加到manager中方便从终端完成迁移


@app.route('/')
def index():
    # 测试打印log日志
    logging.debug('测试debug')
    logging.warning('测试warning')
    logging.error('测试error')
    logging.fatal('测试fatal')
    # flask中输出
    current_app.logger.error('测试error')


    return 'hello'


if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()