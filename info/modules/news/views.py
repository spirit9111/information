from flask import render_template, current_app, session, request, g, jsonify

from info import db
from info.constants import CLICK_RANK_MAX_NEWS
from info.models import News, User, Comment, CommentLike
from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@news_blu.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
	"""点赞"""
	# 判断是否登录,登陆后才能点赞
	user = g.user
	if not user:
		return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")

	# 获取参数(comment_id/action)
	comment_id = request.json.get('comment_id')
	action = request.json.get('action')
	# 判空
	if not all([comment_id, action]):
		return jsonify(errno=RET.PARAMERR, errmsg="未能获取参数")
	# 校验参数
	try:
		comment_id = int(comment_id)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.PARAMERR, errmsg="参数comment_id错误")
	# 判断该评论是否存在
	try:
		comment_mo = Comment.query.get(comment_id)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")

	if not comment_mo:
		return jsonify(errno=RET.NODATA, errmsg="评论不存在")

	# 判断action
	if action == 'remove':
		# 如果在已经点赞,可以取消点赞
		comment_like_mo = CommentLike.query.filter(CommentLike.comment_id == comment_id,
												   CommentLike.user_id == user.id).first()
		if comment_like_mo:
			try:
				db.session.delete(comment_like_mo)
				comment_mo.like_count -= 1
				db.session.commit()
			except Exception as e:
				current_app.logger.debug(e)
				return jsonify(errno=RET.DBERR, errmsg="数据库异常")
	elif action == 'add':
		# 点赞
		comment_like_mo = CommentLike.query.filter(CommentLike.comment_id == comment_id,
												   CommentLike.user_id == user.id).first()
		if not comment_like_mo:
			comment_like_mo = CommentLike()
			comment_mo.like_count += 1
			comment_like_mo.user_id = user.id
			comment_like_mo.comment_id = comment_id
			try:
				db.session.add(comment_like_mo)
				db.session.commit()
			except Exception as e:
				current_app.logger.debug(e)
				return jsonify(errno=RET.DBERR, errmsg="数据库异常")
	else:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	return jsonify(errno=RET.OK, errmsg="点赞成功")


# Todo 评论新闻/增加评论父评论的功能
@news_blu.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
	"""评论功能"""
	# 判断是否登录,登陆后才能评论
	user = g.user
	if not user:
		return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")
	# 获取数据(news_id/comment评论内容/parent_id)
	data_dict = request.json
	news_id = data_dict.get('news_id')
	comment_content = data_dict.get('comment')
	parent_id = data_dict.get('parent_id', None)

	# 判断数据是否为空
	if not all([news_id, comment_content]):
		return jsonify(errno=RET.PARAMERR, errmsg="未能获取参数")
	# 校验数据类型
	try:
		news_id = int(news_id)
		if parent_id:
			parent_id = int(parent_id)
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
	# 判断news是否存在
	try:
		news_ob = News.query.get(news_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

	if not news_ob:
		return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")
	# 向数据库写入数据
	comment = Comment()
	comment.news_id = news_id
	comment.user_id = user.id
	comment.content = comment_content
	# 如果是子评论,需要保存父评论的id
	if parent_id:
		comment.parent_id = parent_id
	try:
		db.session.add(comment)
		db.session.commit()
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	# 将数据传输到前端进行显示
	return jsonify(errno=RET.OK, errmsg="评论成功", data=comment.to_dict())


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
	# 获取用户所有的新闻收藏表，判断news在不在里面再去查询
	news_id_list = []
	if user:
		for news_ob2 in user.collection_news.all():
			news_id_list.append(news_ob2.id)
	# 如果在列表内表示已经收藏
	if news_id in news_id_list:
		is_collected = True

	# Todo 显示点赞的状态
	# 查询出已经点赞的评论全部id,登录状态下
	comment_like_id_list = []
	if user:
		try:
			# 1.查询出当前news的所有评论的id
			comment_mo_list = Comment.query.filter(Comment.news_id == news_id).all()
			comment_id_list = [i.id for i in comment_mo_list]
			# 2.筛选出当前用户点赞的评论
			comment_like_mo_list = CommentLike.query.filter(CommentLike.comment_id.in_(comment_id_list),
															CommentLike.user_id == user.id).all()
			comment_like_id_list = [i.comment_id for i in comment_like_mo_list]
		except Exception as e:
			current_app.logger.debug(e)
			return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

	# 尝试查询评论数据
	comment_ob_list = []
	try:
		comment_ob_list = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc())
	except Exception as e:
		current_app.logger.debug(e)

	comment_data_dict = []
	for comment_ob in comment_ob_list:
		comment_dict = comment_ob.to_dict()
		# 给每一个评论新增新的属性is_like,表示该评论是否被点赞
		comment_dict["is_like"] = False
		# 如果评论的id 在 当前用户当前新闻的 id列表中,则修改is_like为True,表示已经点赞
		if comment_ob.id in comment_like_id_list:
			comment_dict["is_like"] = True

		comment_data_dict.append(comment_dict)

	data = {
		"user": user.to_dict() if user else None,
		"click_news_list": click_news_list,
		"news": news_data_dict,
		"is_collected": is_collected,
		"comments": comment_data_dict
	}

	return render_template('news/detail.html', data=data)
