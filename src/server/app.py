import atexit
from queue import Queue
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)


MAX_QUEUE_SIZE = 10
RESET_INTERVAL = 60

FAIL        = {'tag': "fail"}
SUCCESS     = {'tag': "success"}
NO_DATA     = {'tag': "no_data"}
BUSY        = {'tag' : "busy"}
NOT_USER    = {'tag' : "not_a_user"}
all_users = {}



class UserQueue():
    def __init__(self, sender):
        self.username = sender
        self.queue = Queue(MAX_QUEUE_SIZE)
        self._busy = 0
        self.active = 0

    def pop(self):
        if self.queue.empty():
            return NO_DATA
        else:
            return self.queue.get()

    def enq(self, data):
        self.queue.put(data)

    def reset(self):
        self.active = 0

    def is_busy(self):
        return self._busy

    def set_busy(self, _buzy):
        self._busy = _buzy

    def set_active(self):
        self.active = 1

    def is_active(self):
        return self.active



def reset():
    for user in all_users.values():
        user.reset()


scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(
                    func=reset,
                    trigger="interval",
                    seconds=RESET_INTERVAL
                  )
scheduler.start()
atexit.register(lambda: scheduler.shutdown())




@app.route('/send', methods=['POST', 'GET'])
def send():
    data        = request.form
    sender      = data['sender']
    receiver    = data['receiver']
    tag         = data['tag']

    if sender in all_users:
        if receiver in all_users and all_users[receiver].is_active():
            if (all_users[receiver].is_busy() == 1) and ( tag == 'real_time_data' or tag == 'rt_accept' or tag == 'rt_decline' or tag == 'rt_stop' ):
                all_users[receiver].enq(data)

            elif all_users[receiver].is_busy() == 0:
                if (tag == 'real_time_data'):
                    return NO_DATA
                else:
                    all_users[receiver].enq(data)

            elif all_users[receiver].is_busy() == 1:
                return BUSY

        else:
            return NOT_USER
    else:
        all_users[sender] = UserQueue(sender)
        if receiver in all_users and all_users[receiver].is_active():
            if (all_users[receiver].is_busy() == 1) and ( tag == 'real_time_data' or tag == 'rt_accept' or tag == 'rt_decline' or tag == 'rt_stop' ):
                all_users[receiver].enq(data)

            elif all_users[receiver].is_busy() == 0:
                if (tag == 'real_time_data'):
                    return NO_DATA
                else:
                    all_users[receiver].enq(data)

            elif all_users[receiver].is_busy() == 1:
                return BUSY

        else:
            return NOT_USER

    all_users[sender].set_active()
    return SUCCESS


@app.route('/check', methods=['POST', 'GET'])
def check():
    data = request.form
    sender = data['sender']

    if sender in all_users:
        all_users[sender].set_active()
        response = all_users[sender].pop()
        return response
    else:
        all_users[sender] = UserQueue(sender)
        all_users[sender].set_active()
        return NO_DATA


@app.route('/active', methods=['POST', 'GET'])
def active():
    data    = request.form
    sender  = data['sender']
    busyy   = int(data['busy'])

    all_users[sender].set_busy(busyy)
    all_users[sender].set_active()

    response = []
    for user in all_users.values():
        if user.is_active():
            response.append(user.username)

    return {'active_users': response}


if __name__ == '__main__':
       app.run(host='0.0.0.0')