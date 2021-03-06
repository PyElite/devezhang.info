import logging
from logging.handlers import RotatingFileHandler

from flask_wtf.csrf import generate_csrf
from redis import StrictRedis

from config import config
import redis
from flask import Flask, g, render_template
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

# Flask的很多扩展都可以先初始化扩展对象，然后再调用init_app方法初始化
db = SQLAlchemy()

# 变量注释，方便调用，pycharm提供
redis_store = None  # type: StrictRedis
# redis_store: StrictRedis=None


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
    app = Flask(__name__)  # 默认参数static_path = ./static!!!
    # 从对象中添加配置
    app.config.from_object(config[config_name])
    # 通过app初始化
    db.init_app(app)

    # 实例化redis连接存储对象：用来保存session
    global redis_store
    redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT, decode_responses=True)
    # 包含请求体的请求都需要开启CSRF;CSRFProtect只完成校验，csrf_token仍需自己实现
    CSRFProtect(app)
    # 绑定要设置session的应用对象
    Session(app)

    @app.after_request
    def after_request(response):
        # 生成随机csrf_token值
        csrf_token = generate_csrf()
        # 设置cookie值
        response.set_cookie('csrf_token', csrf_token)
        return response

    from info.utils.common import user_login_data

    @app.errorhandler(404)
    @user_login_data
    def page_not_found(x):
        user = g.user  # 因为data中没有分类数据，所以新闻分类不会展示
        data = {"user": user.to_dict() if user else None}
        return render_template("news/404.html", data=data)

    # 注册根路由蓝图:这个导入称为延迟导入，解决了循环导入
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)
    # 注册注册时的蓝图:每个路由都要注册到app中
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    # 注册新闻详情模块的蓝图
    from info.modules.news import news_blu
    app.register_blueprint(news_blu)
    # 注册新闻详情模块的蓝图
    from info.modules.profile import profile_blu
    app.register_blueprint(profile_blu)
    # 注册管理员模块的蓝图
    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu, url_prefix="/admin")  # 创建或注册都可以加前缀

    return app

