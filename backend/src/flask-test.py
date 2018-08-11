from flask import Flask, request, redirect, url_for
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
import os

env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__),"templates/")),
    autoescape=select_autoescape(['html'])
)

app = Flask(__name__)

my_list = [{'a': 4, 'b': 2}, {'a': 9, 'b': 3}]

@app.route("/", methods=['GET'])
def main():
	return env.get_template('flask-test.html').render(my_list=my_list)

@app.route("/add", methods=['POST'])
def add():
	try:
		a = int(request.form['a-field'])
		b = int(request.form['b-field'])
	except ValueError:
		return redirect(url_for('main'))
	my_list.append({'a': a, 'b': b})
	return redirect(url_for('main'))
