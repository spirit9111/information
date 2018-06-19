import logging

from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
import redis
from flask_wtf import CSRFProtect
from flask_session import Session
from flask_migrate import Migrate, MigrateCommand

from info import create_app, db
app = create_app('development')


migrate = Migrate(app)
Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


@app.route('/')
@app.route('/index')
def index():
	logging.debug('111111111111')
	return '<h1>index</h1>'


if __name__ == '__main__':
	manager.run()

# redis-server /etc/redis/redis.conf 开启服务器
