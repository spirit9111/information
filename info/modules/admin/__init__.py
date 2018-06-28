from flask import Blueprint, redirect, session, request, url_for

admin_blu = Blueprint('admin', __name__, url_prefix='/admin')

from . import views


# 使用钩子函数实现判断用户权限,如果不是管理员直接重定向到首页
@admin_blu.before_request
def check_admin():
	is_admin = session.get('is_admin', False)
	# 如果是普通用户,而且尝试访问 admin界面 就重定向
	dest_url = request.url.endswith(url_for('admin.login'))
	if not is_admin and not dest_url:
		return redirect('/')
