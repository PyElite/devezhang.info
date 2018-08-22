from config import config
import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

# Flask的很多扩展都可以先初始化扩展对象，然后再调用init_app方法初始化
db = SQLAlchemy()


def create_app(config_name):
    """类似于工程方法"""
    app = Flask(__name__)
    # 从对象中添加配置
    app.config.from_object(config[config_name])

    # 通过app初始化
    db.init_app(app)
    # 包含请求体的请求都需要开启CSRF;CSRFProtect只完成校验，csrf_token仍需自己实现
    CSRFProtect(app)
    # 绑定要设置session的应用对象
    Session(app)

    # # 实例化mysql连接对象
    # db = SQLAlchemy(app)
    # 实例化redis连接存储对象：用来保存session
    redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)

    return app