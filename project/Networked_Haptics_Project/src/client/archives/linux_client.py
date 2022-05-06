import tkinter as tk
from tkinter.ttk import *
from tkinter import OptionMenu, StringVar, messagebox
import sqlite3
import requests
import time
import concurrent.futures
import serial
import threading
import logging


###############################################################################################################################################################
################################################### INIT GUI ##################################################################################################
###############################################################################################################################################################

bg_color = "#34495E"
root = tk.Tk()
root.title("Touch")
root.geometry('700x600') 
root.resizable(0,0)
root.configure(background=bg_color) 

tk.Label(root, text='New York University Abu Dhabi', bg=bg_color, font=('calibri', 10), fg='white').pack(side='bottom')
frame = tk.Frame(root, bg="white")
frame.place(relwidth=0.9, relheight=0.9, relx=0.05, rely=0.05)

style = Style()
style.theme_use('classic')
style.configure( 'TButton', 
                    font = ('calibri', 15),
                    borderwidth = '0',
                    background=bg_color,
                    foreground="white",
                    width=30
                    )
style.map('TButton', foreground = [('active', bg_color)], background = [('active', '#DDE2ED')]) 

###############################################################################################################################################################
################################################### INIT GUI END ##############################################################################################
###############################################################################################################################################################



###############################################################################################################################################################
################################################### GLOBAL VARIABLES ##########################################################################################
###############################################################################################################################################################
GET_TIMEOUT = 0.2
ACTIVE_USERS_DELAY  = 1000
GET_DATA_DELAY      = 200
DATA_LENGTH         = 5
ERROR = "ERROR"
BUSY = 0
MESSAGE_BUFFER_DELAY = 30

SERVER_ADDRESS = ""
PORT_ADDRESS = ""
SERVER_SET = 0
PORT_SET = 0

#TAGS
TAG_RT_REQUEST  = "send_rtdata"
TAG_GET_DATA    = "get_data"
TAG_GET_ACTIVE  = "get_active"
TAG_SEND_DATA   = "send_data"
TAG_NO_DATA     = "no_data"
TAG_RT_ACCEPT   = "rt_accept"
TAG_RT_DECLINE  = "rt_decline"
TAG_RT_DATA     = "real_time_data"
TAG_RT_STOP     = "rt_stop"

active_participants = [""] 
sender = ""

################################################################################################################################################################
################################################### GLOBAL VARIABLES END #######################################################################################
################################################################################################################################################################





###############################################################################################################################################################
############################################# INIT USERNAME, PORT, SERVER_ADDRESS #############################################################################
###############################################################################################################################################################

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

tk.Label(root, text=sender, bg=bg_color, font=('calibri', 10, 'bold'), fg='white').pack(side='top') 

#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#

def init_serv_addr():
    global SERVER_ADDRESS

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
            print("(init_serv_addr) server address fetched: ", SERVER_ADDRESS) 
    except Exception as e:
        print("(init_serv_addr)(exception) server address fetch: ", e) 
    return

#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#
def set_server():
    global SERVER_ADDRESS
    global SEND_URL
    global GET_URL
    global ACTIVE_USER_URL

    if SERVER_ADDRESS == "":
        SEND_URL        = "http://15.185.167.245/send"
        GET_URL         = "http://15.185.167.245/check"
        ACTIVE_USER_URL = "http://15.185.167.245/active"
    else:
        SEND_URL        = "http://" + SERVER_ADDRESS + "/send"
        GET_URL         = "http://" + SERVER_ADDRESS + "/check"
        ACTIVE_USER_URL = "http://" + SERVER_ADDRESS + "/active" 
    return

#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#

init_serv_addr()
set_server() 

#-------------------------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------#

def init_port():
    global PORT_ADDRESS
    global PORT_SET

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
try:
    ser = serial.Serial(PORT_ADDRESS, 115200)
except:
    ser = None

def set_port():
    global ser
    try:
        ser = serial.Serial(PORT_ADDRESS, 115200) 
    except Exception as e:
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

def request_post(_url, _data):
    return requests.post(url=_url , data=_data, timeout=GET_TIMEOUT).json() 

def on_closing_top():
    global BUSY
    global RT_BUSY
    BUSY = 0
    RT_BUSY = 0
    for wind in top_windows:
        wind.destroy()
    return

def on_closing_tp():
    global BUSY
    global RT_BUSY
    BUSY = 0
    RT_BUSY = 0
    
    try:
        _data = {'sender' : str(sender), 'receiver' : CURRENT_ACTIVE_CONNECT, 'tag' : "rt_stop"} 
        with concurrent.futures.ThreadPoolExecutor() as executor:
            response = [executor.submit(request_post, SEND_URL, _data)]
    except Exception as e:
        print("(stop_rt)(exception): ", e)

    for wind in tp_windows:
        wind.destroy()
    return

def on_closing_root():
    global BUSY
    global RT_BUSY
    BUSY = 0
    RT_BUSY = 0
    root.destroy()
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
def ShowInfo(label, message):
    messagebox.showinfo(label, message)
    return

def MessageBox(label, message):
    thrd = threading.Thread(target=ShowInfo, args=[label, message]) 
    thrd.start()
    return
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def send_rtdata(recvr, top):
    global BUSY
    global RT_BUSY
    global RT_RECEIVER
    print("(send_rtdata) receiver selected", recvr)

    try:
        if sender:
            _data = {'sender': str(sender), 'receiver' : str(recvr), 'tag' : "send_rtdata"} 
            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = [executor.submit(request_post, SEND_URL, _data)]
                concurrent.futures.wait(response)
                response = response[0].result()
                print("response ", response)
                if response:
                    print("(send_rtdata, " + sender + " ): ")

                    if (response['tag'] == "busy"):
                        MessageBox("Busy", "User is busy. Try again after some time")
                    elif response['tag'] == "not_a_user":
                        MessageBox("Not a User", "Receiver does not exist") 
                    elif response['tag'] == "no_data":
                        pass
                    else:
                        MessageBox("Connect", "Connection request sent. Wait for response") 
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
def send_rtmessage():
    top = tk.Toplevel()
    top.title("Real Time") 
    top.geometry('400x250') 
    top.resizable(0,0)
    top.configure(background=bg_color) 

    top_windows.append(top)

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="Receiver", font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    partcpnt = StringVar()
    drop = OptionMenu(top, partcpnt, *active_participants)
    drop.grid(row=0, column=1, padx=pad_x, pady=pad_y)
    drop.configure(background=bg_color, fg='white', font = ('calibri', 13, 'bold'))

    submit_btn = tk.Button( top, text="Connect",
                            font = ('calibri', 13), width=15, 
                            background='#D1D5D7', 
                            command=lambda: send_rtdata(partcpnt.get(), top))
    submit_btn.grid(row=2, column=1, padx=pad_x, pady=pad_y) 

    top.protocol("WM_DELETE_WINDOW", on_closing_top)
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def send_data(actvty, recvr, top):
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
            receiver = recvr
            activity = actvty

            print("(send_data) Duration arrar: ", duration) 
            _data = {
                    'sender'    : str(sender), 
                    'receiver'  : str(receiver),
                    'activity'  : str(activity),
                    'motors'    : str(motors),
                    'duration'  : str(duration),
                    'tag'       : "send_data"
                    } 

            
            print("(send_data) request to server initiated")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = [executor.submit(request_post, SEND_URL, _data)]
                concurrent.futures.wait(response)
                response = response[0].result()
            
            if (response['tag'] == "busy"):
                        MessageBox("Busy", "User is busy. Try again after some time")
            elif response['tag'] == "not_a_user":
                MessageBox("Not a User", "Receiver does not exist") 
            elif response['tag'] == "no_data":
                pass
            else:
                MessageBox("Success", "Message sent successfully")
                
            top.destroy()

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


def send_message():
    top = tk.Toplevel()
    top.title("Send Message")
    top.geometry('500x300') 
    top.resizable(0,0)
    top.configure(background=bg_color) 

    pad_x = 20
    pad_y = 20
    try:
        conn = sqlite3.connect('user.db') 
        curs = conn.cursor()

        curs.execute("CREATE TABLE IF NOT EXISTS activity (activity_name text PRIMARY KEY, motors text, duration text)") 
        curs.execute("SELECT *,oid FROM activity")
        data = curs.fetchall()

        tk.Label(top, text="Activity",  font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)
        tk.Label(top, text="Receiver", font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=1, column=0, padx=pad_x, pady=pad_y)
        
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
            drop1.configure(background=bg_color, fg='white',font = ('calibri', 13, 'bold'))


            partcpnt = StringVar()
            drop2 = OptionMenu(top, partcpnt, *active_participants)
            drop2.grid(row=1, column=1, padx=pad_x, pady=pad_y)
            drop2.configure(background=bg_color, fg='white', font = ('calibri', 13, 'bold'))


        conn.commit()
        conn.close() 
    except Exception as e:
        MessageBox("DB Error", "Something Went Wrong With the Database")
        print("(send_message)(exception): ", e)
        return

    submit_btn = tk.Button( top, text="Send",
                            font = ('calibri', 13), width=15, 
                            background='#D1D5D7', 
                            command=lambda: send_data(actvty.get(), partcpnt.get(), top))
    submit_btn.grid(row=2, column=1, padx=pad_x, pady=pad_y)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


n_motors = []
n_duration = []
buttons = []

def activity_to_db(actv_name, sequence_length, activity_name, top):
    global n_motors
    global n_duration
    global buttons

    try:
        conn = sqlite3.connect('user.db') 
        curs = conn.cursor()
        curs.execute("CREATE TABLE IF NOT EXISTS activity (activity_name text PRIMARY KEY, motors text, duration text)") 
        motor_arr = []
        dur_arr = []

        print("name: ", actv_name)

        print("motor: ", n_motors)
        print("duration: ", n_duration) 

        for motor in n_motors:
            try:
                test = int(motor.get()) #to throw error if not int
                data = motor.get()
                if not data:
                    MessageBox("Incomplete Entry", "Enter a value in every field")
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
                    MessageBox("Incomplete Entry", "Enter a value in every field")
                    return
                dur_arr.append(data)
            except Exception as e: 
                print("(activity_to_db)(exception): ", e) 
                MessageBox("Error", "Duration must be an integer")
                return

        print("motors: ", motor_arr)
        print("durations", dur_arr)

        str_motors = ",".join(motor_arr)
        str_duration = ",".join(dur_arr)
        

        print(str_motors)
        print(str_duration)

        curs.execute("INSERT INTO activity VALUES (:activity_name, :motors, :duration)",
        {
            'activity_name': str(actv_name),
            'motors' : str(str_motors),
            'duration' : str(str_duration)
        })


        conn.commit()
        conn.close()

        MessageBox("Success", "Successfully added new activity!")
        top.destroy() 
    except Exception as e:
        print("(activity_to_db)(exception): ", e) 
        MessageBox("Error", "Something went wrong. Try again or Ask for assistance. Also make sure that you have not added this activity before.")
        sequence_length.config(state='normal')
        activity_name.config(state='normal') 
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def get_activity_detail(actv_name, top, sequence_length, activity_name):
    global n_motors
    global n_duration
    global buttons

    try:
        s_length = int(sequence_length.get())
    except Exception as e:
        print("(get_activity_detail)(exception): ", e)
        MessageBox("Error", "Sequence length must be an integer")
        return
    
    try:
        pad_x = 5
        pad_y = 5
        
        for obj in n_motors:
            obj.destroy()
        for obj in n_duration:
            obj.destroy()
        for btn in buttons:
            btn.destroy()

        n_motors.clear()
        n_duration.clear()
        buttons.clear() 


        sequence_length.config(state='disabled')
        activity_name.config(state='disabled')
        tk.Label(top, text="Motor Number",  font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=3, column=1, padx=pad_x, pady=pad_y)
        tk.Label(top, text="Duration", font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=3, column=2, padx=pad_x, pady=pad_y)

        cnt = 1
        row_cnt = 4


        for a in range(s_length):
            tk.Label(top, text=cnt, font = ('calibri', 13), background=bg_color, fg='white').grid(row=row_cnt, column=0, padx=2, pady=pad_y)
            motor_no = tk.Entry(top, width=10, bg="white", borderwidth=2, font = ('calibri', 13))
            motor_no.grid(row=row_cnt, column=1, padx=pad_x, pady=pad_y)
            duration = tk.Entry(top, width=10, bg="white", borderwidth=2, font = ('calibri', 13))
            duration.grid(row=row_cnt, column=2, padx=pad_x, pady=pad_y)

            n_motors.append(motor_no)
            n_duration.append(duration)

            cnt = cnt + 1
            row_cnt = row_cnt + 1
        
        add_btn = tk.Button( top, text="Add Activity",
                        font = ('calibri', 13), width=15, 
                        background='#D1D5D7', 
                        command=lambda: activity_to_db(actv_name,sequence_length, activity_name, top)) 
        add_btn.grid(row=row_cnt, column=2, padx=pad_x, pady=pad_y) 

        buttons.append(add_btn) 
    except Exception as e:
        print("(get_activity_detail)(exception): ", e)
        MessageBox("Error", "Something went wrong. Try again or Ask for assistance")
    
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def create_activity():
    top = tk.Toplevel()
    top.title("Create Activity")
    top.geometry('700x600') 
    top.resizable(0,1)
    top.configure(background=bg_color) 

    pad_x = 15
    pad_y = 15


    tk.Label(top, text="Activity Name",  font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)
    activity_name = tk.Entry(top, width=20, bg="white", borderwidth=2, font = ('calibri', 13))
    activity_name.grid(row=0, column=1, padx=pad_x, pady=pad_y)

    tk.Label(top, text="Sequence Length",  font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=1, column=0, padx=pad_x, pady=pad_y)
    sequence_length = tk.Entry(top, width=20, bg="white", borderwidth=2, font = ('calibri', 13))
    sequence_length.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    
    create_btn = tk.Button( top, text="Create",
                        font = ('calibri', 13), width=15, 
                        background='#D1D5D7', 
                        command=lambda: get_activity_detail(activity_name.get(),top, sequence_length, activity_name)) 
    create_btn.grid(row=2, column=1, padx=pad_x, pady=pad_y)
    
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


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
            print("port dne")
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


def get_port():
    top = tk.Toplevel()
    top.title("Account")
    top.geometry('500x300') 
    top.resizable(0,0)
    top.configure(background=bg_color) 

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="Port Number",  font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    port_no = tk.Entry(top, width=20, bg="white", borderwidth=2, font = ('calibri', 13))
    port_no.grid(row=0, column=1, padx=pad_x, pady=pad_y)


    submit_btn = tk.Button( top, text="Submit",
                            font = ('calibri', 13), width=15, 
                            background='#D1D5D7', 
                            command=lambda: save_port(port_no, top)) 
    submit_btn.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def save_serv_addr(serv_addr, top):
    global SEND_URL
    global GET_URL
    global ACTIVE_USER_URL
    global SERVER_ADDRESS

    try:
        conn = sqlite3.connect('user.db') 
        curs = conn.cursor()
        curs.execute("CREATE TABLE IF NOT EXISTS server_address (serv_addr text)") 
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
            MessageBox("Server Address", "Server address successfully updated!") 
        
        SERVER_ADDRESS  = server_addr
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


def get_serv_addr():
    top = tk.Toplevel()
    top.title("Server Address")
    top.geometry('500x300') 
    top.resizable(0,0)
    top.configure(background=bg_color) 

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="Server Address",  font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    serv_addr = tk.Entry(top, width=20, bg="white", borderwidth=2, font = ('calibri', 13))
    serv_addr.grid(row=0, column=1, padx=pad_x, pady=pad_y)


    submit_btn = tk.Button( top, text="Submit",
                            font = ('calibri', 13), width=15, 
                            background='#D1D5D7', 
                            command=lambda: save_serv_addr(serv_addr, top)) 
    submit_btn.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def create_account(firstname, lastname, top):
    global sender
    try:
        conn = sqlite3.connect('user.db') 
        curs = conn.cursor()
        curs.execute("CREATE TABLE IF NOT EXISTS user (first_name text, last_name text)")
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
                'lastt' : lastname,
                'id' : 1
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


def create_account_window():
    top = tk.Toplevel()
    top.title("Account")
    top.geometry('500x300') 
    top.resizable(0,0)
    top.configure(background=bg_color) 

    pad_x = 20
    pad_y = 20  

    tk.Label(top, text="First Name",  font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)
    tk.Label(top, text="Last Name", font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=1, column=0, padx=pad_x, pady=pad_y)

    first_name  = tk.Entry(top, width=20, bg="white", borderwidth=2, font = ('calibri', 13))
    last_name   = tk.Entry(top, width=20, bg="white", borderwidth=2, font = ('calibri', 13))
    first_name.grid(row=0, column=1, padx=pad_x, pady=pad_y)
    last_name.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    submit_btn = tk.Button( top, text="Create",
                            font = ('calibri', 13), width=15, 
                            background='#D1D5D7', 
                            command=lambda: create_account(first_name.get(), last_name.get(), top))
    submit_btn.grid(row=2, column=1, padx=pad_x, pady=pad_y)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


CURRENT_ACTIVE_CONNECT = "";
def stop_rt(_sender, tp):
    global BUSY
    global RT_BUSY
    BUSY = 0
    RT_BUSY = 0

    try:
        _data = {'sender' : str(sender), 'receiver' : _sender, 'tag' : "rt_stop"} 
        with concurrent.futures.ThreadPoolExecutor() as executor:
            response = [executor.submit(request_post, SEND_URL, _data)]
    except Exception as e:
        print("(stop_rt)(exception): ", e)

    for wind in tp_windows:
        wind.destroy()

    MessageBox("Connection Stopped", "Connection stopped")

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


tp_windows = [] 
def handle_rt_streaming_window(_sender):
    global CURRENT_ACTIVE_CONNECT
    global sender
    tp = tk.Toplevel()
    tp.title(sender)
    tp.geometry('400x200') 
    tp.resizable(1,0)
    tp.configure(background=bg_color) 

    CURRENT_ACTIVE_CONNECT = _sender;
    tp_windows.append(tp)

    pad_x = 20
    pad_y = 20  

    connctd = "Connected to " + _sender
    tk.Label(tp, text=connctd,  font = ('calibri', 13, 'bold'), background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    submit_btn = tk.Button( tp, text="Disconnect",
                            font = ('calibri', 13), width=15, 
                            background='#D1D5D7', 
                            command=lambda : stop_rt(_sender, tp)) 
    submit_btn.grid(row=2, column=0, padx=pad_x, pady=pad_y)

    tp.protocol("WM_DELETE_WINDOW", on_closing_tp)

    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


MESSAGE_DELAY = 0
DELAY_TIMER = 0
def reset_busy_by_timer():
    global BUSY
    global DELAY_TIMER
    global MESSAGE_DELAY

    if BUSY == 1 and (MESSAGE_DELAY != 0):
        print("(reset_busy_by_timer(in)) DELAY_TIMER, MESSAGE_DELAY: ", DELAY_TIMER, MESSAGE_DELAY) 
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

def get_data():
    global root
    global BUSY
    global RT_BUSY
    global MESSAGE_DELAY
    global MESSAGE_BUFFER_DELAY
    global RT_RECEIVER
    
    print()
    print("(get_data) Busy status: ", BUSY) 
    try:
        if sender:
            _data = {'sender': str(sender), 'tag' : "get_data"} 
            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = [executor.submit(request_post, GET_URL, _data)]
                concurrent.futures.wait(response)
                response = response[0].result() 
                print("(get_data) response:  ", response)

                if response:
                    if BUSY == 0:
                        if (response['tag'] == "send_rtdata"): 
                            resp = messagebox.askyesno("Incoming Real Time Message", "You have a connection request from " + response['sender'] + ". Accept?")
                            if resp == 1:
                                #set busy state
                                BUSY = 1
                                RT_BUSY = 1
                                #notify sender
                                sendee = str(response['sender'])
                                _data = {'sender' : str(sender), 'receiver': str(response['sender']), 'tag' : "rt_accept"}
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    response_k = [executor.submit(request_post, SEND_URL, _data)]
                                    concurrent.futures.wait(response_k)
                                    response_k = response_k[0].result()
                                    #open connection window
                                    handle_rt_streaming_window(sendee) 
                                    #start receiving and sending directly to arduino
                                    RT_RECEIVER = sendee
                            else:
                                #send message decline to sender
                                BUSY = 0
                                RT_BUSY = 0
                                _data = {'sender' : str(sender), 'receiver': str(response['sender']), 'tag' : "rt_decline"} 
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    response_l = [executor.submit(request_post, SEND_URL, _data)]
                                    concurrent.futures.wait(response_l)
                                    response_l = response_l[0].result()
                                
                        elif (response['tag'] == "send_data"):
                            resp = messagebox.askyesno("Incoming Message", "You have a message from " + response['sender'] + ". Play?")
                            if resp == 1:
                                #set busy to one
                                BUSY = 1

                                #send message to arduino
                                duratnn = response['duration'].split(",") 
                                print("(get_data) duration: ", duratnn)
                                total_durtn = MESSAGE_BUFFER_DELAY
                                print("(get_data) total duration (out): ", total_durtn)
                                for durr in duratnn:
                                    total_durtn = total_durtn + int(durr) 
                                
                                
                                #send message to arduino
                                handle_data(response) 

                                #wait until message is completely played
                                MESSAGE_DELAY = total_durtn
                            else:
                                #send message decline to sender or don't?
                                pass

                        elif (response['tag'] == "busy"):
                            MessageBox("Busy", "User is busy. Try again after some time")

                        else:
                            #print(response['tag']) 
                            pass
                    else:
                        if (response['tag'] == "real_time_data"):
                            handle_rt_data(response['data']) 

                        if (response['tag'] == "rt_stop"):
                            BUSY = 0
                            RT_BUSY = 0
                            for wind in tp_windows:
                                wind.destroy() 
                            MessageBox("Connection Stopped", "Connection stopped by other user")

                        if (response['tag'] == "rt_accept"):
                            BUSY = 1
                            RT_BUSY = 1
                            handle_rt_streaming_window(str(response['sender']))
                            RT_RECEIVER = str(response['sender'])

                        if (response['tag'] == "rt_decline"):
                            BUSY = 0
                            RT_BUSY = 0
                            MessageBox("Request declined", "Connection request declined")
                        
                        else:
                            pass
                        
                else:
                    print("(get_data) no response") 
        else:
            print("(get_data) no user account yet") 
    except Exception as e:
        print("(get_data)(exception): ", e) 

    root.after(GET_DATA_DELAY, get_data)
    return


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def get_active_users():
    global root
    global active_participants
    global BUSY

    print()
    try:
        if sender:
            _data = {'sender': str(sender), 'busy': BUSY, 'tag' : "get_active"} 
            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = [executor.submit(request_post, ACTIVE_USER_URL, _data)]
                concurrent.futures.wait(response)
                response = response[0].result()
                if response:
                    #print("(get_active_users, " + sender + " ): ")
                    active_participants = response['active_users'] 
                    print(response['active_users']) 
                else:
                    print("(get_active_users) no response")
        else:
            print("(get_active_users) no user account yet")
    except Exception as e:
        print("(get_active_users)(exception): ", e) 

    root.after(ACTIVE_USERS_DELAY, get_active_users)
    return


################################################################################################################################################################
################################################### FUNCTIONS END ##############################################################################################
################################################################################################################################################################


################################################################################################################################################################
################################################### ARDUINO HANDLING ###########################################################################################
################################################################################################################################################################
RT_MODE = "r"
MSG_MODE = "m"

def handle_rt_data(_data):
    global RT_MODE
    to_arduino(_data, RT_MODE)
    return

#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#
def handle_data(data):
    global MSG_MODE

    sender      = data.get('sender', 'null')
    receiver    = data.get('receiver', 'null')
    activity    = data.get('activity', 'null')
    motors      = data.get('motors', 'null')
    duration    = data.get('duration', 'null') 

    user_data = [sender, receiver, activity]
    arduino_data = str(motors) + "|" + str(duration)

    to_arduino(arduino_data, MSG_MODE) 
    return

#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#

def to_arduino(arduino_data, mode):
    global ser
    try:
        a_data = ""
        if mode == RT_MODE:
            a_data = a_data + "r" + arduino_data
        elif mode == MSG_MODE:
            a_data = a_data + "m" + arduino_data
        else:
            a_data = a_data + "u" + arduino_data
            
        ser.write(str.encode(str(a_data))) 
        #print("(to_arduino) data sent to arduino")
    except Exception as e:
        print("(to_arduino)(exception) error sending data to arduino ", e) 
    return

#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#

def read_send_from_arduino():
    global BUSY
    global RT_BUSY
    global RT_RECEIVER
    global sender
    global ser

    print()
    data_str = "10"
    try:
        if ser:
            if (ser.inWaiting() > 0 ):
                data_str = ser.readline(ser.inWaiting()).decode('ascii')
                print("(read_send_from_arduino) data read from arduino: ", data_str) 

                if BUSY == 1 and RT_BUSY == 1:
                    #print("(read_send_from_arduino) real time data from arduino being sent to " + RT_RECEIVER) 
                    _data = {'sender': str(sender), 'receiver': RT_RECEIVER , 'data' : data_str, 'tag' : "real_time_data"} 
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            response = [executor.submit(request_post, SEND_URL, _data)]
                            concurrent.futures.wait(response)
                            response = response[0].result()
                            if response:
                                print("(read_send_from_arduino, " + sender + " ): ")
                                #print(response['tag']) 
                            else:
                                print("(read_send_from_arduino) no response") 
                    except Exception as e:
                        print("(read_send_from_arduino)(exception): ", e) 
    except Exception as e:
        print("(read_send_from_arduino)(exception): ", e) 
    
    root.after('1000', read_send_from_arduino) 

    return

################################################################################################################################################################
################################################### ARDUINO HANDLING END #######################################################################################
################################################################################################################################################################



#########################################################################################################
################################################### BUTTON SETUP ########################################
#########################################################################################################

send_btn              = Button(frame, text="SEND A MESSAGE", command=send_message)
rt_btn                = Button(frame, text="SEND REAL-TIME TOUCH MESSAGE", command=send_rtmessage) 
create_actvty_btn     = Button(frame, text="CREATE AN ACTIVITY", command=create_activity)
port_btn              = Button(frame, text="ENTER PORT NO", command=get_port)
create_accnt_btn      = Button(frame, text="CREATE NEW USER ACCOUNT", command=create_account_window)
send_to_ard           = Button(frame, text="ENTER SERVER ADDRESS", command=get_serv_addr) 

pad_x = 100
pad_y = 20

send_btn.grid(row = 0, column = 0, pady=pad_y, padx=pad_x)
rt_btn.grid(row = 1, column = 0, pady=pad_y, padx=pad_x)
create_actvty_btn.grid(row = 2, column = 0, pady=pad_y, padx=pad_x)
port_btn.grid(row = 3, column = 0, pady=pad_y, padx=pad_x)
create_accnt_btn.grid(row = 4, column = 0, pady=pad_y, padx=pad_x)
send_to_ard.grid(row = 5, column = 0, pady=pad_y, padx=pad_x) 

#########################################################################################################
############################################## BUTTON SETUP END #########################################
#########################################################################################################

root.after(GET_DATA_DELAY, get_data)
root.after(ACTIVE_USERS_DELAY, get_active_users)
root.after('1000', read_send_from_arduino) 
root.after('1000', reset_busy_by_timer) 

root.protocol("WM_DELETE_WINDOW", on_closing_root)
root.mainloop() 

################################################################################################################################################################
################################################## ------CODE END------- #######################################################################################
################################################################################################################################################################


