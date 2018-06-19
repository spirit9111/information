import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from config import config

db = SQLAlchemy()
redis_store = None


def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	db.init_app(app)
	global redis_store
	redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)
	CSRFProtect(app)
	Session(app)
	return app
