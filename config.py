import logging
from redis import StrictRedis


class Config(object):
    """一般添加工程配置信息"""
    # 配置session暗钥!!!!
    SECRET_KEY = 'td2ZngpuiGIgVJ/NSCvxAw7a7f4LnX2GEQrxom3UGR20T/+mNV6PAEXViYAKcqai'

    # mysql相关配置信息
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/web_news'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 开启在每次请求的结束，自动执行一次db.session.commit()
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # redis相关配置信息
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379  # 端口不能使用字符串!!!!

    # flask_session相关配置信息:
    SESSION_TYPE = 'redis'  # 1.指定session保存到的数据库类型
    SESSION_USE_SIGNER = True  # 2.将session_id加密签名处理
    # 3.指定session保存时用的数据库
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    PERMANENT_SESSION_LIFETIME = 86400*2  # 4.设置session有效期，单位s
    SESSION_PERMANENT = False  # 5.设置是否需要过期

    # 设置日志等级
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发模式下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产模式下的配置"""
    DEBUG = False
    # 上线后重写父类的log等级，提高日志等级，减少不必要的写入，能提升性能
    LOG_LEVEL = logging.WARNING
    # redis相关配置信息
    # REDIS_HOST = '127.0.0.1'
    # REDIS_PORT = '6379'


class TestingConfig(Config):
    DEBUG = True
    TESTING = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}