from flask import render_template, current_app, session
from flask import jsonify

from info.constants import CLICK_RANK_MAX_NEWS
from info.models import User, News
from info.utils.response_code import RET
from . import index_blu


# Todo 上方分分类
# Todo 左侧新闻
@index_blu.route('/')
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

	# 从session获取user_id或者电话/ 应该能获取到token
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

	data = {
		"user": user.to_dict() if user else None,
		"click_news_list": click_news_list,
	}
	return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
	"""favicon.ico实现"""
	return current_app.send_static_file('news/favicon.ico')
