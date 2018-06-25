from flask import render_template

from info.modules.profile import profile_blu


@profile_blu.route('/info')
def user_info():
	return render_template('news/user.html')
