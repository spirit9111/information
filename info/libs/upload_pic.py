from qiniu import Auth, put_data


def upload_pic(pic):
	# 需要填写你的 Access Key 和 Secret Key
	access_key = 'yV4GmNBLOgQK-1Sn3o4jktGLFdFSrlywR2C-hvsW'
	secret_key = 'bixMURPL6tHjrb8QKVg2tm7n9k8C7vaOeQ4MEoeW'
	# 构建鉴权对象
	q = Auth(access_key, secret_key)
	# 要上传的空间
	bucket_name = 'ihome'
	token = q.upload_token(bucket_name)
	ret, info = put_data(token, None, pic)

	if info and info.status_code != 200:
		raise Exception("上传文件到七牛失败")

	return ret.get('key')

