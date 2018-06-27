from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models
from info.models import User

app = create_app('development')
# app = create_app('production')

migrate = Migrate(app)
Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


# 创建管理员账号的命令
@manager.option('-n', '-name', dest='name')
@manager.option('-p', '-password', dest='password')
def createsuperuser(name, password):
	"""创建管理员账号"""
	if not all([name, password]):
		print('参数不足')
		return
	user = User()
	user.nick_name = name
	user.mobile = name
	user.password = password
	user.is_admin = True
	try:
		db.session.add(user)
		db.session.commit()
		print("OK!")
	except Exception as e:
		print(e)
		db.session.rollback()


if __name__ == '__main__':
	manager.run()

# redis-server /etc/redis/redis.conf 开启redis服务器
