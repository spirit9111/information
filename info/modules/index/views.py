from flask import render_template, current_app, session, request, g
from flask import jsonify

from info.constants import CLICK_RANK_MAX_NEWS, HOME_PAGE_MAX_NEWS
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import index_blu


@index_blu.route('/news_list')
def news_list():
	# Todo 左侧新闻
	# 获取数据(分类cid/第几页page/每页显示条数per_page)
	data_dict = request.args
	cid = data_dict.get('cid', 1)
	page = data_dict.get('page', 1)
	per_page = data_dict.get('per_page', HOME_PAGE_MAX_NEWS)
	# 判空处理
	if not all([cid, page, per_page]):
		return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
	# 转换类型,从URL中获取的数据是字符串 转为 整形
	try:
		cid = int(cid)
		page = int(page)
		per_page = int(per_page)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.PARAMERR, errmsg='参数类型错误')
	# 根据cid去mysql的news表查询
	try:
		# 需要判断是否需要的是--最新数据
		if cid == 1:
			paginate_ob = News.query.order_by(News.create_time.desc()).paginate(page, per_page, False)
		# 请求的不是最新栏目
		else:
			paginate_ob = News.query.filter(News.category_id == cid).order_by(News.create_time.desc()).paginate(page,
																												per_page,
																												False)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
	# 从paginate_list对象中获取数据
	news_model_list = paginate_ob.items  # 模型对象列表
	# Todo
	total_page = paginate_ob.pages
	current_page = paginate_ob.page

	paginate_dirt = []
	for paginate in news_model_list:
		paginate_dirt.append(paginate.to_dict())

	data = {
		"current_page": current_page,
		"total_page": total_page,
		"paginate_dirt": paginate_dirt}
	# 将数据返回给前端
	return jsonify(errno=RET.OK, errmsg="刷新OK", data=data)


@index_blu.route('/')
@user_login_data
def index():
	# Todo 右侧点击排行

	# 从mysql中按照点击量获取news数据,最多显示6条数据
	news_ob_list = None
	try:
		news_ob_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS)
	except Exception as e:
		current_app.logger.debug(e)
	# 讲对象的的数据取出来
	click_news_list = []
	for ob in news_ob_list:
		click_news_list.append(ob.to_dict())

	# Todo 上方分分类
	categories_data = []
	# 获取分类数据(分类id/)
	categories_ob_list = Category.query.all()
	# 分类处理查询
	for category in categories_ob_list:
		categories_data.append(category.to_dict())
	user = g.user
	# # 从session获取user_id或者电话/ 应该能获取到token
	# user_id = session.get('user_id', None)
	# # 如果没有设置,在直接访问时会报错
	# user = None
	# if user_id:
	# 	# 从mysql查询数据(头像/昵称)
	# 	try:
	# 		user = User.query.filter_by(id=user_id).first()
	# 	except Exception as e:
	# 		current_app.logger.debug(e)
	# 		return render_template('news/index.html')
	data = {
		"user": user.to_dict() if user else None,
		"click_news_list": click_news_list,
		"categories_data": categories_data,
	}
	return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
	"""favicon.ico实现"""
	return current_app.send_static_file('news/favicon.ico')
