from flask import render_template, current_app, session, request, g, jsonify

from info.constants import CLICK_RANK_MAX_NEWS
from info.models import News, User
from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@news_blu.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
	user = g.user
	current_app.logger.debug('user:%s' % type(user))
	if not user:
		return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")

	# 获取数据(news_id/action)
	data_dict = request.json
	news_id = data_dict.get("news_id")
	action = data_dict.get("action")
	# 判断数据是否为空
	if not all([news_id, action]):
		return jsonify(errno=RET.PARAMERR, errmsg="未能获取参数")
	try:
		news_id = int(news_id)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	try:
		news_ob = News.query.get(news_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
	if not news_ob:
		return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

	# 判断用户的操作方式('collect', 'cancel_collect')
	if action == 'cancel_collect':
		# 如果在收藏列表,可以取消收藏
		if news_ob in user.collection_news:
			try:
				user.collection_news.remove(news_ob)
			except Exception as e:
				current_app.logger.debug(e)
				return jsonify(errno=RET.DBERR, errmsg="数据库异常")
	elif action == 'collect':
		if news_ob not in user.collection_news:
			# 添加到用户的新闻收藏列表
			try:
				user.collection_news.append(news_ob)
			except Exception as e:
				current_app.logger.debug(e)
				return jsonify(errno=RET.DBERR, errmsg="数据库异常")
	else:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
	return jsonify(errno=RET.OK, errmsg="操作成功")


# 如果是收藏collect
# 如果是取消收藏cancel_collect


@news_blu.route('/<int:news_id>')
@user_login_data
def news(news_id):
	news_ob_list = None
	try:
		news_ob_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS)
	except Exception as e:
		current_app.logger.debug(e)
	# 讲对象的的数据取出来
	click_news_list = []
	for ob in news_ob_list:
		click_news_list.append(ob.to_dict())
	# # Todo 上方分分类
	user = g.user
	# Todo 左侧详情页
	# 判断news_id是否为空
	if not news_id:
		return jsonify(errno=RET.PARAMERR, errmsg="未能获取参数")
	# [判断news_id值的类型是否正确
	try:
		news_id = int(news_id)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.PARAMERR, errmsg="参数类型错误")
	# 根据news_id去mysql查询数据
	try:
		news_ob = News.query.get(news_id)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
	# 取出news_ob的数据
	if not news_ob:
		return jsonify(errno=RET.DATAEXIST, errmsg="数据不存在")
	news_ob.clicks += 1
	news_data_dict = news_ob.to_dict()

	# Todo 收藏功能
	# 获取用户是谁user 新闻是哪个news_id
	# 默认没有收藏
	is_collected = False
	# 获取用户所有的新闻收藏表，判断news在不在里面
	news_id_list = []
	if user:
		current_app.logger.debug(type(user.collection_news.all()))
		for news_ob2 in user.collection_news.all():
			current_app.logger.debug(news_ob2, type(news_ob2))
			news_id_list.append(news_ob2.id)
	# 如果在列表内表示已经收藏
	if news_id in news_id_list:
		is_collected = True

	data = {
		"user": user.to_dict() if user else None,
		"click_news_list": click_news_list,
		"news": news_data_dict,
		"is_collected": is_collected
	}

	return render_template('news/detail.html', data=data)
