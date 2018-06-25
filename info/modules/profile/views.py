from flask import render_template, redirect, g

from info.modules.profile import profile_blu
from info.utils.common import user_login_data


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
