from urllib import response

import redis
from flask import Flask, render_template, g
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from logging.handlers import RotatingFileHandler
import logging
from config import config

db = SQLAlchemy()
redis_store = None


def setup_log(config_name):
	"""配置日志"""

	# 设置日志的记录等级
	logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级
	# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
	file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
	# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
	formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
	# 为刚创建的日志记录器设置日志记录格式
	file_log_handler.setFormatter(formatter)
	# 为全局的日志工具对象（flask app使用的）添加日志记录器
	logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
	setup_log(config_name)
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	db.init_app(app)
	from info.utils.common import do_index_class
	global redis_store
	redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)

	# CSRFProtect可以自动验证来自 表单 和 cookie 中的csrf_token
	CSRFProtect(app)

	Session(app)
	app.add_template_filter(do_index_class, 'do_index_class')

	# 使用钩子函数设置cookie
	@app.after_request
	def set_csrf_token(response):
		# 生成csrf_token
		csrf_token = generate_csrf()
		response.set_cookie('csrf_token', csrf_token)
		return response

	from info.utils.common import user_login_data

	@app.errorhandler(404)
	@user_login_data
	def page_not_found(_):
		user = g.user
		data = {"user": user.to_dict() if user else None}
		return render_template('news/404.html', data=data)

	from info.modules.index import index_blu
	app.register_blueprint(index_blu)
	from info.modules.passport import passport_blu
	app.register_blueprint(passport_blu)
	from info.modules.news import news_blu
	app.register_blueprint(news_blu)
	from info.modules.profile import profile_blu
	app.register_blueprint(profile_blu)
	# 后台
	from info.modules.admin import admin_blu
	app.register_blueprint(admin_blu)
	return app
