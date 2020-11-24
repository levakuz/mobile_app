
from flask import jsonify, make_response, render_template, Flask
from pymongo import MongoClient
from waitress import serve
from datetime import datetime
import json
mongo_client = MongoClient('95.181.230.223', 2717, username='dodo_user', password='8K.b>#Jp49:;jUA+')
db = mongo_client.mobile_app
food = db.food
categories = db.categories
banners = db.banners
users = db.users
orders = db.orders
app = Flask(__name__)

order_number = 0


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


@app.route('/makeorder/<token>')
def make_order(token):
    global order_number
    order_number += 1
    print(order_number)
    str_order = str(order_number)
    if users.find_one({'token': token}) is not None:
        if orders.find_one({'order': str_order, 'user': token, 'status':"1"}, projection={'_id': False}) is None:
            new_order = {'order': str_order, 'user': token, 'time': datetime.strftime(datetime.now(), "%H:%M:%S"),
                         'status': "1"}
            orders.insert_one(new_order)
            new_order = {'order': str_order, 'user': token, 'time': datetime.strftime(datetime.now(), "%H:%M:%S"),
                         'status': "1"}
            print(new_order)
            return jsonify(new_order)
        else:
            return 'this order already exist'
    else:
        return 'no user found'


@app.route('/addtable/<token>/<order>/<table>')
def add_table(token, order, table):
    print(order)
    print(token)
    if orders.find_one({'user': token, 'order': order}) is not None:
        print("here")
        orders.update_one({'$and': [{'order': order}, {'user': token}]}, {'$set': {'table': table}})
        for order in orders.find({'$and': [{'order': order}, {'user': token}]}, projection={'_id': False}):
            print(order)
            return jsonify(order)
    else:
        return 'no order exist'


serve(app, host='0.0.0.0', port=8000)