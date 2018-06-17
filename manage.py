from flask import Flask

app = Flask(__name__)


@app.route('/index')
def index():
	return 'index222222222222'


if __name__ == '__main__':
	app.run()
