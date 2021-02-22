# 2021-02-20

import json
from flask import Flask, render_template
app = Flask(__name__)

data = None
with open('data.json') as f:
	data = json.load(f)
	f.close()

@app.route('/')
def index():
	try:
		return render_template('index.html', data=data)
	except Exception as e:
		return e

@app.errorhandler(404)
def not_found(e):
	stripped_data = {
		'title': data['title'],
		'home': data['home'],
		'footer': data['footer']
	}
	return render_template('error.html', data=stripped_data, code="404", e=e)

if __name__=='__main__':
	app.run(debug=True,host='0.0.0.0')
