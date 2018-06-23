from flask import render_template, current_app, session

from info.constants import CLICK_RANK_MAX_NEWS
from info.models import News, User
from info.modules.news import news_blu


@news_blu.route('/<int:news_id>')
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
	#
	# # Todo 上方分分类
	# categories_data = []
	# # 获取分类数据(分类id/)
	# categories_ob_list = Category.query.all()
	# # 分类处理查询
	# for category in categories_ob_list:
	# 	categories_data.append(category.to_dict())

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
		# "categories_data": categories_data,
	}

	return render_template('news/detail.html', data=data)
# 获取数据(news_id)


# 判空

# 根据 news_id 查询详细
# 把详细的数据传给前端展示
