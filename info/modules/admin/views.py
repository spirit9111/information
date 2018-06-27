from flask import render_template, request, jsonify, redirect, current_app, url_for, session

from info.models import User
from info.modules.admin import admin_blu
from info.utils.response_code import RET


@admin_blu.route('/login', methods=['POST', 'GET'])
def login():
	"""登录"""
	if request.method == 'GET':
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

	# 重定向到admin/index
	return redirect(url_for('admin.index'))


@admin_blu.route('/index')
def index():
	return render_template('admin/index.html')
