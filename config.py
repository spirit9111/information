import redis
from flask import logging


class Config(object):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:w92z12x14@127.0.0.1:3306/information"
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	REDIS_HOST = "127.0.0.1"
	REDIS_PORT = 6379
	SECRET_KEY = 'aa'
	SESSION_TYPE = "redis"  # 指定 session 保存到 redis 中
	SESSION_USE_SIGNER = True  # 让 cookie 中的 session_id 被加密签名处理
	SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 使用 redis 的实例
	PERMANENT_SESSION_LIFETIME = 86400  # session 的有效期，单位是秒
	LOG_LEVEL = logging.DEBUG


class DevelopementConfig(Config):
	"""开发模式下的配置"""
	DEBUG = True


class ProductionConfig(Config):
	"""生产模式下的配置"""
	LOG_LEVEL = logging.ERROR


config = {
	"development": DevelopementConfig,
	"production": ProductionConfig
}
