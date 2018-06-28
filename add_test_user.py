import datetime
import functools

# def user_login_data(f):
#     @functools.wraps(f)
#     def wrapper(*args, **kwargs):
#         return f(*args, **kwargs)
#
#     return wrapper


# @app.route('/news/<int:news_id>')
# @user_login_data
# def num1():
#     print("aaa")
#
#
# # @app.route('/')
# @user_login_data
# def num2():
#     print("bbbb")
#
# if __name__ == '__main__':
#     print(num1.__name__)
#     print(num2.__name__)
import random

from info import db
from info.models import User
from manage import app


def add_test_users():
	users = []
	now = datetime.datetime.now()
	for num in range(0, 1000):
		try:
			user = User()
			user.nick_name = "%011d" % num
			user.mobile = "%011d" % num
			user.password_hash = "pbkdf2:sha256:50000$SgZPAbEj$a253b9220b7a916e03bf27119d401c48ff4a1c81d7e00644e0aaf6f3a8c55829"
			t = random.randint(0, 2678400)
			user.last_login = now - datetime.timedelta(seconds=t)
			users.append(user)
			print(user.mobile)
		except Exception as e:
			print(e)
	# 手动开启一个app的上下文
	with app.app_context():
		db.session.add_all(users)
		db.session.commit()
	print('OK')


if __name__ == '__main__':
	add_test_users()
