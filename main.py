
from flask import jsonify, make_response, render_template, Flask
from pymongo import MongoClient
import json
mongo_client = MongoClient('95.181.230.223', 2717, username='dodo_user', password='8K.b>#Jp49:;jUA+')
db = mongo_client.mobile_app
food = db.food
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Hello wrold!</h1>"


@app.route('/food')
def index():
    users_list = []
    for user in food.find({}, projection={'_id': False}):
        users_list.append(user)
    return jsonify(users_list)


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


app.run(host="0.0.0.0")