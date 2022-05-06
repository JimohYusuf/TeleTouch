import requests
import schedule
import time
import random
import serial
import json

import tkinter as tk 
   
serial_port = ""
root = tk.Tk() 
  
root.geometry("200x200") 
   
name_var = tk.StringVar() 
  
def submit(): 
    global message_var
    global serial_port
    global root

    serial_port = name_entry.get() 
    print("The serial port is : " + serial_port) 
    name_var.set("") 
      
name_label = tk.Label(root, text = 'Serial Port', 
                      font=('calibre', 
                            10, 'bold')) 
name_entry = tk.Entry(root, 
                      textvariable = name_var,font=('calibre',10,'normal')) 
   
sub_btn=tk.Button(root,text = 'Submit', 
                  command = submit) 
   
name_label.grid(row=0,column=0) 
name_entry.grid(row=0,column=1) 
sub_btn.grid(row=2,column=1) 
   
root.mainloop() 

delay_second = 5

server_url = "http://192.168.1.17/client_test_1"

def initiator():

    client_id = 2
    value = random.randint(0,1)

    print("hello")

    try:

        server_data = {'touch': str(value), 'id': str(client_id)} 

        print("Data sent: ")
        print(server_data["touch"])
        response = requests.get(url = server_url, params = server_data) 
    
        data = response.json() 

        print("Data received: ")
        print(data)

    except:
        print("error")


schedule.every(delay_second).seconds.do(initiator)

while 1:
    schedule.run_pending()

    time.sleep(1)
