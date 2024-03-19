#!/usr/bin/python3

#Tkinter Python Module for GUI
from tkinter import Tk, Frame, Label, Button, Entry, Text, Scrollbar, messagebox, StringVar
import asyncio

import socket #Sockets for network connection
import threading # for multiple proccess 
import binascii
import datetime, time
import re

from modbus_async_client import ModbusAsyncClient
from video_player import VideoPlayer

class GUI:
    client_socket = None
    last_received_message = None
    connected = False

    # Constructor
    def __init__(self, master):
        self.root = master
        self.ip_entry = None
        self.port_entry = None
        self.connect_button = None
        self.pressure_sensor_label = None
        self.pressure_sensor_val_label = None
        self.pressure_sensor_val = None
        self.modbus_command_entry = None
        self.modbus_log_text = None
        self.initialize_gui()

    # GUI initializer
    def initialize_gui(self):
        self.root.title("Deepwater camera") 
        # Make window expandable        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        # Left frame in the window
        self.frame_left = Frame()
        self.frame_left.pack(side='left', anchor='w', expand='true', fill='both')
        # Right frame in the window
        self.frame_right = Frame(width = 350)
        self.frame_right.pack(side='right', anchor='e', fill='both')
        self.frame_right.pack_propagate('false')
        # Bottom frame in the left frame
        self.frame_left_bottom = Frame(self.frame_left, bg='yellow') 
        self.frame_left_bottom.pack(side='bottom', anchor='sw', fill='x') # Left Bottom frame.pack()  
        # Display part of layout
        self.display_video_player()
        self.display_connect_section()
        # Add sensors frame in the right frame
        self.frame_sensors = Frame(self.frame_right)
        self.frame_sensors.pack(side='top', anchor='nw', fill='x') # Sensors frame.pack()
        # Display rest layout
        self.display_pressure_sensor()
        self.display_compass_sensors()
        self.display_light_buttons()
        self.display_modbus_command_entry_box()
        self.display_modbus_log_text_box()

    def display_video_player(self):
    
        self.video_frame = Frame(self.frame_left, width=500, height=400, bg='black')
        self.video_frame.pack(side='top', anchor='nw', expand='true', fill='both',) # Video frame frame.pack()

        # Init VideoPlayer (with frame_id)
        videoPlayer = None #VideoPlayer(self.video_frame.winfo_id())
        #videoPlayer.run()
      
        self.video_start_button = Button(self.frame_left_bottom, text="Start video", font=("arial", 10, "bold"), 
            command = lambda: self.on_video_start_button(videoPlayer)
        )
        self.video_start_button.pack(side='left', anchor='sw', padx=5, pady=5)       


    def on_video_start_button(self, videoPlayer):
        if self.video_start_button.config('text')[-1] == 'start':
            self.video_start_button.config(text="stop")
            videoPlayer.start_record()
        else:
            self.stop_record()
            self.video_start_button.config(text="start")

    # Put IP adress Entry, Port Entry boxes and Connect Button on the form
    def display_connect_section(self):
        self.frame_connect = Frame(self.frame_right)
        self.frame_connect.pack(side='top', anchor='nw', ipadx=5, ipady=5) # Connect Section frame.pack()
        # IP adress Label and Entry
        label = Label(self.frame_connect, text='IP ', font=("arial", 10, "bold"))
        label.pack(side='left', ipadx=5, ipady=5)
        self.ip_entry_text = StringVar()
        self.ip_entry = Entry(self.frame_connect, textvariable=self.ip_entry_text, width=15,font=("arial", 10, "bold"))
        self.ip_entry.pack(side='left', pady=5)
        
        # Port Label and Entry
        label = Label(self.frame_connect, text='Port ', font=("arial", 10, "bold"))
        label.pack(side='left', ipadx=5, ipady=5)
        self.port_entry_text = StringVar()
        self.port_entry = Entry(self.frame_connect, textvariable=self.port_entry_text, width=5,font=("arial", 10, "bold"))
        self.port_entry.pack(side='left', pady=5)                      
        #self.ip_entry_text.set("192.168.1.67")
        #self.port_entry_text.set("4001")
        self.ip_entry_text.set("127.0.0.1")
        self.port_entry_text.set(10319)
        
        # Connect Button
        self.connect_button = Button(
            self.frame_connect, text="Connect", font=("arial", 10, "bold"), command=self.on_connect)
        self.connect_button.pack(side='right', padx=5, pady=5)
        
    # Handle "Connect" button click
    def on_connect(self):
        if self.connect_button.config('relief')[-1] == 'raised':
            self.connect_button.config(text="Disconnect")
            self.connect_button.config(relief="sunken")            
            self.connected = True            
            self.ip_entry.config(state='disabled')
            self.port_entry.config(state='disabled')
            self.modbus_command_entry.config(state='normal')
            # Start Modbus Async Client
            self.modbus_async_client = ModbusAsyncClient(
                self.receive_message_from_server, comm='tcp', host=self.ip_entry_text.get(), port=self.port_entry_text.get(), framer='rtu')
            asyncio.run(self.modbus_async_client.start_client())
        else:
            self.connect_button.config(text="Connect")
            self.connect_button.config(relief="raised")            
            self.connected = False
            self.ip_entry.config(state='normal')
            self.port_entry.config(state='normal')
            self.modbus_command_entry.config(state='disabled')
            self.modbus_async_client.stop_client()


    # Function to recieve msg
    def receive_message_from_server(self, buffer):
        print(buffer)
        print(type(buffer))
        self.pressure_sensor_val.set(buffer)
        self.modbus_log_text.insert('end', 'rcvd ' + str(buffer) +'\n') #' '.join(re.findall('..?', buffer.hex())) + '\n')
        self.modbus_log_text.yview('end')
    
    
    # Put pressure sensor label on the form
    def display_pressure_sensor(self):
        # Pressure sensors Frame
        self.frame_pressure = Frame(self.frame_sensors, bg='grey')
        self.frame_pressure.pack(side='left', anchor='nw', padx=3, pady=3)
        # Pressure sensor label
        self.pressure_sensor_label = Label(self.frame_pressure, text='Pressure', font=("arial", 10, "bold"), bg='grey')
        self.pressure_sensor_label.pack(side='top', anchor='nw', padx=3, pady=3, ipady=2)
        # Pressure sensor value
        self.pressure_sensor_val_label = Label(self.frame_pressure, text='', font=("arial", 10, "bold"))
        self.pressure_sensor_val_label.pack(side='top', padx=3, pady=3, ipady=2, fill='x')
        self.pressure_sensor_val = StringVar()
        self.pressure_sensor_val_label['textvariable'] = self.pressure_sensor_val    
        self.pressure_sensor_val.set('0000')

        
    # Put compass sensors labels on the form
    def display_compass_sensors(self): 
        # Compass sensors Frame
        self.frame_compass = Frame(self.frame_sensors, bg='grey')
        self.frame_compass.pack(side='right', anchor='ne', padx=3, pady=3, ipadx=2)
    
        # Compass sensors label
        self.compass_label1 = Label(self.frame_compass, text='Com-', width=4, font=("arial", 10, "bold"), bg='grey')
        self.compass_label1.grid(column=1, row=0, ipadx=2, ipady=2)
        self.compass_label2 = Label(self.frame_compass, text='pass', width=4, font=("arial", 10, "bold"), bg='grey')
        self.compass_label2.grid(column=1, row=1, ipadx=2, ipady=2)
        
        # Compass CalStatus label
        self.CalStatus_label = Label(self.frame_compass, text='CalStatus', font=("arial", 10, "bold"))
        self.CalStatus_label.grid(column=2, row=0, pady=3, padx=2, ipady=2, sticky='we')
        # Compass CalStatus value
        self.CalStatus_val_label = Label(self.frame_compass, text='0000', font=("arial", 10, "bold"))        
        self.CalStatus_val_label.grid(column=2, row=1, pady=3, padx=2, ipady=2, sticky='we')
        self.CalStatus_val = StringVar()
        self.CalStatus_val_label['textvariable'] = self.CalStatus_val
        self.CalStatus_val.set('0000')

        # Compass Tempr label
        self.Tempr_label = Label(self.frame_compass, text='Tempr', font=("arial", 10, "bold"))
        self.Tempr_label.grid(column=3, row=0,  pady=3, padx=2, ipady=2, sticky='we')
        # Compass Tempr value
        self.Tempr_val_label = Label(self.frame_compass, text='0000', font=("arial", 10, "bold"))        
        self.Tempr_val_label.grid(column=3, row=1,  pady=3, padx=2, ipady=2, sticky='we')
        self.Tempr_val = StringVar()
        self.Tempr_val_label['textvariable'] = self.Tempr_val
        self.Tempr_val.set('0000')
        
        # Compass Pitch label
        self.Pitch_label = Label(self.frame_compass, text='Pitch', font=("arial", 10, "bold"))
        self.Pitch_label.grid(column=4, row=0,  pady=3, padx=2, ipady=2, sticky='we')
        # Compass Pitch value
        self.Pitch_val_label = Label(self.frame_compass, text='0000', font=("arial", 10, "bold"))        
        self.Pitch_val_label.grid(column=4, row=1,  pady=3, padx=2, ipady=2, sticky='we')
        self.Pitch_val = StringVar()
        self.Pitch_val_label['textvariable'] = self.Pitch_val
        self.Pitch_val.set('0000')
        
        # Compass Heading label
        self.Heading_label = Label(self.frame_compass, text='Heading', font=("arial", 10, "bold"))
        self.Heading_label.grid(column=5, row=0,  pady=3, padx=2, ipady=2, sticky='we')
        # Compass Heading value
        self.Heading_val_label = Label(self.frame_compass, text='0000', font=("arial", 10, "bold"))        
        self.Heading_val_label.grid(column=5, row=1,  pady=3, padx=2, ipady=2, sticky='we')
        self.Heading_val = StringVar()
        self.Heading_val_label['textvariable'] = self.Heading_val
        self.Heading_val.set('0000')
        
    
    # Put light buttons on the form
    def display_light_buttons(self):
        self.frame_light = Frame(self.frame_left_bottom, bg='orange')
        self.frame_light.pack(side='right', anchor='se') # Light buttons frame.pack()
        # Create Light1 OFF Button
        self.light1_button = Button(self.frame_light, text="Light1 OFF", font=("arial", 10, "bold"), command=self.on_light1)
        self.light1_button.pack(side='left', padx=5, pady=5)
        # Create Light2 OFF Button
        self.light2_button = Button(self.frame_light, text="Light2 OFF", font=("arial", 10, "bold"), command=self.on_light2)
        self.light2_button.pack(side='left', padx=5, pady=5)
        # Create Light3 OFF Button
        self.light3_button = Button(self.frame_light, text="Light3 OFF", font=("arial", 10, "bold"), command=self.on_light3)
        self.light3_button.pack(side='left', padx=5, pady=5)
        # Create Light4 OFF Button
        self.light4_button = Button(self.frame_light, text="Light4 OFF", font=("arial", 10, "bold"), command=self.on_light4)
        self.light4_button.pack(side='left', padx=5, pady=5)


    def on_light1(self):
        if self.light1_button.config('relief')[-1] == 'sunken':
            self.light1_button.config(relief="raised")
            self.light1_button.config(text="Light1 OFF")
            self.send_message(bytearray.fromhex('AA 05 00 00 00 00'))
        else:
            self.light1_button.config(relief="sunken")
            self.light1_button.config(text="Light1 ON")
            self.send_message(bytearray.fromhex('AA 05 00 00 FF 00'))

    def on_light2(self):
        if self.light2_button.config('relief')[-1] == 'sunken':
            self.light2_button.config(relief="raised")
            self.light2_button.config(text="Light2 OFF")
            self.send_message(bytearray.fromhex('AA 05 00 01 00 00'))
        else:
            self.light2_button.config(relief="sunken")
            self.light2_button.config(text="Light2 ON")
            self.send_message(bytearray.fromhex('AA 05 00 01 FF 00'))

    def on_light3(self):
        if self.light3_button.config('relief')[-1] == 'sunken':
            self.light3_button.config(relief="raised")
            self.light3_button.config(text="Light3 OFF")
            self.send_message(bytearray.fromhex('BB 05 00 00 00 00'))
        else:
            self.light3_button.config(relief="sunken")
            self.light3_button.config(text="Light3 ON")
            self.send_message(bytearray.fromhex('BB 05 00 00 FF 00'))

    def on_light4(self):
        if self.light4_button.config('relief')[-1] == 'sunken':
            self.light4_button.config(relief="raised")
            self.light4_button.config(text="Light4 OFF")
            self.send_message(bytearray.fromhex('BB 05 00 01 00 00'))
        else:
            self.light4_button.config(relief="sunken")
            self.light4_button.config(text="Light4 ON")
            self.send_message(bytearray.fromhex('BB 05 00 01 FF 00'))

    # Put "Modbus command" Entry box on the form
    def display_modbus_command_entry_box(self):
        # Modbus command Frame
        self.frame_mb_com = Frame(self.frame_right)        
        self.frame_mb_com.pack(side='top', anchor='nw', fill='x') # Modbus command frame.pack()
        # Modbus command Label
        label = Label(self.frame_mb_com, text='Modbus command, crc auto', font=("arial", 10, "bold"))
        label.pack(side='top', anchor='nw',  ipadx=5, ipady=5)
        # Modbus command Entry
        self.modbus_command_entry = Entry(self.frame_mb_com, width=50, font=("arial", 10, "bold"))
        self.modbus_command_entry.pack(side='top', anchor='nw', padx=5)
        # Bind Enter key to a handler function
        self.modbus_command_entry.bind('<Return>', self.on_modbus_command_enter_pressed)
        self.modbus_command_entry.config(state='disabled')

    # Put "Modbus log" transcript area Text box on the form
    def display_modbus_log_text_box(self):
        # Modbus log Frame
        self.frame_mb_log = Frame(self.frame_right)
        self.frame_mb_log.pack(side='top', anchor='nw', expand='true', fill='both', padx=5, pady=5) # Modbus log frame.pack()
        # Modbus log Label
        label = Label(self.frame_mb_log, text='Modbus log', font=("arial", 10, "bold"))
        label.pack(side='top', anchor='nw',  ipadx=5, ipady=5)        
        # Modbus log Text box 
        self.modbus_log_text = Text(self.frame_mb_log, width=10, font=("arial", 10, "bold"))
        self.modbus_log_text.pack(side='left', anchor='w', expand='true', fill='both')
        # Modbus log  Scrollbar
        scrollbar = Scrollbar(self.frame_mb_log, command=self.modbus_log_text.yview, orient='vertical')        
        scrollbar.pack(side='right', fill='y', padx=2)
        self.modbus_log_text.config(yscrollcommand=scrollbar.set)
        self.modbus_log_text.bind('<KeyPress>', lambda e: 'break') 

    # Handle Enter key press
    def on_modbus_command_enter_pressed(self, event):
        self.send_modbus_command()

    # Send Modbus command to the remote server
    def send_modbus_command(self):
        data = self.modbus_command_entry.get().strip()
        message = bytearray.fromhex(data)
        #self.send_message(message)

        return 'break'

    # Calculate CRC
    def modbusCrc(self, msg):
        crc = 0xFFFF
        for n in range(len(msg)):
            crc ^= msg[n]
            for i in range(8):
                if crc & 1:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    # Send message to the remote server
    def send_message(self, message):
        if not(self.connected):
            messagebox.showerror("Error", "Not connected")
            return
        crc = self.modbusCrc(message)
#        print("0x%04X"%(crc))
        ba = crc.to_bytes(2, byteorder='little')
#        print("%02X %02X"%(ba[0], ba[1]))
        message.append(ba[0])
        message.append(ba[1])
#        self.modbus_log_text.insert('end', message.decode('utf-8') + '\n')
        self.modbus_log_text.insert('end', 'send ' + ' '.join(re.findall('..?', message.hex()))+ '\n')
        self.modbus_log_text.yview(END)
        #self.client_socket.send(message)

    # Handle closing the window
    def on_close_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()
            #if self.connected: self.client_socket.close()
            exit(0)

# The main function 
if __name__ == '__main__':
    root = Tk()
    gui = GUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_close_window)
    root.mainloop()
