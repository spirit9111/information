from . import index_blu


@index_blu.route('/')
@index_blu.route('/index')
def index():
	# logging.debug('111111111111')
	return '<h1>index</h1>'
