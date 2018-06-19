from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db

app = create_app('development')

migrate = Migrate(app)
Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
	manager.run()

# redis-server /etc/redis/redis.conf 开启服务器
