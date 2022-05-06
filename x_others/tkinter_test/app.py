import tkinter as tk
from tkinter import IntVar, Label, OptionMenu, Radiobutton, StringVar, filedialog, Text, messagebox
import os
import sqlite3


root = tk.Tk()
root.title("Test app")
#root.iconbitmap('')


canvas = tk.Canvas(root, height=700, width= 700, bg="#263D42")
canvas.pack()

frame = tk.Frame(root, bg="white")
frame.place(relwidth=0.8, relheight=0.8, relx=0.1, rely=0.1)



conn = sqlite3.connect('activity_list.db')
c = conn.cursor()


# c.execute(""" CREATE TABLE activity2 (
#         activity_name text,
#         motor_array text,
#         duration_arr text
#         )""")


def submit():
    conn = sqlite3.connect('activity_list.db')
    c = conn.cursor()

    c.execute("INSERT INTO activity2 VALUES (:activity_name, :motor_array, :duration_arr)",
        {
            'activity_name': activity_name.get(),
            'motor_array': motor_array.get(),
            'duration_arr': duration_arr.get()
        })
    conn.commit()
    conn.close() 

    activity_name.delete(0,tk.END)
    duration_arr.delete(0,tk.END)
    motor_array.delete(0,tk.END)

def query():
    conn = sqlite3.connect('activity_list.db')
    c = conn.cursor()

    c.execute("SELECT *,oid FROM activity2")
    activities = c.fetchall()
    print(activities) 

    # c.fetchone()
    # c.fetchmany(20)

    conn.commit()
    conn.close() 

activity_name = tk.Entry(frame, width=50)
activity_name.grid(row=0, column=1, padx=20)
motor_array = tk.Entry(frame, width=50)
motor_array.grid(row=1, column=1, padx=20)
duration_arr = tk.Entry(frame, width=50)
duration_arr.grid(row=2, column=1, padx=20)

activity_label = tk.Label(frame, text="Activity Name")
activity_label.grid(row=0, column=0)
motor_label = tk.Label(frame, text="Motor Array")
motor_label.grid(row=1, column=0)
duration_label = tk.Label(frame, text="Duration Array")
duration_label.grid(row=2, column=0) 


tk.Button(frame, text="Submit", command=submit).grid(row=4, column=1, columnspan=30)
tk.Button(frame, text="Query", command=query).grid(row=5, column=1, columnspan=30)

conn.commit()
conn.close() 



# activity_list  = [
#     "Activity 1",
#     "Activity 2",
#     "Activity 3"
# ]

# clicked = StringVar()
# clicked.set(activity_list[0])
# drop = OptionMenu(frame, clicked, *activity_list)
# drop.pack() 



# var = IntVar()
# chk_b = tk.Checkbutton(frame, text="Don't check!", variable=var) 
# chk_b.pack() 

# def chk_btn():
#     tk.Label(frame, text=var.get()).pack()

# tk.Button(frame, text="Show check val", command=chk_btn).pack()



#top = tk.Toplevel()


# def popup():
#     #messagebox.showinfo("This is a popup", "Hi there!")
#     response = messagebox.askokcancel("This is a popup", "Hi there. You good?")
#     tk.Label(frame, text=response).pack() 

# tk.Button(frame, text="Popup", command=popup).pack()



# textbox = tk.Entry(frame, width=50, bg="white", borderwidth=3)
# textbox.pack()

# def adduser():
#     user = textbox.get()
#     mylabel = tk.Label(frame, text=user)
#     mylabel.pack() 

# def add_activity(activity_dictionary):
#     print(activity_dictionary)
#     return activity_dictionary



# a = IntVar()
# def clicked(value):
#     label2 = tk.Label(frame, text=value)
#     label2.pack()

# radio_button = tk.Radiobutton(frame, text="option 1", variable=a, value=1, command=lambda: clicked(a.get())).pack()
# radio_button = tk.Radiobutton(frame, text="option 2", variable=a, value=2, command=lambda: clicked(a.get())).pack()



# MODES = [
#     ("option 1","apple"),
#     ("option 2","orange"),
#     ("option 3","banana"),
#     ("option 4","guava")
# ]
# option = StringVar()
# option.initialize(None)

# for text,mode in MODES:
#     Radiobutton(frame, text=text, variable=option, value=mode).pack()
# tk.Button(frame, text="Select option", command=lambda: clicked(option.get())).pack()



# activities = tk.Button(root, text="Add Activity", padx=10,
#                     pady=5, fg="white", bg="green", command=lambda: add_activity(10)).pack()

# openfile = tk.Button(root, text="OpenFile", padx=10,
#                     pady=5, fg="white", bg="green", command=adduser).pack()

# endprogram = tk.Button(root, text="Endprogram", padx=10,
#                     pady=5, fg="white", bg="green", command=root.quit).pack()

root.mainloop()