from flask import render_template, redirect, g, request, jsonify, current_app
from info import db
from info.modules.profile import profile_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


# Todo 新闻列表
# Todo 发布
# Todo 收藏
# Todo 密码
# Todo 关注
# Todo 头像
@profile_blu.route('/pic_info', methods=['POST'])
def pic_info():
	pass


# Todo 基本资料
@profile_blu.route('/base_info', methods=['POST', 'GET'])
@user_login_data
def base_info():
	"""基本资料"""
	# user = g.user
	if request.method == 'GET':
		return render_template('news/user_base_info.html', data={"user": g.user.to_dict()})
	# # 获取签名/昵称/性别
	nick_name = request.json.get('nick_name')
	signature = request.json.get('signature')
	gender = request.json.get('gender')
	# # 判空
	if not all([nick_name, signature, gender]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
	# # 教研参数
	if gender not in ['MAN', 'WOMAN']:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
	# # 将数据存入数据库
	try:
		user = g.user
		user.nick_name = nick_name
		user.signature = signature
		user.gender = gender
		db.session.commit()
		current_app.logger.debug(user.nick_name, user.signature, user.gender)
	except Exception as e:
		db.session.rollback()
		current_app.logger.debug(e)
	# return jsonify(errno=RET.DBERR, errmsg="数据库异常")
	# # # 将数据返回给钱段
	return jsonify(errno=RET.OK, errmsg="更新数据成功")


# return render_template("news/user_base_info.html")


@profile_blu.route('/info')
@user_login_data
def user_info():
	user = g.user
	if not user:
		# 用户未登录，重定向到主页
		return redirect('/')
	data = {
		"user": user.to_dict(),
	}
	# 渲染模板
	return render_template("news/user.html", data=data)
