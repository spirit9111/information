from flask import render_template, redirect, g, request, jsonify, current_app, url_for
from info import db
from info.constants import QINIU_DOMIN_PREFIX
from info.libs.upload_pic import upload_pic
from info.models import User, News, Category
from info.modules.profile import profile_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


# Todo 关注

# Todo 新闻列表
@profile_blu.route('/news_list')
@user_login_data
def news_list():
	return render_template('news/user_news_list.html')


# Todo 新闻发布
@profile_blu.route('/publish', methods=['POST', 'GET'])
@user_login_data
def publish():
	if request.method == 'GET':
		categories_mo_list = Category.query.filter(Category.id != 1).all()
		categories = []
		for i in categories_mo_list:
			categories.append(i.to_dict())

		data = {
			"categories": categories
		}
		return render_template('news/user_news_release.html', data=data)
	# 获取参数
	user = g.user
	title = request.form.get('title')
	source = '个人发布'
	category_id = request.form.get('category_id')
	digest = request.form.get('digest')
	index_image = request.files.get("index_image").read()
	content = request.form.get("content")
	# # 判空
	if not all([title, category_id, digest, index_image, content]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
	try:
		title = int(title)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	# 上传图片
	try:
		key = upload_pic(index_image)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.THIRDERR, errmsg="图片上传失败")
	# 保存数据
	news = News()
	news.title = title
	news.category_id = category_id
	news.digest = digest
	news.index_image_url = key
	news.content = content
	news.source = source
	news.user_id = user.id
	news.status = 1
	try:
		db.session.add(news)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库保存失败")
	# return jsonify(errno=RET.OK, errmsg="等待审核!")
	return redirect(url_for('profile.news_list'))


# Todo 收藏
@profile_blu.route('/collection')
@user_login_data
def collection():
	user = g.user
	# 获取当前页,默认1
	page = request.args.get('p', 1)
	# 教研参数
	try:
		page = int(page)
	except Exception as e:
		current_app.logger.error(e)
	# p = 1
	news_mo_list = []
	current_page = 1
	total_page = 1
	try:
		paginate_mo = user.collection_news.paginate(page, 10, False)
		current_page = paginate_mo.page
		total_page = paginate_mo.pages
		news_mo_list = paginate_mo.items
	except Exception as e:
		current_app.logger.debug(e)

	data_list = []
	for i in news_mo_list:
		data_list.append(i.to_dict())

	data = {
		"collection": data_list,
		"current_page": current_page,
		"total_page": total_page,
	}
	return render_template('news/user_collection.html', data=data)


# Todo 密码
@profile_blu.route('/re_pwd', methods=['POST', 'GET'])
@user_login_data
def re_pwd():
	if request.method == 'GET':
		return render_template('news/user_pass_info.html')
	# 获取oldpwd/newpwd
	old_password = request.json.get('old_password')
	new_password = request.json.get('new_password')
	# 判空
	if not all([old_password, new_password]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
	if old_password == new_password:
		return jsonify(errno=RET.PWDERR, errmsg="新旧密码不能相同")

	user = g.user
	# 验证旧密码是否正确
	if not user.check_password(old_password):
		return jsonify(errno=RET.PWDERR, errmsg="旧密码输入错误")
	user.password = new_password
	return jsonify(errno=RET.OK, errmsg="密码修改成功")


# Todo 头像
@profile_blu.route('/pic_info', methods=['POST', 'GET'])
@user_login_data
def pic_info():
	user = g.user
	if request.method == 'GET':
		# to_dict()中的avatar已经加上了域名前缀
		return render_template('news/user_pic_info.html', data={"user": user.to_dict()})
	# 获取头像,二进制文件
	pic_file = request.files.get('avatar')
	# 判空
	if not pic_file:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	try:
		pic_file_2 = pic_file.read()
		# 调用第三方上传头像,获取key
		key = upload_pic(pic_file_2)
		# 将key保存到mysql
		user.avatar_url = key
		db.session.commit()
	except Exception as e:
		db.session.rollback()
		current_app.logger.debug(e)
		return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

	# 将url数据返回给前端
	data = {
		"avatar_url": QINIU_DOMIN_PREFIX + user.avatar_url
	}
	return jsonify(errno=RET.OK, errmsg="OK", data=data)


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
