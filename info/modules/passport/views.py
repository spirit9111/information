import random
import re
from datetime import datetime

from flask import request, jsonify, current_app, make_response, session, redirect, url_for
from info import redis_store, db
from info.constants import IMAGE_CODE_REDIS_EXPIRES, SMS_CODE_REDIS_EXPIRES
from info.models import User
from info.modules.passport import passport_blu

from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET


@passport_blu.route('/logout')
def logout():
	"""登出"""
	session.pop('mobile')
	session.pop('user_id')
	session.pop('nick_name')
	if session.get('is_admin'):
		session.pop('is_admin')
	return redirect(url_for('index.index'))


# return redirect(url_for('index.index'))


@passport_blu.route('/login', methods=['POST'])
def login():
	"""登录"""
	# 从前端获取数据(手机号/密码)
	data_dict = request.json
	current_app.logger.debug(data_dict)
	mobile = data_dict.get('mobile')
	password = data_dict.get('password')
	# 判空
	if not all([mobile, password]):
		return jsonify(errno=RET.PARAMERR, errmsg='参数错误,参数不完整')
	# 验证手机号
	if not re.match(r'^(13[0-9]|14[5|7]|15[0|1|2|3|5|6|7|8|9]|18[0|1|2|3|5|6|7|8|9])\d{8}$', mobile):
		return jsonify(errno=RET.PARAMERR, errmsg='手机号不符合规范')

	# 通过手机号去mysql中查询密码
	try:
		user = User.query.filter_by(mobile=mobile).first()
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')
	# 判断是否存在user
	if not user:
		return jsonify(errno=RET.USERERR, errmsg='此人不存在')
	# 验证密码是否匹配
	if not user.check_password(password):
		return jsonify(errno=RET.PWDERR, errmsg='密码或用户名输入错误')
	# 保持登录状态
	session['mobile'] = user.mobile
	session['user_id'] = user.id
	session['nick_name'] = user.nick_name
	# 更新最后的登录时间
	user.last_login = datetime.now()
	# 返回状态给前端
	return jsonify(errno=RET.OK, errmsg='登陆成功')


@passport_blu.route('/register', methods=['POST'])
def register():
	"""注册视图"""
	# 获取前端传递的参数(手机号/短信验证/密码)
	data_dict = request.json
	current_app.logger.debug('注册数据:%s' % data_dict)
	mobile = data_dict.get('mobile')
	smscode = data_dict.get('smscode')
	password = data_dict.get('password')
	# 判断参数是否为空
	if not all([mobile, smscode, password]):
		return jsonify(errno=RET.PARAMERR, errmsg='参数错误,参数不完整')
	# 尝试从redis根据手机号取出真实的验证码
	try:
		real_smscode = redis_store.get(mobile).decode()
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')
	# 如果值为none
	if not real_smscode:
		return jsonify(errno=RET.NODATA, errmsg='短信验证过期')
	# 进行匹配验证,如果失败
	if real_smscode != smscode:
		return jsonify(errno=RET.PARAMERR, errmsg='短信验证不匹配')
	# 尝试将参数保存到mysql中
	try:
		user = User()
		user.mobile = mobile
		user.nick_name = mobile
		user.password = password
		# 最后一次登录时间
		user.last_login = datetime.now()
		db.session.add(user)
		db.session.commit()
	except Exception as e:
		current_app.logger.debug(e)
		return jsonify(errno=RET.DATAERR, errmsg='数据库写入失败')
	# 保持登录状态
	session['mobile'] = user.mobile
	session['user_id'] = user.id
	session['nick_name'] = user.nick_name
	# 返回消息给状态信息给前端
	return jsonify(errno=RET.OK, errmsg='注册成功')


@passport_blu.route('/sms_code', methods=['POST'])
def send_sms_code():
	"""发送短信验证功能"""
	# 测试专用
	# return jsonify(errno=RET.OK, errmsg="发送成功")
	# 当点击发送短信时,获取前段发送的数据JSON格式,转换为字典进行操作
	# data_dict = json.loads(request.data)
	data_dict = request.json
	current_app.logger.debug(data_dict)
	# 获取手机号/验证码/uuid,取出来是string
	# mobile = data_dict['mobile']
	mobile = data_dict.get('mobile')
	image_code = data_dict['image_code']
	image_code_id = data_dict['image_code_id']
	# 判断手机号/验证码/uuid是否全部都有值,没有值则报错
	if not all([mobile, image_code, image_code_id]):
		# RET.PARAMERR常量
		return jsonify(errno=RET.PARAMERR, errmsg='参数错误,参数不完整')
	# 如果验证手机号是否符合规范,不规范则报错
	if not re.match(r'^(13[0-9]|14[5|7]|15[0|1|2|3|5|6|7|8|9]|18[0|1|2|3|5|6|7|8|9])\d{8}$', mobile):
		return jsonify(errno=RET.PARAMERR, errmsg='手机号不符合规范')
	# 手机号符合规范,尝试根据image_code_id 去redis获取real_image_code
	try:
		real_image_code = redis_store.get(image_code_id).decode()
		if real_image_code:
			redis_store.delete(image_code_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')
	# 如果取不到值,real_image_code不存在
	if not real_image_code:
		return jsonify(errno=RET.NODATA, errmsg='验证码超时')
	# 验证 验证码与redis中的真实数据是否匹配(忽略大小写)
	if image_code.lower() != real_image_code.lower():
		return jsonify(errno=RET.DATAERR, errmsg='验证码输入错误')
	# 调用第三方发送验证短信
	result = random.randint(0, 999999)
	code = '%06d' % result
	current_app.logger.debug("短信验证码：%s" % code)
	# send_2_mes(int(mobile), int(code))

	# 把手机号和验证码保存到redis
	try:
		redis_store.set(mobile, code, SMS_CODE_REDIS_EXPIRES)
	except Exception as e:
		current_app.logger.error(e)
		# 保存时出现异常
		return jsonify(errno=RET.DBERR, errmsg="保存验证码出现异常")
	# 返回发送成功的响应
	return jsonify(errno=RET.OK, errmsg="发送成功")


@passport_blu.route('/image_code')
def get_image_code():
	"""实现验证码图片显示"""
	# 1.接受把前段uuid并当做img_code_id
	img_code_id = request.args.get('code_id')
	# 2.生成验证码内容value(图片和真实数据)
	name, text, image = captcha.generate_captcha()
	current_app.logger.debug('图片验证码:%s' % text)
	# 3.将uuid和真实数据保存到redis,并添加超时时间
	redis_store.set(img_code_id, text, IMAGE_CODE_REDIS_EXPIRES)
	# 4.设置respons数据的类型
	# 5.创建response对象
	response = make_response(image)
	response.headers["Content-Type"] = "image/jpg"
	# 6.将生成的图片返回给前段展示
	return response
