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


def refresh_bd_users(routing_key):
    for bd in users.find({}, projection={'_id': False}):

        channel.basic_publish(
            exchange='',
            routing_key=routing_key,
            body=json.dumps(bd),
            properties=pika.BasicProperties(
                delivery_mode=2,
            ))
    message = json.dumps('end')
    channel.basic_publish(
        exchange='',
        routing_key=routing_key,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
        ))


def send_message(routing_key, message):
    channel.basic_publish(
        exchange='',
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,
        ))


def send_bd(routing_key, message):
    channel.basic_publish(
        exchange='',
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,
        ))

    message = json.dumps('end')
    channel.basic_publish(
        exchange='',
        routing_key=routing_key,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
        ))


def update_robots(routing_key):
    robots_list = []
    for robot in db_robots.find({}, projection={'_id': False}):
        robots_list.append(robot)
    print(robots_list)
    send_message(routing_key, robots_list)


def get_parsing_orders(ch, method, properties, body):
    """Создает новые спарщенные заказы из полученного массива"""
    print(json.loads(body))
    print(body)

    for j in json.loads(body):
        if users.find_one({'order': j['order'], 'status': {'$ne': '3'}}, projection={'_id': False}) is None:
            users.insert_one(j)
            j.pop('_id')
            print(j)
            send_message('add_order_interface', j)

        else:
            users.find_one_and_update({'$and': [{'order': j['order']}, {'status': {'$lt': '4'}}]},
                                      {'$set': {'status': j['status']}})

    refresh_bd_users('orders')
    refresh_bd_users("orders1")


def clear_data(ch, method, properties, body):
    """При получении сообщения производится очистка базы данных"""
    users.remove()


def order_data_geopos_gui(ch, method, properties, body):
    """Отправляет базу данных заказов в интерфейс пользователя"""
    order_list = []
    print(body)
    print("order data geopos")
    number = json.loads(body)
    print(number['key'])
    if str(number['key']) == "1":
        """Отправка данных о всех заказах"""
        for user in users.find({'status': {'$ne': '5'}},   # Ищу все активные заказы
                               projection={'_id': False}):
            order_list.append(user)
        print(order_list)
        ch.basic_publish(exchange='',                       # Отправка всех активных заказов в очередь ответа
                         routing_key=properties.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                         properties.correlation_id),
                         body=json.dumps(order_list))

    elif str(number['key']) == "2":
        """Отправка данных о конкретном заказе"""
        print(number['order'])
        for user in users.find({'$and': [{'status': {'$ne': '5'}}, {'order': number['order']}]},
                               projection={'_id': False, 'cashbox': False}):
            order_list.append(user)
        ch.basic_publish(exchange='',
                         routing_key=properties.reply_to,
                         properties=pika.BasicProperties(correlation_id=\
                                                         properties.correlation_id),
                         body=json.dumps(order_list))


def robot_db_response(ch, method, properties, body):
    """Производит обновление базы данных роботов"""
    update_robots('robots')


def robot_interface_message(ch, method, properties, body):
    """Принимает сообщение из интерфейса робота и отправляет соответсвующее сообщение в ROS"""
    print(body)
    print('robot interface')
    new_robot_data_list = json.loads(body)
    print(new_robot_data_list)
    print(len(new_robot_data_list))
    for i in range(len(new_robot_data_list)):
        print(new_robot_data_list[i]['id'])
        users.update_one({'$and': [{'order': new_robot_data_list[i]['id']}, {'robot_id': {'$exists': False}},
                                   {'table': {'$exists': True}}, {'status': '3'}]},
                         {'$set': {'robot_id': new_robot_data_list[i]['robot']}})
        users.update_one({'$and': [{'order': new_robot_data_list[i]['id']}, {'robot_id': {'$exists': True}}]},
                         {'$set': {'status': '4'}})
        refresh_bd_users('orders')
        refresh_bd_users("orders1")
    for user in users.find({'$and': [{'order': new_robot_data_list[i]['id']}, {'robot_id': {'$exists': True}}]}):
        print(user['table'])
        channel.basic_publish(
            exchange='',
            routing_key="robot_delivery_order",
            body=user['table'],
            properties=pika.BasicProperties(
                delivery_mode=2,
            ))


def update_robot_status(ch, method, properties, body):
    """Принимает сообщение с id робота и устаналивает ему статус активного"""
    print(body)
    print('update robot')
    new_robot_data = json.loads(body)
    print(new_robot_data)
    db_robots.find_one_and_update({'robot_id': new_robot_data}, {'$set': {'is_active': 1}})
    update_robots('robots')


def robot_db_response_user(ch, method, properties, body):
    """Отправляет базу данных роботов в интерфейс пользователя"""
    robots_list = []
    robot_info = json.loads(body)
    for user in db_robots.find({}, projection={'_id': False}):
        robots_list.append(user)
    ch.basic_publish(exchange='',
                     routing_key=properties.reply_to,
                     properties=pika.BasicProperties(correlation_id= \
                                                     properties.correlation_id),
                     body=json.dumps(robots_list))


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


@app.route('/checkrobot/<order>/<table>')
def check_robot(order, table):
    for user in users.find({'$and': [{'status': '4'}, {'order': order}, {'table': table}]},
                           projection={'_id': False, 'cashbox': False}):
        print(user)
        if user is None:
            channel.basic_publish(
                exchange='',
                routing_key="robot_delivery_order",
                body='False',
                properties=pika.BasicProperties(
                    delivery_mode=2,
                ))
        else:
            channel.basic_publish(
                exchange='',
                routing_key="robot_delivery_order",
                body='True',
                properties=pika.BasicProperties(
                    delivery_mode=2,
                ))
    users.update_one({'$and': [{'status': '4'}, {'order': order}, {'table': table}]}, {'$set': {'status': '5'}})


credentials = pika.PlainCredentials('admin', 'admin')
connection = pika.BlockingConnection(pika.ConnectionParameters('95.181.230.223',
                                                               5672,
                                                               '/',
                                                               credentials))

channel = connection.channel()

"""///////////////////////////////////////////Блок объявления очередей///////////////////////////////////////////////"""
channel.queue_declare(queue='cashboxerrors', durable=True)
channel.queue_declare(queue='tableserrors', durable=True)
channel.queue_declare(queue='bdmodule', durable=True)
channel.queue_declare(queue='bdtables', durable=True)
channel.queue_declare(queue='bdrobots', durable=True)
channel.queue_declare(queue='robots', durable=True)
channel.queue_declare(queue='rfidnums', durable=True)
channel.queue_declare(queue='GetOrders', durable=True)
channel.queue_declare(queue='orders', durable=True)
channel.queue_declare(queue='orders1', durable=False)
channel.queue_declare(queue='robot_delivery_order', durable=False)
channel.queue_declare(queue='parser_clear_data', durable=False)
channel.queue_declare(queue='parser_data', durable=False)
channel.queue_declare(queue='rpc_robots_db', durable=False)
channel.queue_declare(queue='set_selected_orders', durable=False)
channel.queue_declare(queue='set_robot_status', durable=False)
channel.queue_declare(queue='get_robots', durable=False)
channel.queue_declare(queue='rpc_find_order_for_interface', durable=False)
channel.queue_declare(queue='add_order_interface', durable=False)
"""///////////////////////////////////////////Конец блока объявления очередей////////////////////////////////////////"""


channel.basic_consume(queue='get_robots', on_message_callback=robot_db_response, auto_ack=True)
channel.basic_consume(queue='rpc_find_order_for_interface', on_message_callback=order_data_geopos_gui, auto_ack=True)
channel.basic_consume(queue='rpc_robots_db', on_message_callback=robot_db_response_user, auto_ack=True)
channel.basic_consume(queue='set_selected_orders', on_message_callback=robot_interface_message, auto_ack=True)
channel.basic_consume(queue='set_robot_status', on_message_callback=update_robot_status, auto_ack=True)
channel.basic_consume(queue='parser_data', on_message_callback=get_parsing_orders, auto_ack=True)
channel.basic_consume(queue='parser_clear_data', on_message_callback=clear_data, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
serve(app, host='0.0.0.0', port=8001)
channel.start_consuming()
