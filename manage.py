from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
import redis
from flask_wtf import CSRFProtect
from flask_session import Session
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__)


class Config:
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


app.config.from_object(Config)

db = SQLAlchemy(app)
# redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
manager = Manager(app)
csrf = CSRFProtect(app)
Session(app)
migrate = Migrate(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


@app.route('/')
@app.route('/index')
def index():
	return '<h1>index</h1>'


if __name__ == '__main__':
	manager.run()

# redis-server /etc/redis/redis.conf 开启服务器
