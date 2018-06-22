from flask import render_template, current_app, session
from flask import jsonify

from info.models import User
from info.utils.response_code import RET
from . import index_blu


# Todo 右上角登录/退出/注册/头像实现
@index_blu.route('/')
@index_blu.route('/index')
def index():
	# 从session获取user_id或者电话
	user_id = session.get('user_id', None)
	# 如果没有设置,在直接访问时会报错
	user = None
	if user_id:
		# 从mysql查询数据(头像/昵称)
		try:
			user = User.query.filter_by(id=user_id).first()
		except Exception as e:
			current_app.logger.debug(e)
			return render_template('news/index.html')
	data = user.to_dict() if user else None
	return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
	"""favicon.ico实现"""
	return current_app.send_static_file('news/favicon.ico')
