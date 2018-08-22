import logging
from logging.handlers import RotatingFileHandler
from config import config
import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

# Flask的很多扩展都可以先初始化扩展对象，然后再调用init_app方法初始化
db = SQLAlchemy()


def setup_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级

    # 创建日志记录器:日志保存路径、单日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)

    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')

    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)

    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    """类似于工程方法"""
    # 配置日志,传入配置名字，根据名字获取对应的配置日志的等级
    setup_log(config_name)
    # 创建flask对象
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

