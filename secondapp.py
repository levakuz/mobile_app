from flask import jsonify, make_response, render_template, Flask
from pymongo import MongoClient
from waitress import serve
import json
import pika
mongo_client = MongoClient('95.181.230.223', 2717, username='dodo_user', password='8K.b>#Jp49:;jUA+')
db = mongo_client.new_database
db_robots = db.robots
users = db.users
db2 = mongo_client.mobile_app
spb = db2.spb
app = Flask(__name__)



@app.route('/dodo/restaurants/<city>')
def get_restaurant_list(city):
    restaurant_list = []
    if city == "Санкт-Петербург":
        for rest in spb.find({}, projection={'_id': False}):
            restaurant_list.append(rest)
        return jsonify(restaurant_list)


@app.route('/makeorder/<order>')
def make_order(order):
    if users.find_one({'order': order, 'status': {'$ne': '5'}}) is not None:
        for user in users.find({'order': order, 'status': {'$ne': '5'}}, projection={'_id': False}):
            print(user)

            return jsonify(user)

    else:
        return 'no order found'


@app.route('/addtable/<order>/<table>')
def add_table(order, table):
    print(order)
    if users.find_one({'order': order, 'status': {'$ne': '5'}}, projection={'_id': False}) is not None:
        print("here")
        users.update_one({'$and': [{'order': order}, {'status': {'$ne': '5'}}]}, {'$set': {'table': table}})
        for user in users.find({'$and': [{'order': order}, {'table': table}]}, projection={'_id': False}):
            if user is None:
                return "Error with DB"
            else:
                print(user)
                return jsonify(user)
    else:
        return 'no order exist'


@app.route('/checkrobot/<order>/<robot>')
def check_robot(order, robot):
    for user in users.find({'$and': [{'status': '4'}, {'order': order}, {'robot_id': robot}]},
                           projection={'_id': False, 'cashbox': False}):
        print(user)
        if user is None:
            print('here1')
            channel.basic_publish(
                exchange='',
                routing_key="robot_delivery_order",
                body='False',
                properties=pika.BasicProperties(
                    delivery_mode=2,
                ))
        else:
            print('here2')
            channel.basic_publish(
                exchange='',
                routing_key="robot_delivery_order",
                body='True',
                properties=pika.BasicProperties(
                    delivery_mode=2,
                ))
    users.update_one({'$and': [{'status': '4'}, {'order': order}, {'robot_id': robot}]}, {'$set': {'status': '5'}})
    for user in users.find({'$and': [{'status': '5'}, {'order': order}, {'robot_id': robot}]},
                           projection={'_id': False, 'cashbox': False}):
        if user is None:
            return 'error'
        else:
            return jsonify(user)


credentials = pika.PlainCredentials('admin', 'admin')
connection = pika.BlockingConnection(pika.ConnectionParameters('95.181.230.223',
                                                               5672,
                                                               '/',
                                                               credentials))

channel = connection.channel()



print(' [*] Waiting for messages. To exit press CTRL+C')
serve(app, host='0.0.0.0', port=8001)
channel.start_consuming()
