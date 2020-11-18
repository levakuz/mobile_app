
from flask import jsonify, make_response, render_template, Flask
from pymongo import MongoClient
from waitress import serve
import json
mongo_client = MongoClient('95.181.230.223', 2717, username='dodo_user', password='8K.b>#Jp49:;jUA+')
db = mongo_client.mobile_app
food = db.food
categories = db.categories
banners = db.banners
users = db.users
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


@app.route('/categories')
def show_categories():
    categories_list = []
    for categorie in categories.find({}, projection={'_id': False}):
        categories_list.append(categorie)
    return jsonify(categories_list)


@app.route('/banners')
def show_banners():
    banners_list = []
    for banner in banners.find({}, projection={'_id': False}):
        banners_list.append(banner)
    return jsonify(banners_list)


@app.route('/login/<username>/<password>')
def login(username, password):
    if users.find_one({'login':username}) is not None:
        for user in users.find({'login':username}):
            print(user)
            if user['password'] == password:
                return user['token']
            elif user['password'] != password:
                return 'false password'

    else:
        return 'false username'


serve(app, host='0.0.0.0', port=8000)