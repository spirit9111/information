from flask import render_template

from info.modules.news import news_blu


@news_blu.route('/<int:news_id>')
def news(news_id):
	return render_template('news/detail.html')
# 获取数据(news_id)


# 判空

# 根据 news_id 查询详细
# 把详细的数据传给前端展示
