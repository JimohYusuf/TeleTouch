from flask import Flask, request
import random

from apscheduler.schedulers.background import BackgroundScheduler
import atexit

clients_size = 19

all_client_states = [0] * clients_size

server = Flask(__name__)

def states_reset():
    for i in range(len(all_client_states)):
        all_client_states[i] = 0
        

scheduler = BackgroundScheduler()
#scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=states_reset, trigger="interval", seconds=60)
scheduler.start() 

atexit.register(lambda: scheduler.shutdown())

@server.route('/client_test_1', methods=['POST', 'GET']) 
def client_test_1(): 
    global all_client_states

    client_id = 1

    value = int(request.args.get('touch'))
    sender_id = int(request.args.get('id'))

    print("Data received: ")
    print(value)

    print("From client: ")
    print(id)

    all_client_states[client_id] = value

    return_value = all_client_states[sender_id]

    # return_value = random.randint(0,1)

    print("Data sent: ")
    print(return_value)

    return str(return_value)

@server.route('/client_test_2', methods=['POST', 'GET']) 
def client_test_2(): 
    data = request.values
    print(data)
    return data
    # global all_client_states

    # client_id = 2

    # value = int(request.args.get('touch'))
    # sender_id = int(request.args.get('id'))

    # print("Data received: ")
    # print(value)

    # print("From client: ")
    # print(id)

    # all_client_states[client_id] = value

    # return_value = all_client_states[sender_id]

    # # return_value = random.randint(0,1)

    # print("Data sent: ")
    # print(return_value)

    # return str(return_value)


if __name__ == '__main__':
   server.run(debug=True, host='192.168.0.101', port='80', threaded=True)   