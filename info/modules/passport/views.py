import random
import re

from flask import request, json, jsonify, current_app
from info import redis_store
from info.constants import IMAGE_CODE_REDIS_EXPIRES, SMS_CODE_REDIS_EXPIRES
from info.libs.dysms_python.send_2_mes import send_2_mes
from info.modules.passport import passport_blu

from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET


@passport_blu.route('/image_code')
def get_image_code():
	"""实现验证码图片显示"""
	# 1.接受把前段uuid并当做img_code_id
	img_code_id = request.args.get('code_id')
	# 2.生成验证码内容value(图片和真实数据)
	name, text, image = captcha.generate_captcha()
	# 3.将uuid和真实数据保存到redis,并添加超时时间
	redis_store.set(img_code_id, text, IMAGE_CODE_REDIS_EXPIRES)
	# 4.将生成的图片返回给前段展示
	return image


@passport_blu.route('/register', methods=['POST', 'GET'])
def register():
	pass
	# 当点击发送短信时,获取前段发送的数据JSON格式,转换为字典进行操作
	data_dict = json.loads(request.data)
	# 获取手机号/验证码/uuid,取出来是string
	mobile = data_dict['mobile']
	image_code = data_dict['image_code']
	image_code_id = data_dict['image_code_id']
	# 判断手机号/验证码/uuid是否全部都有值,没有值则报错
	if not all([mobile, image_code, image_code_id]):
		# RET.PARAMERR常量
		return jsonify(errno=RET.PARAMERR, errmsg='参数错误,参数不完整')
	# 如果验证手机号是否符合规范,不规范则报错
	if re.match(r'^(13[0-9]|14[5|7]|15[0|1|2|3|5|6|7|8|9]|18[0|1|2|3|5|6|7|8|9])\d{8}$', mobile):
		return jsonify(errno=RET.PARAMERR, errmsg='手机号不符合规范')
	# 手机号符合规范,尝试根据image_code_id 去redis获取real_image_code
	try:
		real_image_code = redis_store.get(image_code_id)
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
	send_2_mes(mobile, code)

	# 把手机号和验证码保存到redis
	try:
		redis_store.set(mobile, code, SMS_CODE_REDIS_EXPIRES)
	except Exception as e:
		current_app.logger.error(e)
		# 保存时出现异常
		return jsonify(errno=RET.DBERR, errmsg="保存验证码出现异常")

	# 7. 返回发送成功的响应
	return jsonify(errno=RET.OK, errmsg="发送成功")
