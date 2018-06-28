import time
from datetime import datetime, timedelta

from flask import render_template, request, redirect, current_app, url_for, session, g
from info.models import User
from info.modules.admin import admin_blu
from info.utils.common import user_login_data


@admin_blu.route('/user_count', methods=['GET'])
def user_count():
	"""用户统计"""
	# 获取用户总数
	user_all_count = 0
	try:
		user_all_count = User.query.count()
	except Exception as e:
		current_app.logger.debug(e)

	# 目标:获取月新增数
	# 获取当前的年月日
	now = time.localtime()
	# 拼凑一个表示当前月份,日期为1号的 字符串
	begin_mouth_str = '%d-%02d-01' % (now.tm_year, now.tm_mon)
	# 将字符串转换为datetime对象,并格式化输出
	begin_mouth = datetime.strptime(begin_mouth_str, '%Y-%m-%d')
	mon_count = 0
	try:
		mon_count = User.query.filter(User.is_admin == 0, User.create_time >= begin_mouth).count()
	except Exception as e:
		current_app.logger.debug(e)

	# 目标:获取日新增数
	begin_day_str = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)
	begin_day = datetime.strptime(begin_day_str, '%Y-%m-%d')
	day_count = 0
	try:
		day_count = User.query.filter(User.is_admin == 0, User.create_time >= begin_day).count()
	except Exception as e:
		current_app.logger.debug(e)

	# 获取折线图每日数据,近一个月的活跃用户数据
	everyday_count_list = []
	everyday_list = []
	for i in range(0, 31):
		everyday_begin = begin_day - timedelta(days=i)

		everyday_end = begin_day - timedelta(days=i - 1)

		everyday_count = User.query.filter(User.is_admin == 0, User.last_login >= everyday_begin,
										   User.last_login <= everyday_end, ).count()

		everyday_count_list.append(everyday_count)

		everyday_list.append(everyday_end.strftime('%m-%d'))

		# 翻转
	everyday_count_list.reverse()
	everyday_list.reverse()
	data = {
		"user_all_count": user_all_count,
		"mon_count": mon_count,
		"begin_day": day_count,
		"everyday_count_list": everyday_count_list,
		"everyday_list": everyday_list
	}

	return render_template('admin/user_count.html', data=data)


@admin_blu.route('/login', methods=['POST', 'GET'])
def login():
	"""登录"""
	if request.method == 'GET':
		# 如果是已经登陆的管理员进入login界面,不需要重新填写登录信息
		user_id = session.get('user_id')
		is_admin = session.get('is_admin')
		if user_id and is_admin:
			return redirect(url_for('admin.index'))
		return render_template('admin/login.html')
	# 获取参数(name/pwd)
	nick_name = request.form.get('username')
	password = request.form.get('password')
	# 判空
	if not all([nick_name, password]):
		return render_template('admin/login.html', errmsg="参数错误")
	# 校验
	# 判断user是否存在
	try:
		user_mo = User.query.filter(User.nick_name == nick_name).first()
	except Exception as e:
		current_app.logger.debug(e)
		return render_template('admin/login.html', errmsg="数据库异常")

	if not user_mo:
		return render_template('admin/login.html', errmsg="用户不存在")

	# 判断pwd是否正确
	if not user_mo.check_password(password):
		return render_template('admin/login.html', errmsg="密码错误")
	# 判断权限
	if not user_mo.is_admin:
		return render_template('admin/login.html', errmsg="权限错误")
	# 保持登录状态
	session['nick_name'] = user_mo.nick_name
	session['mobile'] = user_mo.mobile
	session['user_id'] = user_mo.id
	session["is_admin"] = True

	# 重定向到admin/index
	return redirect(url_for('admin.index'))


@admin_blu.route('/index')
@user_login_data
def index():
	"""admin首页"""
	user = g.user
	if not user:
		return

	return render_template('admin/index.html', user=user.to_dict())
