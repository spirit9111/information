from flask import request

from info import redis_store
from info.constants import IMAGE_CODE_REDIS_EXPIRES
from info.modules.passport import passport_blu

from info.utils.captcha.captcha import captcha


@passport_blu.route('/image_code')
def get_image_code():
	"""实现验证码图片显示"""
	# 1.接受把前段uuid并当做img_code_id
	img_code_id = request.args.get('code_id')
	# 2.生成验证码内容value(图片和真实数据)
	name, text, image = captcha.generate_captcha()
	# 3.将uuid和真实数据保存到redis
	redis_store.set(img_code_id, text, IMAGE_CODE_REDIS_EXPIRES)
	# 4.将生成的图片返回给前段展示
	return image
