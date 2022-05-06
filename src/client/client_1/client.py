from tkinter.ttk import *
import tkinter as tk
from ctypes.wintypes import MSG, SERVICE_STATUS_HANDLE
from tkinter import OptionMenu, StringVar, messagebox
import concurrent.futures
from threading import Thread, Event
import functools
import requests
import sqlite3
import serial


def threaded(func):
    """Decorator to automatically launch a function in a thread"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # replaces original function...
        # ...and launches the original in a thread
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper
###############################################################################################################################################################
################################################### INIT GUI ##################################################################################################
###############################################################################################################################################################

bg_color = "#34495E"
root = tk.Tk()
root.title("Touch")
root.geometry('800x700')
root.resizable(0, 0)
root.configure(background=bg_color)

root_menu = tk.Menu(root,type="menubar") 
root.config(menu=root_menu)


tk.Label(
            root, 
            text='New York University Abu Dhabi', 
            bg=bg_color,
            font=('calibri', 10), 
            fg='white').pack(side='bottom'
        )
frame = tk.Frame(root, bg="white")
frame.place(relwidth=0.9, relheight=0.9, relx=0.05, rely=0.05)

style = Style()
style.theme_use('classic')
style.configure(
                'TButton',
                font=('calibri', 15),
                borderwidth='0',
                background=bg_color,
                foreground="white",
                width=30
                )
style.map(
            'TButton', 
            foreground=[('active', bg_color)], 
            background=[('active', '#DDE2ED')]
         )

###############################################################################################################################################################
################################################### INIT GUI END ##############################################################################################
###############################################################################################################################################################


###############################################################################################################################################################
################################################### GLOBAL VARIABLES ##########################################################################################
###############################################################################################################################################################
'''
    MESSAGE_BUFFER_DELAY  - is the extra delay (in ms) added to pad a message. Basically so that
                            there is some delay before playing another message after one message has been played.
    ACTIVE_USERS_DELAY    - This delay (in ms) represents how often the application gets the list of
                            active users from the server.
    GET_DATA_DELAY        - This delay (in ms) represents how often the application queries the server to
                            check if it has a real-time data or prerecorded message from a user.
    BUSY                  - indicates whether this user is busy or not. This data is communcated to the server every
                            ACTIVE_USERS_DELAY in function get_active_users to inform the server of its the user's state.
    GET_TIMEOUT           - Timeout delay for all http POST requests
'''
MESSAGE_BUFFER_DELAY = 5
ACTIVE_USERS_DELAY = 1000
GET_DATA_DELAY = 200
MAX_GET_DELAY  = 120000
DELAY_INCREASE = 1000
GET_TIMEOUT = 1
BUSY = 0
ERROR = "ERROR"


'''
    SERVER_ADDRESS  - stores the address of the server
    PORT_ADDRESS    - stores the port no/address
    SERVER_SET      - indicates if the server address has been successfully set
    PORT_SET        - indicates if the port no/address has been successfully set
'''
SERVER_ADDRESS = ""
PORT_ADDRESS = ""
SERVER_SET = 0
PORT_SET = 0


''' 
    TAGS - Any of this tags may be sent to the server with every message. 
           The server needs the tag to detrmine how to handle the data.
'''
TAG_RT_REQUEST = "send_rtdata"
TAG_GET_DATA   = "get_data"
TAG_GET_ACTIVE = "get_active"
TAG_SEND_DATA  = "send_data"
TAG_NO_DATA    = "no_data"
TAG_RT_ACCEPT  = "rt_accept"
TAG_RT_DECLINE = "rt_decline"
TAG_RT_DATA    = "real_time_data"
TAG_RT_STOP    = "rt_stop"

'''
    active participants - holds the list of active participants from the server
    sender              - is the name of this user
'''
active_participants = [""]
sender = ""

################################################################################################################################################################
################################################### GLOBAL VARIABLES END #######################################################################################
################################################################################################################################################################


###############################################################################################################################################################
############################################# INIT USERNAME, PORT, SERVER_ADDRESS #############################################################################
###############################################################################################################################################################
'''
    init_username tries to initialize the username (sender) on startup. It checks the database
    for the username.
'''

def init_username():
    global sender
    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()

        curs.execute("SELECT * FROM user")
        data = curs.fetchone()
        print("loading user: ", data)

        if data is None:
            print("(init_username) no user account")
            pass
        else:
            sender = data[0] + " " + data[1]
            print("(init_username) sender name set on start: ", sender)
    except Exception as e:
        print("(init_username)(exception) username fetch: ", e)
    return


init_username()

tk.Label(root, text=sender, bg=bg_color, font=(
    'calibri', 10, 'bold'), fg='white').pack(side='top')

#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#
'''
    init_serv_addr tries to get the server address on startup. It checks the database for the 
    server address.
'''

def init_serv_addr():
    global SERVER_ADDRESS
    global SERVER_SET

    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()

        curs.execute("SELECT * FROM server_address")
        data = curs.fetchone()
        print("fetching server address: ", data)

        if data is None:
            print("(init_serv_addr) server dne")
        else:
            SERVER_ADDRESS = data[0]
            SERVER_SET = 1
            print("(init_serv_addr) server address fetched: ", SERVER_ADDRESS)
    except Exception as e:
        print("(init_serv_addr)(exception) server address fetch: ", e)
    return


#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#
'''
    set_server makes the web endpoints (send/check/active) from the server address. 
    set_server is called whenever there is a change to the SERVER_ADDRESS variable.
'''


def set_server():
    global SERVER_ADDRESS
    global SEND_URL
    global GET_URL
    global ACTIVE_USER_URL
    global SERVER_SET

    if SERVER_ADDRESS == "":
        SEND_URL = "http://15.185.167.245/send"
        GET_URL = "http://15.185.167.245/check"
        ACTIVE_USER_URL = "http://15.185.167.245/active"
    else:
        SEND_URL = "http://" + SERVER_ADDRESS + "/send"
        GET_URL = "http://" + SERVER_ADDRESS + "/check"
        ACTIVE_USER_URL = "http://" + SERVER_ADDRESS + "/active"
    
    SERVER_SET = 1

    return


#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#

init_serv_addr()
set_server()

#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#
'''
    init_port attempts to set the PORT_ADDRESS and PORT_SET variables on startup. It checks the databse for the
    variable values.
'''

def init_port():
    global PORT_ADDRESS

    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()

        curs.execute("SELECT * FROM port")
        data = curs.fetchone()
        print("fetching port: ", data)

        if data is None:
            print("(init_port) port dne")
        else:
            PORT_ADDRESS = data[0]
            print("(init_port) port fetched: ", PORT_ADDRESS)
    except Exception as e:
        print("(init_port)(exception) port fetch ", e)
    return


#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#
'''
    This is a first attempt to connect to the serial port on startup.
'''

try:
    ser = serial.Serial(PORT_ADDRESS, 115200)
    PORT_SET = 1
except:
    ser = None


'''
    set_port is called whenever there is a change to the PORT_ADDRESS variable.
'''

def set_port():
    global ser
    global PORT_SET
    if not ser:
        try:
            ser = serial.Serial(PORT_ADDRESS, 115200)
            PORT_SET = 1
        except Exception as e:
            PORT_SET = 0
            print("(set_port)(exception): ", e)
    return

#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#

init_port()
set_port()

################################################################################################################################################################
################################################### INIT USERNAME, PORT, SERVER_ADDRESS END ####################################################################
################################################################################################################################################################


################################################################################################################################################################
################################################### FUNCTIONS BEGIN ############################################################################################
################################################################################################################################################################

'''
    request_post sends out all requests
'''

def request_post(_url, _data):
    return requests.post(url=_url, data=_data, timeout=GET_TIMEOUT).json()


'''
    on_closing_top is called when any other than the root and real-time windows is closed by the user. 
    it destroys all of such openned window.
'''

def on_closing_top():
    global BUSY
    global RT_BUSY
    BUSY = 0
    RT_BUSY = 0
    for wind in top_windows:
        wind.destroy()
    return


'''
    on_closing_top is called if the real-time connection window is closed by the user without 
    disconnecting from the real-time connection. 
    it marks the user as not busy and send a stop message to the other client.
'''

def on_closing_tp():
    global BUSY
    global RT_BUSY
    BUSY = 0
    RT_BUSY = 0

    try:
        _data = {'sender': str(
            sender), 'receiver': CURRENT_ACTIVE_CONNECT, 'tag': "rt_stop"}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            response = executor.submit(request_post, SEND_URL, _data)
    except Exception as e:
        print("(stop_rt)(exception): ", e)

    for wind in tp_windows:
        wind.destroy()
    return


'''
    on_closing_root is called when the root window is closed by the user. It destroys itself.
'''

def on_closing_root():
    global BUSY
    global RT_BUSY
    BUSY = 0
    RT_BUSY = 0
    root.quit() 
    return

'''
    check status provides information of whether the port number to the arduino and the server
    address have been set successfully.
'''
def check_status():
    top = tk.Toplevel()
    top.title("Status") 
    top.geometry('400x250')
    top.resizable(0, 0)
    top.configure(background=bg_color)

    top_windows.append(top)

    pad_x = 20
    pad_y = 15

    server_stat = "Server Status:   NOT SET"
    port_stat   = "Port Status:     NOT SET"
    if SERVER_SET:
        server_stat = "Server Status:   SET"
    if PORT_SET:
        port_stat = "Port Status:   SET"
    
    tk.Label(top, text=server_stat, font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)
    tk.Label(top, text=port_stat, font=('calibri', 13, 'bold'),
    background=bg_color, fg='white').grid(row=1, column=0, padx=pad_x, pady=pad_y)

    return
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
ShowInfo    - info gui popup
MessageBox  - message popup
'''

def ShowInfo(label, message):
    messagebox.showinfo(label, message)
    return


def MessageBox(label, message):
    thrd = Thread(target=ShowInfo, args=[label, message])
    thrd.start()
    return
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


'''
    send_rtdata handles sending real-time data when the user has is connected to another user in 
    real-time mode. 
'''

def send_rtdata(recvr, top):
    global BUSY
    global RT_BUSY
    global RT_RECEIVER
    print("(send_rtdata) receiver selected", recvr)

    try:
        if sender:
            _data = {'sender': str(sender), 'receiver': str(
                recvr), 'tag': "send_rtdata"}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = executor.submit(request_post, SEND_URL, _data)
                response = response.result()
                print("response ", response)
                if response:
                    print("(send_rtdata, " + sender + " ): ")

                    if (response['tag'] == "busy"):
                        MessageBox(
                            "Busy", "User is busy. Try again after some time")
                    elif response['tag'] == "not_a_user":
                        MessageBox("Not a User", "Receiver does not exist")
                    elif response['tag'] == "no_data":
                        pass
                    else:
                        MessageBox(
                            "Connect", "Connection request sent. Wait for response")
                        RT_RECEIVER = str(recvr)
                        BUSY = 1
                        RT_BUSY = 1
                else:
                    print("(send_rtdata) no response")
        else:
            MessageBox("Error", "Create a user account to send messages")
            top.destroy()
    except Exception as e:
        print("((exception) send_rtdata) ", e)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
top_windows = []

'''
    send_rtmessage handles real-time connection GUI
'''

def send_rtmessage():
    top = tk.Toplevel()
    top.title("Real Time")
    top.geometry('400x250')
    top.resizable(0, 0)
    top.configure(background=bg_color)

    top_windows.append(top)

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="Receiver", font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    partcpnt = StringVar()
    drop = OptionMenu(top, partcpnt, *active_participants)
    drop.grid(row=0, column=1, padx=pad_x, pady=pad_y)
    drop.configure(background=bg_color, fg='white',
                   font=('calibri', 13, 'bold'))

    submit_btn = tk.Button(top, text="Connect",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: send_rtdata(partcpnt.get(), top))
    submit_btn.grid(row=2, column=1, padx=pad_x, pady=pad_y)

    top.protocol("WM_DELETE_WINDOW", on_closing_top)
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

''' 
    send_data handles the sending of prerecorded messages (Hapticonsr)? 
'''

def send_data(actvty, recvr, top):
    global MSG_MODE

    if sender:
        if not actvty or not recvr:
            MessageBox("Alert", "No activity or receiver selected")
            return

        print("(send_data) activity selected: ", actvty)
        print("(send_data) receiver selected", recvr)

        try:
            conn = sqlite3.connect('user.db')
            curs = conn.cursor()
            print("(send_data) connected to database")

            curs.execute("SELECT * FROM activity WHERE activity_name = :actv",
                         {
                             'actv': actvty
                         })

            data = curs.fetchone()

            print("(send_data) activity data from db", data)
            motors = data[1]
            duration = data[2]
            intensity = data[3] 
            receiver = recvr
            activity = actvty

            print("(send_data) Duration arrar: ", duration)
            _data = {
                'sender': str(sender),
                'receiver': str(receiver),
                'activity': str(activity),
                'motors': str(motors),
                'duration': str(duration),
                'intensity':str(intensity),
                'tag': "send_data"
            }

            if (recvr == 'Self'):
                motors    = str(motors).replace(",","")
                duration  = str(duration).replace(",","")
                intensity = str(intensity).replace(",","")
                arduino_data = str(motors) + "s" + str(duration) + "s" + str(intensity)
                print("(send_data): arduino data", arduino_data)
                to_arduino(arduino_data, MSG_MODE)
            else:
                print("(send_data) request to server initiated")
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    response = executor.submit(request_post, SEND_URL, _data)
                    response = response.result()

                if (response['tag'] == "busy"):
                    MessageBox("Busy", "User is busy. Try again after some time")
                elif response['tag'] == "not_a_user":
                    MessageBox("Not a User", "Receiver does not exist")
                elif response['tag'] == "no_data":
                    pass
                else:
                    MessageBox("Success", "Message sent successfully")

            #top.destroy()

            conn.commit()
            conn.close()
        except Exception as e:
            MessageBox("Error", "Could not send message")
            top.destroy()
            print("(send_data)(exception): ", e)
    else:
        MessageBox("Error", "Create a user account to send messages")
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    send_message handles prerecorded message GUI
'''

def send_message():
    top = tk.Toplevel()
    top.title("Send Message")
    top.geometry('500x300')
    top.resizable(0, 0)
    top.configure(background=bg_color)

    pad_x = 20
    pad_y = 20
    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()

        curs.execute(
            "CREATE TABLE IF NOT EXISTS activity (activity_name text PRIMARY KEY, motors text, duration text)")
        curs.execute("SELECT *,oid FROM activity")
        data = curs.fetchall()

        tk.Label(top, text="Haptic Message",  font=('calibri', 13, 'bold'),
                 background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)
        tk.Label(top, text="Receiver", font=('calibri', 13, 'bold'),
                 background=bg_color, fg='white').grid(row=1, column=0, padx=pad_x, pady=pad_y)

        activities = [""] 
        activities_2 = []
        if data is None:
            print("no activity exists yet")
            MessageBox("Activity", "You have no activity yet")
        else:
            for activity in data:
                activities_2.append(activity[0])

            if(len(activities_2) != 0):
                activities = activities_2

            actvty = StringVar()
            #actvty.set(activities[0])
            drop1 = OptionMenu(top, actvty, *activities)
            drop1.grid(row=0, column=1, padx=pad_x, pady=pad_y)
            drop1.configure(background=bg_color, fg='white',
                            font=('calibri', 13, 'bold'), width=7)

            partcpnt = StringVar()
            partcpnt.set(active_participants[0])
            drop2 = OptionMenu(top, partcpnt, *active_participants)
            drop2.grid(row=1, column=1, padx=pad_x, pady=pad_y)
            drop2.configure(background=bg_color, fg='white',
                            font=('calibri', 13, 'bold'), width=7)


        conn.commit()
        conn.close()
    except Exception as e:
        MessageBox("DB Error", "Something Went Wrong With the Database")
        print("(send_message)(exception): ", e)
        return

    submit_btn = tk.Button(top, text="Send",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: send_data(actvty.get(), partcpnt.get(), top))
    submit_btn.grid(row=2, column=1, padx=pad_x, pady=pad_y)

    return

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    delete_activity_gui deletes an activity from the database
'''
def delete_activity(actvty, top):
    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()

        curs.execute("DELETE FROM activity WHERE activity_name=:actvty_name",
                     {
                         'actvty_name': actvty,
                     })

        conn.commit()
        conn.close()
        MessageBox("Delete Activity", "You have successfully deleted " + actvty)
        top.destroy()

    except Exception as e:
        MessageBox("DB Error", "Something Went Wrong With the Database")
        print("(send_message)(exception): ", e)
        return

    return


'''
    delete_activity_gui: gui that calls delete_activity
'''
def delete_activity_gui():
    top = tk.Toplevel()
    top.title("Send Message")
    top.geometry('400x200')
    top.resizable(0, 0)
    top.configure(background=bg_color)

    pad_x = 20
    pad_y = 20
    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()

        curs.execute(
            "CREATE TABLE IF NOT EXISTS activity (activity_name text PRIMARY KEY, motors text, duration text)")
        curs.execute("SELECT *,oid FROM activity")
        data = curs.fetchall()

        tk.Label(top, text="Haptic Message",  font=('calibri', 13, 'bold'),
                 background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)
        tk.Label(top, text="Receiver", font=('calibri', 13, 'bold'),
                 background=bg_color, fg='white').grid(row=1, column=0, padx=pad_x, pady=pad_y)

        activities = [""]

        if data is None:
            print("no activity exists yet")
            MessageBox("Activity", "You have no activity yet")
        else:
            for activity in data:
                activities.append(activity[0])

            actvty = StringVar()
            actvty.set(activities[0])
            drop1 = OptionMenu(top, actvty, *activities)
            drop1.grid(row=0, column=1, padx=pad_x, pady=pad_y)
            drop1.configure(background=bg_color, fg='white',
                            font=('calibri', 13, 'bold'))

        conn.commit()
        conn.close()
    except Exception as e:
        MessageBox("DB Error", "Something Went Wrong With the Database")
        print("(send_message)(exception): ", e)
        return

    submit_btn = tk.Button(top, text="Delete",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: delete_activity(actvty.get(),top))
    submit_btn.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    return

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
n_motors = []
n_duration = []
n_intensity = []
buttons = []

motor_objects = []
duration_objects = []
intensity_objects = []
indx_objects = []

'''
    activity_to_db handles storing prerecorded message to the database
'''

def activity_to_db(actv_name, drop_obj, activity_name, top):
    global n_motors
    global n_duration
    global n_intensity
    global buttons

    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()
        curs.execute(
            "CREATE TABLE IF NOT EXISTS activity (activity_name text PRIMARY KEY, motors text, duration text, intensity text)") 
        motor_arr = []
        dur_arr = []
        int_arr = []

        # print("name: ", actv_name)
        # print("motor: ", n_motors)
        # print("duration: ", n_duration)

        for motor in n_motors:
            try:
                test = int(motor.get())  # to throw error if not int
                data = motor.get()
                if not data:
                    MessageBox("Incomplete Entry",
                               "Enter a value in every field")
                    return
                elif (test < 0) or (test > 4):
                    MessageBox("Invalid Input",
                               "Motor number can only be 1, 2, 3, or 4") 
                    return
                motor_arr.append(data)
            except Exception as e:
                print("(activity_to_db)(exception): ", e)
                MessageBox("Error", "Motor Number must be an integer")
                return

        for dur in n_duration:
            try:
                test = int(dur.get())
                data = dur.get()
                if not data:
                    MessageBox("Incomplete Entry",
                               "Enter a value in every field")
                    return
                elif (test < 1) or (test > 9):
                    MessageBox("Invalid Input",
                               "Duration must be an integer from 1 to 9 ") 
                    return
                dur_arr.append(str(data))
            except Exception as e:
                print("(activity_to_db)(exception): ", e)
                MessageBox("Error", "Duration must be an integer")
                return
        
        for val in n_intensity:
            try:
                test = int(val.get())
                data = val.get()
                if not data:
                    MessageBox("Incomplete Entry",
                               "Enter a value in every field")
                    return
                elif (test < 1) or (test > 9):
                    MessageBox("Invalid Input",
                               "Duration must be an integer from 1 to 9 ") 
                    return
                int_arr.append(str(data))
            except Exception as e:
                print("(activity_to_db)(exception): ", e)
                MessageBox("Error", "Duration must be an integer")
                return

        print("motors: ", motor_arr)
        print("durations", dur_arr)
        print("intensities", int_arr)

        str_motors = ",".join(motor_arr)
        str_duration = ",".join(dur_arr)
        str_intensity = ",".join(int_arr)

        print(str_motors)
        print(str_duration)
        print(str_intensity)

        curs.execute("INSERT INTO activity VALUES (:activity_name, :motors, :duration, :intensity)",
                     {
                         'activity_name': str(actv_name),
                         'motors': str(str_motors),
                         'duration': str(str_duration),
                         'intensity':str(str_intensity)
                     })

        conn.commit()
        conn.close()

        for obj in motor_objects:
            obj.destroy()
        for obj in duration_objects:
            obj.destroy()
        for obj in intensity_objects:
            obj.destroy()
        for obj in indx_objects:
            obj.destroy()

        motor_objects.clear()
        duration_objects.clear()
        intensity_objects.clear() 
        indx_objects.clear() 

        MessageBox("Success", "Successfully added new activity!")
        #top.destroy()
    except Exception as e:
        print("(activity_to_db)(exception): ", e)
        MessageBox("Error", "Something went wrong. Try again or Ask for assistance. Also make sure that you have not added this activity before.")
        drop_obj.config(state='normal')
        activity_name.config(state='normal')
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    get_activity_detail handles message prerecording GUI. 
    Calls activity_to_db to store the prerecorded activity details it gets.
'''

def test_activity():
    global MSG_MODE
    motor_arr = []
    dur_arr = []
    int_arr = []

    for motor in n_motors:
        try:
            test = int(motor.get())  # to throw error if not int
            data = motor.get()
            if not data:
                MessageBox("Incomplete Entry",
                            "Enter a value in every field")
                return
            elif (test < 0) or (test > 4):
                MessageBox("Invalid Input",
                            "Motor number can only be 1, 2, 3, or 4") 
                return
            motor_arr.append(data)
        except Exception as e:
            print("(activity_to_db)(exception): ", e)
            MessageBox("Error", "Motor Number must be an integer")
            return

    for dur in n_duration:
        try:
            test = int(dur.get())
            data = dur.get()
            if not data:
                MessageBox("Incomplete Entry",
                            "Enter a value in every field")
                return
            elif (test < 1) or (test > 9):
                MessageBox("Invalid Input",
                            "Duration must be an integer from 1 to 9 ") 
                return
            dur_arr.append(str(data))
        except Exception as e:
            print("(activity_to_db)(exception): ", e)
            MessageBox("Error", "Duration must be an integer")
            return

    for val in n_intensity:
        try:
            test = int(val.get())
            data = val.get()
            if not data:
                MessageBox("Incomplete Entry",
                            "Enter a value in every field")
                return
            elif (test < 1) or (test > 9):
                MessageBox("Invalid Input",
                            "Duration must be an integer from 1 to 9 ") 
                return
            int_arr.append(str(data))
        except Exception as e:
            print("(activity_to_db)(exception): ", e)
            MessageBox("Error", "Duration must be an integer")
            return

    
    str_motors = "".join(motor_arr)
    str_duration = "".join(dur_arr) 
    str_intensity = "".join(int_arr)

    arduino_data = str_motors + "s" + str_duration + "s" + str_intensity
    to_arduino(arduino_data, MSG_MODE)
    print("(test_activity): arduino_data: ", arduino_data) 
    print("(test_activity): Running activity test") 



def get_activity_detail(actv_name, top, no_motors, drop_obj, activity_name):
    global n_motors
    global n_duration
    global n_intensity
    global buttons

    s_length = None
    try:
        s_length = int(no_motors.get())
    except Exception as e:
        print("(get_activity_detail)(exception): ", e)
        print("s_length: ", s_length)
        MessageBox("Error", "No of vibration motors must be an integer")
        
        return
    
    print("(get_activity_detail) activity name: ", actv_name) 
    if not actv_name:
        MessageBox("Error", "Activity must have a name")
        return

    try:
        pad_x = 5
        pad_y = 5

        for obj in motor_objects:
            obj.destroy()
        for obj in duration_objects:
            obj.destroy()
        for obj in intensity_objects:
            obj.destroy()
        for obj in indx_objects:
            obj.destroy()
        for btn in buttons:
            btn.destroy()

        motor_objects.clear()
        duration_objects.clear()
        intensity_objects.clear() 
        indx_objects.clear()
        
        n_motors.clear()
        n_duration.clear()
        n_intensity.clear() 
        buttons.clear()

        #drop_obj.config(state='disabled')
        #activity_name.config(state='disabled')
        tk.Label(top, text="Motor Number",  font=('calibri', 13, 'bold'),
                 background=bg_color, fg='white').grid(row=3, column=1, padx=pad_x, pady=pad_y)
        tk.Label(top, text="Duration", font=('calibri', 13, 'bold'),
                 background=bg_color, fg='white').grid(row=3, column=2, padx=pad_x, pady=pad_y)
        tk.Label(top, text="Intensity", font=('calibri', 13, 'bold'),
                 background=bg_color, fg='white').grid(row=3, column=3, padx=pad_x, pady=pad_y)

        cnt = 1
        row_cnt = 4

        
        for a in range(s_length):
            indx = tk.Label(top, text=cnt, font=('calibri', 13), background=bg_color,
                     fg='white')
            indx.grid(row=row_cnt, column=0, padx=2, pady=pad_y)

            # motor_no = tk.Entry(top, width=10, bg="white",
            #                     borderwidth=2, font=('calibri', 13))
            # motor_no.grid(row=row_cnt, column=1, padx=pad_x, pady=pad_y)
            motor_arr = [0,1,2,3,4] 
            motor_no = StringVar()
            drop_motor = OptionMenu(top, motor_no, *motor_arr) 
            drop_motor.grid(row=row_cnt, column=1, padx=pad_x, pady=pad_y)
            drop_motor.configure(background='white', fg='black',
                            font=('calibri', 13, 'bold'), width=10, height=1)  


            duration = tk.IntVar()
            duration.set(1) 
            duration_slider = tk.ttk.Scale(
                top,
                from_=1,
                to=3,
                orient='horizontal',
                variable=duration,
            )
            # duration = tk.Entry(top, width=10, bg="white",
            #                     borderwidth=2, font=('calibri', 13))
            duration_slider.grid(row=row_cnt, column=2, padx=pad_x, pady=pad_y)

            intensity = tk.IntVar()
            intensity.set(1)
            intensity_slider = tk.ttk.Scale(
                top,
                from_=1,
                to=3,
                orient='horizontal',
                variable=intensity,
            )        
            
            intensity_slider.grid(row=row_cnt, column=3, padx=pad_x, pady=pad_y)

            motor_objects.append(drop_motor)
            duration_objects.append(duration_slider)
            intensity_objects.append(intensity_slider)
            indx_objects.append(indx)

            n_motors.append(motor_no)
            n_duration.append(duration)
            n_intensity.append(intensity) 


            cnt = cnt + 1
            row_cnt = row_cnt + 1

        add_btn = tk.Button(top, text="Add Activity",
                            font=('calibri', 13), width=15,
                            background='#D1D5D7',
                            command=lambda: activity_to_db(actv_name, drop_obj, activity_name, top))
        add_btn.grid(row=row_cnt, column=2, padx=pad_x, pady=pad_y)

        row_cnt += 1

        test_btn = tk.Button(top, text="Test Activity",
                            font=('calibri', 13), width=15,
                            background='#D1D5D7',
                            command=lambda: test_activity())
        test_btn.grid(row=row_cnt, column=2, padx=pad_x, pady=pad_y)

        buttons.append(add_btn)
        buttons.append(test_btn) 
    except Exception as e:
        print("(get_activity_detail)(exception): ", e)
        drop_obj.config(state='normal')
        activity_name.config(state='normal') 
        MessageBox(
            "Error", "Something went wrong. Try again or Ask for assistance")

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    create_activity handles the initial window openend when creating a prerecorded message.
'''

def create_activity_gui():
    top = tk.Toplevel()
    top.title("Create Activity")
    top.geometry('700x800')
    top.resizable(0, 1)
    top.configure(background=bg_color)

    pad_x = 15
    pad_y = 15

    tk.Label(top, text="Activity Name",  font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)
    activity_name = tk.Entry(top, width=20, bg="white",
                             borderwidth=2, font=('calibri', 13))
    activity_name.grid(row=0, column=1, padx=pad_x, pady=pad_y)

    tk.Label(top, text="No. of Motors",  font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=1, column=0, padx=pad_x, pady=pad_y)

    vibr_no_range = [1,2,3,4,5,6,7,8,9,10] 
    no_vibr_motor = StringVar() 
    # no_vibr_motor.set("1") 
    drop1 = OptionMenu(top, no_vibr_motor, *vibr_no_range) 
    drop1.grid(row=1, column=1, padx=pad_x, pady=pad_y)
    drop1.configure(background='white', fg='black',
                    font=('calibri', 13, 'bold'), width=15)

    # sequence_length = tk.Entry(
    #     top, width=20, bg="white", borderwidth=2, font=('calibri', 13))
    # sequence_length.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    create_btn = tk.Button(top, text="Create",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: get_activity_detail(activity_name.get(), top, no_vibr_motor,drop1, activity_name))
    create_btn.grid(row=2, column=1, padx=pad_x, pady=pad_y)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    save_port sets and stores the new port set by the user to the database.
    Calls set_port to attempt connection to the port with the new port no/address.
'''

def save_port(port_no, top):
    global PORT_ADDRESS

    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()
        curs.execute("CREATE TABLE IF NOT EXISTS port (port_no text)")
        curs.execute("SELECT *,oid FROM port")
        data = curs.fetchone()

        try:
            test = port_no.get()
        except Exception as e:
            print("(save_port): ", e)
            MessageBox("Error", "Port number must be an integer")
            return

        port = port_no.get()

        if data is None:
            print("port DNE")
            curs.execute("INSERT INTO port VALUES (:port_no)",
                         {
                             'port_no': port,

                         })
            MessageBox("COM Port", "Port saved successfully!")
        else:
            print("port exists")
            curs.execute("UPDATE port SET port_no = :portt WHERE oid = :id",
                         {
                             'portt': port,
                             'id': 1
                         })
            MessageBox("COM Port", "Port updated successfully!")

        PORT_ADDRESS = port
        set_port()
        print("(save_port): port updated by user to ", port)

        conn.commit()
        conn.close()
    except Exception as e:
        print("(save_port): ", e)
        MessageBox("DB Error", "Something Went Wrong With the Database")

    top.destroy()

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    get_port handles the port setting GUI
'''

def get_port():
    top = tk.Toplevel()
    top.title("Account")
    top.geometry('500x300')
    top.resizable(0, 0)
    top.configure(background=bg_color)

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="Port Number",  font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    port_no = tk.Entry(top, width=20, bg="white",
                       borderwidth=2, font=('calibri', 13))
    port_no.grid(row=0, column=1, padx=pad_x, pady=pad_y)

    submit_btn = tk.Button(top, text="Submit",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: save_port(port_no, top))
    submit_btn.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    save_serv_addr sets and stores the new server address set by the user to the database.
    Calls set_server to attempt connection to update the request endpoints.
'''

def save_serv_addr(serv_addr, top):
    global SEND_URL
    global GET_URL
    global ACTIVE_USER_URL
    global SERVER_ADDRESS

    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()
        curs.execute(
            "CREATE TABLE IF NOT EXISTS server_address (serv_addr text)")
        curs.execute("SELECT *,oid FROM server_address")
        data = curs.fetchone()

        try:
            test = serv_addr.get()
        except Exception as e:
            print("(save_serv_addr): ", e)
            MessageBox("Error", "Port number must be an integer")
            return

        server_addr = serv_addr.get()

        if data is None:
            print("server dne")
            curs.execute("INSERT INTO server_address VALUES (:serv_addr)",
                         {
                             'serv_addr': server_addr,

                         })
            MessageBox("Server Address", "Server address successfully saved!")
        else:
            print("server exists")
            curs.execute("UPDATE server_address SET serv_addr = :servv WHERE oid = :id",
                         {
                             'servv': server_addr,
                             'id': 1
                         })
            MessageBox("Server Address",
                       "Server address successfully updated!")

        SERVER_ADDRESS = server_addr
        set_server()

        print("(save_serv_addr): Server address updated by user")

        conn.commit()
        conn.close()
    except Exception as e:
        print("(save_serv_addr): ", e)
        MessageBox("DB Error", "Something went wrong with the database")

    top.destroy()

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    get_serv_addr handles the setting server GUI
'''

def get_serv_addr():
    top = tk.Toplevel()
    top.title("Server Address")
    top.geometry('500x300')
    top.resizable(0, 0)
    top.configure(background=bg_color)

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="Server Address",  font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    serv_addr = tk.Entry(top, width=20, bg="white",
                         borderwidth=2, font=('calibri', 13))
    serv_addr.grid(row=0, column=1, padx=pad_x, pady=pad_y)

    submit_btn = tk.Button(top, text="Submit",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: save_serv_addr(serv_addr, top))
    submit_btn.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    create_account handles creating/updating the username in the database.
'''

def create_account(firstname, lastname, top):
    global sender
    try:
        conn = sqlite3.connect('user.db')
        curs = conn.cursor()
        curs.execute(
            "CREATE TABLE IF NOT EXISTS user (first_name text, last_name text)")
        curs.execute("SELECT * FROM user")
        data = curs.fetchone()

        if data is None:
            print("User does not exist")
            curs.execute("INSERT INTO user VALUES (:first_name, :last_name)",
                         {
                             'first_name': firstname,
                             'last_name': lastname
                         })
            print("Created new user")
            sender = firstname + " " + lastname
            MessageBox("New User", "User Account Created Successfully!")

        else:
            print("user exists")
            curs.execute("UPDATE user SET first_name = :firstt, last_name = :lastt WHERE oid = :id",
                         {
                             'firstt': firstname,
                             'lastt': lastname,
                             'id': 1
                         })

            sender = firstname + " " + lastname
            MessageBox("User", "Username updated successfully!")

        print("user (sender) saved")
        conn.commit()
        conn.close()
    except Exception as e:
        print("(create_account)(exception): ", e)
        MessageBox("DB Error", "Something Went Wrong With the Database")

    top.destroy()

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    create_account_window handles the creting account window
'''

def create_account_window():
    top = tk.Toplevel()
    top.title("Account")
    top.geometry('500x300')
    top.resizable(0, 0)
    top.configure(background=bg_color)

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="First Name",  font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)
    tk.Label(top, text="Last Name", font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=1, column=0, padx=pad_x, pady=pad_y)

    first_name = tk.Entry(top, width=20, bg="white",
                          borderwidth=2, font=('calibri', 13))
    last_name = tk.Entry(top, width=20, bg="white",
                         borderwidth=2, font=('calibri', 13))
    first_name.grid(row=0, column=1, padx=pad_x, pady=pad_y)
    last_name.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    submit_btn = tk.Button(top, text="Create",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: create_account(first_name.get(), last_name.get(), top))
    submit_btn.grid(row=2, column=1, padx=pad_x, pady=pad_y)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
''' 
    CURRENT_ACTIVE_CONNECT - holds the name of the other user in the just closed rt connection
'''
CURRENT_ACTIVE_CONNECT = ""

'''
    stop_rt is called when a user disconnects from a real-time connection.
'''

def stop_rt(_sender, tp):
    global BUSY
    global RT_BUSY
    BUSY = 0
    RT_BUSY = 0

    try:
        _data = {'sender': str(sender), 'receiver': _sender, 'tag': "rt_stop"}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            response = executor.submit(request_post, SEND_URL, _data)
    except Exception as e:
        print("(stop_rt)(exception): ", e)

    for wind in tp_windows:
        wind.destroy()

    MessageBox("Connection Stopped", "Connection stopped")

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
tp_windows = []

'''
    handle_rt_streaming_window handles the real-time connection window.
'''

def handle_rt_streaming_window(_sender):
    global CURRENT_ACTIVE_CONNECT
    global sender
    tp = tk.Toplevel()
    tp.title(sender)
    tp.geometry('400x200')
    tp.resizable(1, 0)
    tp.configure(background=bg_color)

    CURRENT_ACTIVE_CONNECT = _sender
    tp_windows.append(tp)

    pad_x = 60
    pad_y = 20

    connctd = "Connected to " + _sender
    tk.Label(tp, text=connctd,  font=('calibri', 13, 'bold'), background=bg_color,
             fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    submit_btn = tk.Button(tp, text="Disconnect",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: stop_rt(_sender, tp))
    submit_btn.grid(row=2, column=0, padx=pad_x, pady=pad_y)

    tp.protocol("WM_DELETE_WINDOW", on_closing_tp)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
MESSAGE_DELAY = 0
DELAY_TIMER = 0

'''
    reset_busy_by_timer resets the busy status of the user to 0 after a prerecorded message
    sent by another user has been played completely.
'''

def reset_busy_by_timer():
    global BUSY
    global DELAY_TIMER
    global MESSAGE_DELAY

    if BUSY == 1 and (MESSAGE_DELAY != 0):
        print("(reset_busy_by_timer(in)) DELAY_TIMER, MESSAGE_DELAY: ",
              DELAY_TIMER, MESSAGE_DELAY)
        if DELAY_TIMER < MESSAGE_DELAY:
            DELAY_TIMER = DELAY_TIMER + 1
        else:
            BUSY = 0
            DELAY_TIMER = 0
            MESSAGE_DELAY = 0
    else:
        pass

    root.after('1000', reset_busy_by_timer)
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

RT_RECEIVER = ""
RT_BUSY = 0

'''
    - get_data does a lot of the heavy-lifting
    - get data connects to the server every GET_DATA_DELAY (in ms) to check for any data
    - depending on the data tag it gets from the server, get_data either handles or
      delegates to the appropriate function for handling that tag.
'''


@threaded 
def get_data():
    global root
    global BUSY
    global RT_BUSY
    global MESSAGE_DELAY
    global MESSAGE_BUFFER_DELAY
    global RT_RECEIVER
    global GET_DATA_DELAY
    global DELAY_INCREASE
    global MAX_GET_DELAY

    try:
        if sender:
            _data = {'sender': str(sender), 'tag': "get_data"}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = executor.submit(request_post, GET_URL, _data)
                response = response.result()
                #print("(get_data) response:  ", response)

                if response:
                    GET_DATA_DELAY = 200
                    print("(get_data): reset get_data_delay to ", GET_DATA_DELAY) 
                    if BUSY == 0:
                        if (response['tag'] == "send_rtdata"):
                            resp = messagebox.askyesno(
                                "Incoming Real Time Message", "You have a connection request from " + response['sender'] + ". Accept?")
                            if resp == 1:
                                # set busy state
                                BUSY = 1
                                RT_BUSY = 1
                                # notify sender
                                sendee = str(response['sender'])
                                _data = {'sender': str(sender), 'receiver': str(
                                    response['sender']), 'tag': "rt_accept"}
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    response_k = executor.submit(
                                        request_post, SEND_URL, _data)
                                    response_k = response_k.result()
                                    # open connection window
                                    handle_rt_streaming_window(sendee)
                                    # start receiving and sending directly to arduino
                                    RT_RECEIVER = sendee
                            else:
                                # send message decline to sender
                                BUSY = 0
                                RT_BUSY = 0
                                _data = {'sender': str(sender), 'receiver': str(
                                    response['sender']), 'tag': "rt_decline"}
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    response_l = executor.submit(
                                        request_post, SEND_URL, _data)
                                    response_l = response_l.result()

                        elif (response['tag'] == "send_data"):
                            resp = messagebox.askyesno(
                                "Incoming Message", "You have a message from " + response['sender'] + ". Play?")
                            if resp == 1:
                                # set busy to one
                                BUSY = 1

                                # send message to arduino
                                duratnn = response['duration'].split(",")
                                print("(get_data) duration: ", duratnn)
                                total_durtn = 0
                                print(
                                    "(get_data) total duration (out): ", total_durtn)
                                for durr in duratnn:
                                    total_durtn = total_durtn + int(durr)

                                # send message to arduino
                                handle_data(response)

                                # wait until message is completely played
                                MESSAGE_DELAY = int(
                                    total_durtn / 10) + MESSAGE_BUFFER_DELAY
                            else:
                                # send message decline to sender or don't?
                                pass

                        elif (response['tag'] == "busy"):
                            MessageBox(
                                "Busy", "User is busy. Try again after some time")

                        else:
                            # print(response['tag'])
                            pass
                    else:
                        if (response['tag'] == "real_time_data"):
                            handle_rt_data(response['data'])

                        if (response['tag'] == "rt_stop"):
                            BUSY = 0
                            RT_BUSY = 0
                            for wind in tp_windows:
                                wind.destroy()
                            MessageBox("Connection Stopped",
                                    "Connection stopped by other user")

                        if (response['tag'] == "rt_accept"):
                            BUSY = 1
                            RT_BUSY = 1
                            handle_rt_streaming_window(str(response['sender']))
                            RT_RECEIVER = str(response['sender'])

                        if (response['tag'] == "rt_decline"):
                            BUSY = 0
                            RT_BUSY = 0
                            MessageBox("Request declined",
                                    "Connection request declined")

                        else:
                            pass

                else:
                    print("(get_data) no response")
        else:
            print("(get_data) no user account yet")
    
    except requests.Timeout:
        if (GET_DATA_DELAY < MAX_GET_DELAY):
            GET_DATA_DELAY += DELAY_INCREASE
            print("(get_data)(Timeout Exception): increased GET_DATA_DELAY to ", GET_DATA_DELAY, " milliseconds") 
        else:
            print("(get_data)(Timeout Exception): GET_DATA_DELAY at maximum value: ",  GET_DATA_DELAY, " milliseconds") 
    except Exception as e:
        print("(get_data)(exception): ", e)

    root.after(GET_DATA_DELAY, get_data)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
    get_active_delay is called every ACTIVE_USERS_DELAY (in ms) to update active_participants
    get_active_delay also relays the current BUSY state of the user to the server
'''

@threaded
def get_active_users():
    global root
    global active_participants
    global BUSY
    global ACTIVE_USERS_DELAY
    global DELAY_INCREASE
    global MAX_GET_DELAY  

    try:
        if sender:
            active_participants = ['Self']
            _data = {'sender': str(sender), 'busy': BUSY, 'tag': "get_active"}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = executor.submit(
                    request_post, ACTIVE_USER_URL, _data)
                response = response.result()
                if response:
                    ACTIVE_USERS_DELAY = 1000
                    print("(get_active_users): delay reset to ", ACTIVE_USERS_DELAY) 
                    #print("(get_active_users, " + sender + " ): ") 
                    active_participants = active_participants + response['active_users']
                    #print(response['active_users'])
                else:
                    print("(get_active_users) no response")
                
        else:
            print("(get_active_users) no user account yet")
    
    except requests.Timeout:
        if (ACTIVE_USERS_DELAY < MAX_GET_DELAY):
            ACTIVE_USERS_DELAY += DELAY_INCREASE
            print("(get_active_users)(exception): increased ACTIVE_USERS_DELAY  to ", ACTIVE_USERS_DELAY, " milliseconds") 
        else:
            print("(get_active_users)(Timeout Exception): ACTIVE_USERS_DELAY at max value: ", ACTIVE_USERS_DELAY, " milliseconds") 

    except Exception as e:
        print("(get_active_users)(exception): ", e)

    root.after(ACTIVE_USERS_DELAY, get_active_users)

    return




'''
    stop_self_conn is called when self-touch window is closed
'''
SELF_BUSY = 0
def stop_self_conn(tp):
    global BUSY
    global RT_BUSY
    global SELF_BUSY
    BUSY = 0
    RT_BUSY = 0
    SELF_BUSY = 0

    for wind in tp_windows:
        wind.destroy()

    return


'''
    self_touch handles self-touching functionality
'''

def self_touch():
    global BUSY
    global RT_BUSY
    global SELF_BUSY
    tp = tk.Toplevel()
    tp.title("Self Touch Mode")
    tp.geometry('300x200')
    tp.resizable(0, 0)
    tp.configure(background=bg_color)

    tp_windows.append(tp)

    pad_x = 60
    pad_y = 20

    BUSY = 1
    RT_BUSY = 1
    SELF_BUSY = 1

    connctd = "Connected to Yourself"
    tk.Label(tp, text=connctd,  font=('calibri', 13, 'bold'), background=bg_color,
             fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    stop_btn = tk.Button(tp, text="Stop",
                         font=('calibri', 13), width=15,
                         background='#D1D5D7',
                         command=lambda: stop_self_conn(tp))
    stop_btn.grid(row=2, column=0, padx=pad_x, pady=pad_y)

    tp.protocol("WM_DELETE_WINDOW", on_closing_tp)

    return


'''
    used to test prerecorded message functionality (for testing only)
'''


def send_test_message():
    to_arduino("1234s6666", "m")
    return


################################################################################################################################################################
################################################### FUNCTIONS END ##############################################################################################
################################################################################################################################################################


################################################################################################################################################################
################################################### ARDUINO HANDLING ###########################################################################################
################################################################################################################################################################
'''
    handle_rt_data - is called by get_data if there is a real-time data from the server.
                   - it passes the data it get to function to_arduino for further handling
'''

RT_MODE = "r"
MSG_MODE = "m"
def handle_rt_data(_data):
    global RT_MODE
    to_arduino(_data, RT_MODE)
    return


#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#
'''
    handle_data - is called by get_data if there is a prerecorded message from the server
                - it preprocesses the data and passes the data to function to_arduino
'''

def handle_data(data):
    global MSG_MODE

    motors = data.get('motors', 'null')
    duration = data.get('duration', 'null')
    motors = motors.replace(',', '')
    duration = duration.replace(',', '')
    arduino_data = str(motors) + "s" + str(duration)

    to_arduino(arduino_data, MSG_MODE)
    return



#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#
'''
    to_arduino is called by either handle_data or handle_rt_data. 
    it appends the appropriate tag to the data and sends it through the serial port to the arduino.
'''

def to_arduino(arduino_data, mode):
    global ser
    try:
        a_data = ""
        if mode == RT_MODE:
            a_data = a_data + RT_MODE + arduino_data
        elif mode == MSG_MODE:
            a_data = a_data + MSG_MODE + arduino_data
        else:
            a_data = a_data + "u" + arduino_data

        ser.write(str.encode(str(a_data)))
        print("(to arduino) sent data to arduino: ", a_data)
    except Exception as e:
        print("(to_arduino)(exception) error sending data to arduino ", e)
    return


#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#
READ_SEND_FROM_ARDUINO_DELAY = 100
TOUCH_THRESHOLD = 5

'''
    read_send_from_arduino is called every READ_SEND_FROM_ARDUINO_DELAY (in ms).
    it checks the arduino for data  - if the user is in a real-time connection, it sends the data to the other user
                                    - if the user is in self-touch mode, it sends data back to arduino
                                    - else, it does nothing
'''
@threaded
def read_send_from_arduino():
    global BUSY
    global RT_BUSY
    global RT_RECEIVER
    global sender
    global ser
    global t3

    #print()
    data_str = "1"
    try:
        if ser:
            if (ser.inWaiting() > 0):
                data_str = ser.readline(ser.inWaiting()).decode(
                    'ascii').strip('\r\n')
                #print("(read_send_from_arduino) data read from arduino: ", data_str)

                data_int = int(data_str)
                if (data_int > TOUCH_THRESHOLD):

                    if BUSY == 1 and RT_BUSY == 1 and SELF_BUSY == 0:
                        _data = {'sender': str(
                            sender), 'receiver': RT_RECEIVER, 'data': data_str, 'tag': "real_time_data"}

                        try:
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                response = executor.submit(
                                    request_post, SEND_URL, _data)
                                response = response.result()
                                # if response:
                                #     print("(read_send_from_arduino, " + sender + " ): ")
                                # else:
                                #     print("(read_send_from_arduino) no response")
                        except Exception as e:
                            print("(read_send_from_arduino)(exception): ", e)

                    elif BUSY == 1 and RT_BUSY == 1 and SELF_BUSY == 1:
                        handle_rt_data(data_str)

    except Exception as e:
        print("(read_send_from_arduino)(exception): ", e)

    root.after(READ_SEND_FROM_ARDUINO_DELAY, read_send_from_arduino) 
        
    return
################################################################################################################################################################
################################################### ARDUINO HANDLING END #######################################################################################
################################################################################################################################################################

'''
    threading_ starts a seperate thread for the functions which can potentially block the GUI. 
'''

# t1 = threading.Thread(target=get_data)
# t2 = threading.Thread(target=get_active_users)
# t3 = threading.Thread(target=read_send_from_arduino)
# event_1 = Event()
# t1 = Get_Data(event_1)
# t1.start()
# t1.join()
#########################################################################################################
################################################### BUTTON SETUP ########################################
#########################################################################################################
'''
    BUTTONS on the GUI
'''
WIDTH = 40
send_btn            = Button(
                            frame, 
                            text="SEND A RECORDED HAPTIC ACTIVITY",
                            command=send_message, 
                            width=WIDTH)
rt_btn              = Button(
                            frame, 
                            text="REALTIME HAPTIC COMMUNICATION",
                            command=send_rtmessage, 
                            width=WIDTH)
rt_self_btn         = Button(
                            frame, 
                            text="REALTIME SELF TOUCH",
                            command=self_touch, 
                            width=WIDTH)
create_actvty_btn   = Button(
                            frame, 
                            text="RECORD A HAPTIC ACTIVITY", 
                            command=create_activity_gui, 
                            width=WIDTH)
port_btn            = Button(
                            frame, 
                            text="ENTER ARDUINO PORT NO",
                            command=get_port, 
                            width=WIDTH) 
create_accnt_btn    = Button(
                            frame, 
                            text="CREATE NEW USER ACCOUNT", 
                            command=create_account_window, 
                            width=WIDTH) 
server_addr_btn     = Button(
                            frame, 
                            text="ENTER SERVER ADDRESS", 
                            command=get_serv_addr, 
                            width=WIDTH)
status_btn     = Button(
                            frame, 
                            text="CHECK STATUS", 
                            command=check_status, 
                            width=WIDTH)


''' padding for the GUI buttons'''
pad_x = 145
pad_y = 30 # with all buttons, set to 15

send_btn.grid(row=0, column=0, pady=pad_y, padx=pad_x)
#rt_btn.grid(row=1, column=0, pady=pad_y, padx=pad_x)
#rt_self_btn.grid(row=2, column=0, pady=pad_y, padx=pad_x)
create_actvty_btn.grid(row=3, column=0, pady=pad_y, padx=pad_x)
port_btn.grid(row=4, column=0, pady=pad_y, padx=pad_x)
#create_accnt_btn.grid(row=5, column=0, pady=pad_y, padx=pad_x)
#server_addr_btn.grid(row=6, column=0, pady=pad_y, padx=pad_x)
#status_btn.grid(row=7, column=0, pady=pad_y, padx=pad_x)

#########################################################################################################
############################################## MENU BAR #################################################
#########################################################################################################

options_menu = tk.Menu(root_menu, tearoff=False, font=("Arial",10)) 
root_menu.add_cascade(label="Actions", menu=options_menu)
options_menu.add_command(label="Create Activity", command=create_activity_gui) 
options_menu.add_separator()
options_menu.add_command(label="Delete Activity", command=delete_activity_gui) 
options_menu.add_separator()
options_menu.add_command(label="Exit", command=root.quit) 


#########################################################################################################
############################################## MENU BAR END #############################################
#########################################################################################################

#########################################################################################################
############################################## BUTTON SETUP END #########################################
#########################################################################################################
''' function scheduling using the tkinter root '''

root.after(GET_DATA_DELAY, get_data)
root.after(ACTIVE_USERS_DELAY, get_active_users)
root.after(READ_SEND_FROM_ARDUINO_DELAY, read_send_from_arduino) 
root.after('1000', reset_busy_by_timer) 
root.after('30000', set_port)
root.protocol("WM_DELETE_WINDOW", on_closing_root)

root.mainloop() 

##############################################################################################################################################################################################
################################################## ------CODE END------- #####################################################################################################################
##############################################################################################################################################################################################
