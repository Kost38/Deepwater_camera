#!/usr/bin/python3

from tkinter import Tk, Frame, Scrollbar, Label, END, Entry, Text, VERTICAL, Button, messagebox, StringVar #Tkinter Python Module for GUI  
import socket #Sockets for network connection
import threading # for multiple proccess 
import binascii
import datetime, time
import re


class GUI:
    client_socket = None
    last_received_message = None
    connected = False

    def __init__(self, master):
        self.root = master
        self.chat_transcript_area = None
        self.ip_widget = None
        self.port_widget = None
        self.enter_text_widget = None
        self.join_button = None
        self.initialize_gui()


    def initialize_socket(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # initialazing socket with TCP and IPv4
        remote_ip = self.ip_widget_text.get() # IP address 
        remote_port = int(self.port_widget_text.get()) #TCP port
        try:
            self.client_socket.connect((remote_ip, remote_port)) #connect to the remote server
        except socket.error as e:
            messagebox.showerror("Error", "Connection error: %s" % e) 
            return 1
        return 0

    def initialize_gui(self): # GUI initializer
        self.root.title("Deepwater camera") 
        self.root.resizable(0, 0)
        self.display_name_section()
        self.display_control_buttons()
        self.display_chat_entry_box()
        self.display_chat_box()

    def sensors_thread_start(self):
        timerThread = threading.Thread(target=self.sensors_thread)
        timerThread.daemon = True
        timerThread.start()
        
    def sensors_thread(self):
        next_call = time.time()
        while True:
#            print(datetime.datetime.now())
#            self.send_message(bytearray.fromhex('AA 01 00 00 00 08'))
#            self.send_message(bytearray.fromhex('BB 01 00 00 00 08'))
            self.send_message(bytearray.fromhex('F0 04 00 00 00 01'))
            next_call = next_call+1
            time.sleep(next_call - time.time())


    def listen_for_incoming_messages_in_a_thread(self):
        thread = threading.Thread(target=self.receive_message_from_server, args=(self.client_socket,)) # Create a thread for the send and receive in same time 
        thread.daemon = True
        thread.start()

    #function to recieve msg
    def receive_message_from_server(self, so):
        while True:
            buffer = so.recv(256)
            if not buffer:
                break
            #message = buffer.decode('utf-8')
            self.chat_transcript_area.insert('end', 'rcvd ' + ' '.join(re.findall('..?', buffer.hex())) + '\n')
            self.chat_transcript_area.yview(END)

        so.close()

    def display_name_section(self):
        frame = Frame()
        Label(frame, text='IP ', font=("arial", 13,"bold")).pack(side='left', pady=20)
        self.ip_widget_text = StringVar()
        self.ip_widget = Entry(frame, textvariable=self.ip_widget_text, width=15,font=("arial", 13))
        self.ip_widget.pack(side='left', anchor='e',  pady=15)
        Label(frame, text=' port ', font=("arial", 13,"bold")).pack(side='left', pady=20)
        self.port_widget_text = StringVar()
        self.port_widget = Entry(frame, textvariable=self.port_widget_text, width=5,font=("arial", 13))
        self.port_widget.pack(side='left', anchor='e',  pady=15)
        self.join_button = Button(frame, text="Connect", width=10, command=self.on_join)
        self.join_button.pack(side='right',padx=5, pady=15)
        frame.pack(side='top', anchor='nw')
        self.ip_widget_text.set("192.168.1.67")
        self.port_widget_text.set("4001")


    def display_control_buttons(self):
        frame = Frame()
        self.command1_button = Button(frame, text="R1 OFF", width=10, command=self.on_command1)
        self.command1_button.pack(side='left',padx=5, pady=15)
        self.command2_button = Button(frame, text="R2 OFF", width=10, command=self.on_command2)
        self.command2_button.pack(side='left',padx=5, pady=15)
        self.command3_button = Button(frame, text="R3 OFF", width=10, command=self.on_command3)
        self.command3_button.pack(side='left',padx=5, pady=15)
        self.command4_button = Button(frame, text="R4 OFF", width=10, command=self.on_command4)
        self.command4_button.pack(side='left',padx=5, pady=15)
        frame.pack(side='top', anchor='nw')

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


    def display_chat_box(self):
        frame = Frame()
        Label(frame, text='Modbus log', font=("arial", 12,"bold")).pack(side='top', padx=270)
        self.chat_transcript_area = Text(frame, width=60, height=10, font=("arial", 12))
        scrollbar = Scrollbar(frame, command=self.chat_transcript_area.yview, orient=VERTICAL)
        self.chat_transcript_area.config(yscrollcommand=scrollbar.set)
        self.chat_transcript_area.bind('<KeyPress>', lambda e: 'break')
        self.chat_transcript_area.pack(side='left', padx=15, pady=10)
        scrollbar.pack(side='right', fill='y',padx=1)
        frame.pack(side='left')

    def display_chat_entry_box(self):   
        frame = Frame()
        Label(frame, text='Modbus command, crc auto', font=("arial", 12,"bold")).pack(side='top', anchor='w', padx=120)
        self.enter_text_widget = Entry(frame, width=50, font=("arial", 12))
        self.enter_text_widget.pack(side='left', pady=10, padx=10)
        self.enter_text_widget.bind('<Return>', self.on_enter_key_pressed)
        frame.pack(side='left')

    def on_join(self):
        if len(self.ip_widget.get()) == 0 or len(self.port_widget.get()) == 0:
            messagebox.showerror("Error", "Ip or port error")
            return
        if self.initialize_socket() > 0: return
        self.connected = True
        self.listen_for_incoming_messages_in_a_thread()
        self.sensors_thread_start()
        self.ip_widget.config(state='disabled')
        self.port_widget.config(state='disabled')
        self.join_button.config(state='disabled')

#        self.client_socket.send(("joined:" + self.name_widget.get()).encode('utf-8'))

    def on_enter_key_pressed(self, event):
        self.send_chat()


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
#        self.chat_transcript_area.insert('end', message.decode('utf-8') + '\n')
        self.chat_transcript_area.insert('end', 'send ' + ' '.join(re.findall('..?', message.hex()))+ '\n')
        self.chat_transcript_area.yview(END)
        self.client_socket.send(message)


    def send_chat(self):
#        senders_name = self.name_widget.get().strip() + ": "
        data = self.enter_text_widget.get().strip()
        message = bytearray.fromhex(data)
        self.send_message(message)
#        self.enter_text_widget.delete(1.0, 'end')
        return 'break'

    def on_close_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()
            if self.connected: self.client_socket.close()
            exit(0)

#the mail function 
if __name__ == '__main__':
    root = Tk()
    gui = GUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_close_window)
    root.mainloop()
