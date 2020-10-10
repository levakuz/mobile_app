from flask import Flask, render_template
from flask import Flask, jsonify, make_response
from pymongo import MongoClient
import json
mongo_client = MongoClient('95.181.230.223', 2717, username='dodo_user', password='8K.b>#Jp49:;jUA+')
db = mongo_client.mobile_app
food = db.food


app = Flask(__name__)


@app.route('/food')
def index():
    users_list = []
    for user in food.find({}, projection={'_id': False}):
        users_list.append(user)
        response = jsonify(users_list)
        response = make_response(jsonify(users_list))
    return response


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


