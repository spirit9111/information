import time
from datetime import datetime, timedelta
from flask import render_template, request, redirect, current_app, url_for, session, g, jsonify, abort

from info import db
from info.constants import QINIU_DOMIN_PREFIX
from info.libs.upload_pic import upload_pic
from info.models import User, News, Category
from info.modules.admin import admin_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


# Todo 关注


@admin_blu.route('/news_type', methods=['POST', 'GET'])
def news_type():
	"""新闻分类"""
	if request.method == 'GET':
		try:
			category_mo_list = Category.query.filter(Category.id != 1).all()
		except Exception as e:
			current_app.logger.debug(e)
			return render_template('admin/news_type.html', errmsg="数据库查询失败")
		category_data_list = []
		for i in category_mo_list:
			category_data_list.append(i.to_dict())
		data = {
			"category_data_list": category_data_list
		}
		return render_template('admin/news_type.html', data=data)
	# 新增分类/修改原有分类名
	cname = request.json.get("name")
	cid = request.json.get("id", None)
	if not cname:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
	# 如果接收到了cid表示修改
	if cid:
		try:
			cid = int(cid)
			category = Category.query.get(cid)
		except Exception as e:
			current_app.logger.error(e)
			return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

		if not category:
			return jsonify(errno=RET.NODATA, errmsg="未查询到分类数据")
		category.name = cname
	else:
		category = Category()
		category.name = cname
		db.session.add(category)

	return jsonify(errno=RET.OK, errmsg="OK")


@admin_blu.route('/news_edit_detail', methods=['POST', 'GET'])
def news_edit_detail():
	"""编辑详细/提交"""

	if request.method == "GET":
		news_id = request.args.get("news_id")
		if not news_id:
			abort(404)
		try:
			news_id = int(news_id)
		except Exception as e:
			current_app.logger.error(e)
			return render_template('admin/news_edit_detail.html', errmsg="参数错误")
		try:
			news = News.query.get(news_id)
		except Exception as e:
			current_app.logger.error(e)
			return render_template('admin/news_edit_detail.html', errmsg="查询数据错误")
		if not news:
			return render_template('admin/news_edit_detail.html', errmsg="未查询到数据")
		# 查询分类数据
		try:
			category_mo_list = Category.query.filter(Category.id != 0).all()
		except Exception as e:
			current_app.logger.error(e)
			return render_template('admin/news_edit_detail.html', errmsg="查询数据错误")
		category_data_list = []
		for category in category_mo_list:
			# 取到分类的字典
			cate_dict = category.to_dict()
			# 设置而外属性表示是否需要加载时选中
			if category.id == news.category_id:
				cate_dict["is_selected"] = True
			category_data_list.append(cate_dict)
		data = {
			"news": news.to_dict(),
			"categories": category_data_list
		}

		return render_template('admin/news_edit_detail.html', data=data)


	# post进入这里
	news_id = request.form.get("news_id")
	title = request.form.get("title")
	digest = request.form.get("digest")
	content = request.form.get("content")
	index_image = request.files.get("index_image")
	category_id = request.form.get("category_id")
	# 判空
	if not all([title, digest, content, category_id]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
	try:
		news = News.query.get(news_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	if not news:
		return jsonify(errno=RET.NODATA, errmsg="数据不存在")

	if index_image:
		try:
			index_image = index_image.read()
		except Exception as e:
			current_app.logger.debug(e)
			return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

	# 上传
	try:
		key = upload_pic(index_image)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
	# 保存到mysql
	news.index_image_url = QINIU_DOMIN_PREFIX + key
	news.title = title
	news.digest = digest
	news.content = content
	news.category_id = category_id

	return jsonify(errno=RET.OK, errmsg="OK")


@admin_blu.route('/news_edit')
def news_edit():
	"""编辑首页"""
	page = request.args.get('news_id', 1)
	keywords = request.args.get('keywords', None)
	try:
		page = int(page)
	except Exception as e:
		current_app.logger.error(e)

	news_mo_list = []
	current_page = 1
	total_page = 1

	# 搜索功能实现
	filter_list = [News.status != 0]
	if keywords:
		filter_list.append(News.title.contains(keywords))
	try:
		paginate_mo = News.query.filter(*filter_list).order_by(News.create_time).paginate(page, 10, False)
		current_page = paginate_mo.page
		total_page = paginate_mo.pages
		news_mo_list = paginate_mo.items
	except Exception as e:
		current_app.logger.debug(e)

	news_data_list = []
	for news in news_mo_list:
		news_data_list.append(news.to_dict())

	data = {
		"news_data_list": news_data_list,
		"current_page": current_page,
		"total_page": total_page
	}

	return render_template('admin/news_edit.html', data=data)


@admin_blu.route('/check_news', methods=['POST'])
def check_news():
	"""审核详细"""
	news_id = request.json.get('news_id')
	action = request.json.get('action')

	if not all([news_id, action]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

	try:
		news_id = int(news_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	if action not in ["accept", "reject"]:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	# 查询到指定的新闻数据
	try:
		news = News.query.get(news_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	if not news:
		return jsonify(errno=RET.NODATA, errmsg="未查询到数据")
	# 审核不通过
	if action == 'reject':
		reason = request.json.get('reason')
		if not reason:
			return jsonify(errno=RET.PARAMERR, errmsg="请输入拒绝原因")
		news.status = -1
		news.reason = reason
	else:
		news.status = 0
	return jsonify(errno=RET.OK, errmsg="审核通过")


@admin_blu.route('/news_rev_detail/<int:news_id>')
def news_rev_detail(news_id):
	"""审核界面"""
	if not news_id:
		return render_template('admin/news_review_detail.html', data={"errmsg": "参数错误"})

	try:
		news_mo = News.query.filter(News.id == news_id).first()
	except Exception as e:
		current_app.logger.debug(e)
		return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})

	data = {
		'news': news_mo.to_dict()
	}

	return render_template('admin/news_review_detail.html', data=data)


@admin_blu.route('/news_rev')
def news_rev():
	"""新闻审核主页"""

	# 筛选出所有没有通过审核的新闻
	page = request.args.get('p', 1)
	keywords = request.args.get('keywords', None)
	try:
		page = int(page)
	except Exception as e:
		current_app.logger.error(e)
	news_mo_list = []
	current_page = 1
	total_page = 1

	# 搜索功能实现
	filter_list = [News.status != 0]
	if keywords:
		filter_list.append(News.title.contains(keywords))
	try:
		paginate_mo = News.query.filter(*filter_list).order_by(News.create_time).paginate(page, 10, False)
		current_page = paginate_mo.page
		total_page = paginate_mo.pages
		news_mo_list = paginate_mo.items
	except Exception as e:
		current_app.logger.debug(e)

	news_data_list = []
	for news in news_mo_list:
		news_data_list.append(news.to_review_dict())

	data = {
		"news_data_list": news_data_list,
		"current_page": current_page,
		"total_page": total_page
	}

	return render_template('admin/news_review.html', data=data)


@admin_blu.route('/user_list')
def user_list():
	"""用户列表"""
	page = request.args.get('p', 1)

	try:
		page = int(page)
	except Exception as e:
		current_app.logger.error(e)
	user_mo_list = []
	current_page = 1
	total_page = 1
	try:
		paginate_mo = User.query.filter(User.is_admin == 0).paginate(page, 10, False)
		current_page = paginate_mo.page
		total_page = paginate_mo.pages
		user_mo_list = paginate_mo.items
	except Exception as e:
		current_app.logger.debug(e)

	user_data_list = []
	for user in user_mo_list:
		user_data_list.append(user.to_admin_dict())

	data = {
		"user_data_list": user_data_list,
		"current_page": current_page,
		"total_page": total_page
	}
	# return render_template('admin/user_list.html')
	return render_template('admin/user_list.html', data=data)


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
