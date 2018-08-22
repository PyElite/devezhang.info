import logging
import redis


class Config(object):
    """一般添加工程配置信息"""
    # DEBUG = True

    # mysql相关配置信息
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/web_news'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis相关配置信息
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = '6379'

    # flask_session相关配置信息:
    # 1.指定session保存到的数据库类型
    SESSION_TYPE = 'redis'
    # 2.将session_id加密签名处理
    SESSION_USE_SIGNER = True
    # 3.使用redis实例
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 4.设置session有效期，单位s
    PERMANENT_SESSION_LIFETIME = 86400*2
    # 5.设置是否需要过期
    SESSION_PERMANENT = False
    # 设置日志等级
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发模式下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产模式下的配置"""
    DEBUG = False
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