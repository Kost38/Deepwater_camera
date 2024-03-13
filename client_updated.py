#!/usr/bin/python3

#Tkinter Python Module for GUI
from tkinter import Tk, Frame, Scrollbar, Label, END, Entry, Text, VERTICAL, Button, messagebox, StringVar  

import socket #Sockets for network connection
import threading # for multiple proccess 
import binascii
import datetime, time
import re


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
        self.root.resizable(0, 0)
        self.display_connect_section()
        self.display_pressure_sensor()
        self.display_control_buttons()
        self.display_modbus_command_entry_box()
        self.display_modbus_log_text_box()    
        
    # Put IP adress Entry, Port Entry boxes and Connect Button on the form
    def display_connect_section(self):
        frame = Frame()
        
        # Create IP adress Entry
        Label(frame, text='IP ', font=("arial", 13,"bold")).pack(side='left', pady=20)
        self.ip_entry_text = StringVar()
        self.ip_entry = Entry(frame, textvariable=self.ip_entry_text, width=15,font=("arial", 13))
        self.ip_entry.pack(side='left', anchor='e',  pady=15)
        
        # Create Port Entry
        Label(frame, text=' port ', font=("arial", 13,"bold")).pack(side='left', pady=20)
        self.port_entry_text = StringVar()
        self.port_entry = Entry(frame, textvariable=self.port_entry_text, width=5,font=("arial", 13))
        self.port_entry.pack(side='left', anchor='e',  pady=15)

        # Create Connect Button
        self.connect_button = Button(frame, text="Connect", width=10, command=self.on_connect)
        self.connect_button.pack(side='right',padx=5, pady=15)
        
        frame.grid(column=0, row=0) # pack(side='top', anchor='nw')        
        self.ip_entry_text.set("192.168.1.67")
        self.port_entry_text.set("4001")
        # self.ip_entry_text.set("127.0.0.1")
        # self.port_entry_text.set(10319)

  
    # Handle "Connect" button click
    def on_connect(self):
        if len(self.ip_entry.get()) == 0 or len(self.port_entry.get()) == 0:
            messagebox.showerror("Error", "Ip or port error")
            return
        if self.initialize_socket() > 0: return
        self.connected = True
        self.listen_for_incoming_messages_in_a_thread()
        self.send_messages_to_sensors_in_a_thread()
        # Disable connect section
        self.ip_entry.config(state='disabled')
        self.port_entry.config(state='disabled')
        self.connect_button.config(state='disabled')
        # self.client_socket.send(("joined:" + self.name_widget.get()).encode('utf-8'))

    # Initialize socket and connect to the remote server
    def initialize_socket(self):
        # Initialazing socket with TCP and IPv4
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # IP address 
        remote_ip = self.ip_entry_text.get()
        # TCP port
        remote_port = int(self.port_entry_text.get()) 
        try:
            # Connect to the remote server
            self.client_socket.connect((remote_ip, remote_port)) 
        except socket.error as e:
            messagebox.showerror("Error", "Connection error: %s" % e) 
            return 1
        return 0

    def listen_for_incoming_messages_in_a_thread(self):
        # Create a thread for the send and receive in same time 
        thread = threading.Thread(target=self.receive_message_from_server, args=(self.client_socket,))
        thread.daemon = True
        thread.start()

    # Function to recieve msg
    def receive_message_from_server(self, socket):        
        while True:
            buffer = socket.recv(256)
            if not buffer:
                break
            # message = buffer.decode('utf-8')            
            self.pressure_sensor_val.set(buffer[4:6].hex())
            self.modbus_log_text.insert('end', 'rcvd ' + ' '.join(re.findall('..?', buffer.hex())) + '\n')
            self.modbus_log_text.yview(END)

        socket.close()
    
    def send_messages_to_sensors_in_a_thread(self):
        timerThread = threading.Thread(target=self.send_messages_to_sensors)
        timerThread.daemon = True
        timerThread.start()
        
    def send_messages_to_sensors(self):
        next_call = time.time()
        while True:
#            print(datetime.datetime.now())
#            self.send_message(bytearray.fromhex('AA 01 00 00 00 08'))
#            self.send_message(bytearray.fromhex('BB 01 00 00 00 08'))
            self.send_message(bytearray.fromhex('F0 04 00 00 00 01'))
            next_call = next_call+1
            time.sleep(next_call - time.time())

    # Put pressure sensor label on the form
    def display_pressure_sensor(self):
        frame = Frame()        
        # Create pressure sensor caption label
        self.pressure_sensor_label = Label(frame, text='Pressure sensor', font=("arial", 13,"bold"))
        self.pressure_sensor_label.pack(side='top', pady=20)
        # Create pressure sensor value label
        self.pressure_sensor_val_label = Label(frame, text='', font=("arial", 13,"bold"))        
        self.pressure_sensor_val_label.pack(side='right', pady=20)
        self.pressure_sensor_val = StringVar()
        self.pressure_sensor_val_label['textvariable'] = self.pressure_sensor_val    
        self.pressure_sensor_val.set('0000')
        frame.grid(column=1, row=0) # pack(side='top', anchor='ne')
    
    # Put control buttons on the form
    def display_control_buttons(self):
        frame = Frame()
        # Create R1 OFF Button
        self.command1_button = Button(frame, text="R1 OFF", width=10, command=self.on_command1)
        self.command1_button.pack(side='left',padx=5, pady=15)
        # Create R2 OFF Button
        self.command2_button = Button(frame, text="R2 OFF", width=10, command=self.on_command2)
        self.command2_button.pack(side='left',padx=5, pady=15)
        # Create R3 OFF Button
        self.command3_button = Button(frame, text="R3 OFF", width=10, command=self.on_command3)
        self.command3_button.pack(side='left',padx=5, pady=15)
        # Create R4 OFF Button
        self.command4_button = Button(frame, text="R4 OFF", width=10, command=self.on_command4)
        self.command4_button.pack(side='left',padx=5, pady=15)
        frame.grid(column=0, row=1) #.pack(side='left', anchor='nw')

    def on_command1(self):
        if self.command1_button.config('relief')[-1] == 'sunken':
            self.command1_button.config(relief="raised")
            self.command1_button.config(text="R1 OFF")
            self.send_message(bytearray.fromhex('AA 05 00 00 00 00'))
        else:
            self.command1_button.config(relief="sunken")
            self.command1_button.config(text="R1 ON")
            self.send_message(bytearray.fromhex('AA 05 00 00 FF 00'))

    def on_command2(self):
        if self.command2_button.config('relief')[-1] == 'sunken':
            self.command2_button.config(relief="raised")
            self.command2_button.config(text="R2 OFF")
            self.send_message(bytearray.fromhex('AA 05 00 01 00 00'))
        else:
            self.command2_button.config(relief="sunken")
            self.command2_button.config(text="R2 ON")
            self.send_message(bytearray.fromhex('AA 05 00 01 FF 00'))

    def on_command3(self):
        if self.command3_button.config('relief')[-1] == 'sunken':
            self.command3_button.config(relief="raised")
            self.command3_button.config(text="R3 OFF")
            self.send_message(bytearray.fromhex('BB 05 00 00 00 00'))
        else:
            self.command3_button.config(relief="sunken")
            self.command3_button.config(text="R3 ON")
            self.send_message(bytearray.fromhex('BB 05 00 00 FF 00'))

    def on_command4(self):
        if self.command4_button.config('relief')[-1] == 'sunken':
            self.command4_button.config(relief="raised")
            self.command4_button.config(text="R4 OFF")
            self.send_message(bytearray.fromhex('BB 05 00 01 00 00'))
        else:
            self.command4_button.config(relief="sunken")
            self.command4_button.config(text="R4 ON")
            self.send_message(bytearray.fromhex('BB 05 00 01 FF 00'))


    # Put "Modbus log" transcript area Text box on the form
    def display_modbus_log_text_box(self):
        frame = Frame()
        # Create "Modbus log" Text box
        Label(frame, text='Modbus log', font=("arial", 12,"bold")).pack(side='top', padx=270)
        self.modbus_log_text = Text(frame, width=60, height=10, font=("arial", 12))
        # Create a scrollbar for the Text box
        scrollbar = Scrollbar(frame, command=self.modbus_log_text.yview, orient=VERTICAL)
        # Attach a Scrollbar to the Text transcript area
        self.modbus_log_text.config(yscrollcommand=scrollbar.set)
        self.modbus_log_text.bind('<KeyPress>', lambda e: 'break')
        self.modbus_log_text.pack(side='left', padx=15, pady=10)
        scrollbar.pack(side='right', fill='y',padx=1)
        frame.grid(column=1, row=2) #.pack(side='left')

    # Put "Modbus command" Entry box on the form
    def display_modbus_command_entry_box(self):   
        frame = Frame()        
        # Create "Modbus command" Entry
        Label(frame, text='Modbus command, crc auto', font=("arial", 12,"bold")).pack(side='top', anchor='w', padx=120)
        self.modbus_command_entry = Entry(frame, width=50, font=("arial", 12))
        self.modbus_command_entry.pack(side='left', pady=10, padx=10)
        # Bind Enter key to a handler function
        self.modbus_command_entry.bind('<Return>', self.on_modbus_command_enter_pressed)        
        frame.grid(column=0, row=2) #.pack(side='left')

    # Handle Enter key press
    def on_modbus_command_enter_pressed(self, event):
        self.send_modbus_command()

    # Send Modbus command to the remote server
    def send_modbus_command(self):
#        senders_name = self.name_widget.get().strip() + ": "
        data = self.modbus_command_entry.get().strip()
        message = bytearray.fromhex(data)
        self.send_message(message)
#        self.modbus_command_entry.delete(1.0, 'end')
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
        self.client_socket.send(message)

    # Handle closing the window
    def on_close_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()
            if self.connected: self.client_socket.close()
            exit(0)

# The main function 
if __name__ == '__main__':
    root = Tk()
    gui = GUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_close_window)
    root.mainloop()
