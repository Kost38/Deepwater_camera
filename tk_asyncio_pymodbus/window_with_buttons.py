#!/usr/bin/python3

#Tkinter Python Module for GUI
from tkinter import Frame, Label, Button, Entry, Text, Scrollbar, messagebox, StringVar
import asyncio

import socket #Sockets for network connection
import threading # for multiple proccess 
import binascii
import datetime, time
#import re

from modbus_async_client_wrapper import ModbusAsyncClientWrapper
from video_player import VideoPlayer

class GUI:
    client_socket = None
    last_received_message = None
    next_srt_time = datetime.timedelta(microseconds = 1)
    next_time = datetime.datetime.now()
    next_depth = 0

    # Constructor
    def __init__(self, tk_root, mainframe, put_command_for_asyncio_loop_to_queue_callback, delay_after_chain_of_commands, modbus_timeout, host, port):
        self.tk_root = tk_root
        self.mainframe = mainframe
        self.put_command_for_asyncio_loop_to_queue = put_command_for_asyncio_loop_to_queue_callback
        self.delay_after_chain_of_commands = delay_after_chain_of_commands
        self.modbus_timeout = modbus_timeout
        self.host = host
        self.port = port
        self.ip_entry = None
        self.port_entry = None
        self.connect_button = None
        self.pressure_sensor_label = None
        self.pressure_sensor_val_label = None
        self.pressure_sensor_val = None
        self.modbus_command_entry = None
        self.modbus_log_text = None
        self.async_task = None
        self.sensors_chain_started = False
        self.stop_sensors_clicked_by_light = False
        self.initialize_gui()

    # GUI initializer
    def initialize_gui(self):
        self.tk_root.title("Deepwater camera") 
        self.tk_root.protocol("WM_DELETE_WINDOW", self.on_close_window)
        # Make window expandable        
        self.tk_root.grid_rowconfigure(0, weight=1)
        self.tk_root.grid_columnconfigure(0, weight=1)
        # Left frame in the window
        self.frame_left = Frame()
        self.frame_left.pack(side='left', anchor='w', expand='true', fill='both')
        # Right frame in the window
        self.frame_right = Frame(width = 500)
        self.frame_right.pack(side='right', anchor='e', fill='both')
        self.frame_right.pack_propagate('false')
        # Bottom frame in the left frame
#        self.frame_left_bottom = Frame(self.frame_left, bg='yellow') 
#        self.frame_left_bottom.pack(side='bottom', anchor='sw', fill='x') # Left Bottom frame.pack()  

        # Display part of layout

        self.display_connect_section()
        self.frame_left_bottom = Frame(self.frame_right, bg='yellow') 
        self.frame_left_bottom.pack(side='top', anchor='nw', fill='x') # Left Bottom frame.pack()  
        self.display_video_player()
        # Add sensors frame in the right frame
        self.frame_sensors = Frame(self.frame_right)
        self.frame_sensors.pack(side='top', anchor='nw', fill='x') # Sensors frame.pack()
        self.display_light_buttons()
        # Display rest layout
        self.display_pressure_sensor()
        self.display_compass_sensors()
        self.display_modbus_command_entry_box()
        self.display_modbus_log_text_box()

    def display_video_player(self):
        # Video player Frame
        self.video_frame = Frame(self.frame_left, width=500, height=400, bg='black')
        self.video_frame.pack(side='top', anchor='nw', expand='true', fill='both',) # Video frame frame.pack()

        self.video_start_button = Button(self.frame_left_bottom, text="Start video", font=("arial", 10, "bold"), 
            command = lambda: self.on_video_start_button()
        )
        self.video_start_button.pack(side='left', anchor='sw', padx=5, pady=5)       
        
        self.video_record_button = Button(self.frame_left_bottom, text="Record", font=("arial", 10, "bold"), 
            command = lambda: self.on_video_record_button()
        )
        self.video_record_button.pack(side='left', anchor='sw', padx=5, pady=5) 
        self.video_record_button.config(state='disabled')

    def on_video_start_button(self):
        if self.video_start_button.config('relief')[-1] == 'raised':
            # Init VideoPlayer (with frame_id)
            self.videoPlayer = VideoPlayer(self.video_frame.winfo_id())            
            self.video_start_button.config(text="Stop video")
            self.video_start_button.config(relief="sunken") 
            self.video_record_button.config(state='normal')
        else:
            if (self.videoPlayer.recording):
                self.video_record_button.config(text="Record")
                self.video_record_button.config(relief="raised")
                
            self.videoPlayer.stop_video()    
            #del self.videoPlayer
            
            self.video_start_button.config(text="Start video")
            self.video_start_button.config(relief="raised")
            self.video_record_button.config(state='disabled')
            
    def on_video_record_button(self):
        if self.video_record_button.config('relief')[-1] == 'raised':
            self.video_record_button.config(relief="sunken") 
            self.video_record_button.config(text="Recording...")
            self.frame_left_bottom.configure(bg="red")
            self.videoPlayer.start_record()           
        else:
            self.videoPlayer.stop_record()
            self.next_srt_time = datetime.timedelta(microseconds = 1)
            self.next_time = datetime.datetime.now()
            self.next_depth = 0
            self.video_record_button.config(text="Record")
            self.frame_left_bottom.configure(bg="yellow")
            self.video_record_button.config(relief="raised")

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
        
        # Host and port values         
        self.ip_entry_text.set(self.host)
        self.port_entry_text.set(self.port)
        
        # Connect Button
        self.connect_button = Button(
            self.frame_connect, text="Connect", font=("arial", 10, "bold"), command=self.on_connect)
        self.connect_button.pack(side='left', padx=5, pady=5)                
                
      
        # Frame
        self.frame_buttons = Frame(self.frame_right)
        self.frame_buttons.pack(side='top', anchor='nw', ipadx=5, ipady=3) # Connect Section frame.pack()
        
        # Calibrate compass Button
        self.calibrate_compass_button = Button(
            self.frame_buttons, text="Calibrate compass", font=("arial", 10, "bold"), command=self.on_calibrate_compass)
        self.calibrate_compass_button.pack(side='left', padx=3, pady=3)
        self.calibrate_compass_button.config(state='disabled') 
        
        # Correct compass north Button
        self.correct_compass_north_button = Button(
            self.frame_buttons, text="Correct north", font=("arial", 10, "bold"), command=self.on_correct_compass_north)
        self.correct_compass_north_button.pack(side='left', padx=3, pady=3)
        self.correct_compass_north_button.config(state='disabled') 
        
        # Save configuration Button
        self.save_compass_configuration_button = Button(
            self.frame_buttons, text="Save config", font=("arial", 10, "bold"), command=self.on_save_compass_configuration)
        self.save_compass_configuration_button.pack(side='left', padx=3, pady=3)
        self.save_compass_configuration_button.config(state='disabled') 
        
       
        # Frame
        self.frame_buttons = Frame(self.frame_right)
        self.frame_buttons.pack(side='top', anchor='nw', ipadx=5, ipady=3) # Connect Section frame.pack()
        
        # Start transacting with sensors Button
        self.start_sensors_button = Button(
            self.frame_buttons, text="Start sensors", font=("arial", 10, "bold"), command=self.on_start_sensors)
        self.start_sensors_button.pack(side='left', padx=3, pady=3)
        self.start_sensors_button.config(state='disabled') 
        
        # Reset Button
        self.reset_compass_button = Button(
            self.frame_buttons, text="Reset", font=("arial", 10, "bold"), command=self.on_reset_compass)
        self.reset_compass_button.pack(side='right', padx=10, pady=3)
        self.reset_compass_button.config(state='disabled') 
        
        # Get CalStatus Button
        self.reset_compass_button = Button(
            self.frame_buttons, text="Get CalStatus", font=("arial", 10, "bold"), command=self.on_get_compass_calibration_status)
        self.reset_compass_button.pack(side='right', padx=3, pady=3)
        self.reset_compass_button.config(state='disabled') 


    # Create a modbus async client wrapper and connect to the server
    async def create_modbus_async_client_and_connect(self):
        # Create a wrapper object
        self.modbus_wrapper = ModbusAsyncClientWrapper(
            self.delay_after_chain_of_commands,
            self.modbus_timeout,
            comm='tcp', 
            host=self.ip_entry_text.get(), 
            port=self.port_entry_text.get(), 
            framer='rtu'            
        )
        # Create a future task: to create a modbus async client and to connect to the server
        connect_to_modbus_task = asyncio.ensure_future(self.modbus_wrapper.create_and_connect())        
        # Wait for the future result
        await connect_to_modbus_task
        
        return connect_to_modbus_task.result()
        
    # Handle "Connect/Disconnect" button click
    def on_connect(self):
        if self.connect_button.config('relief')[-1] == 'raised':
            self.put_command_for_asyncio_loop_to_queue('Connect', self.mainframe)            
        else:                   
            # Stop sensors if needed
            if self.start_sensors_button.config('relief')[-1] == 'sunken':                
                self.put_command_for_asyncio_loop_to_queue('StopSensors', self.mainframe, 'Disconnect handling') 
                self.put_command_for_asyncio_loop_to_queue('Disconnect', self.mainframe, 'Disconnect handling') 
            else:                
                self.put_command_for_asyncio_loop_to_queue('Disconnect', self.mainframe)

    def switch_on_connect(self):
        # Enable
        self.calibrate_compass_button.config(state='normal')
        self.correct_compass_north_button.config(state='normal')
        self.save_compass_configuration_button.config(state='normal')        
        self.reset_compass_button.config(state='normal')
        self.start_sensors_button.config(state='normal')
        self.modbus_command_entry.config(state='normal')
        self.light1_button.config(state='normal')
        self.light2_button.config(state='normal')
        self.light3_button.config(state='normal')
        self.light4_button.config(state='normal')
        # Disable
        self.ip_entry.config(state='disabled')
        self.port_entry.config(state='disabled')   
        # Sunk and rename
        self.connect_button.config(relief="sunken") 
        self.connect_button.config(text='Connected') # Instead of 'Connect'        

    def switch_on_disconnect(self):
        # Enable
        self.ip_entry.config(state='normal')
        self.port_entry.config(state='normal') 
        # Disable
        self.calibrate_compass_button.config(state='disabled')
        self.correct_compass_north_button.config(state='disabled')
        self.save_compass_configuration_button.config(state='disabled')
        self.reset_compass_button.config(state='disabled')
        self.start_sensors_button.config(state='disabled')
        self.modbus_command_entry.config(state='disabled')
        self.light1_button.config(state='disabled')
        self.light2_button.config(state='disabled')
        self.light3_button.config(state='disabled')
        self.light4_button.config(state='disabled') 
        # Raise and rename
        self.connect_button.config(relief="raised")
        self.connect_button.config(text='Connect') # Instead of 'Connected'     
        
        
    # Handle "Start/Stop sensors" button click
    def on_start_sensors(self): 
        if self.start_sensors_button.config('relief')[-1] == 'raised':
            self.put_command_for_asyncio_loop_to_queue('StartSensors', self.mainframe)            
        else:
            self.put_command_for_asyncio_loop_to_queue('StopSensors', self.mainframe) 
            
    def switch_on_start_sensors(self):
        # Disable
        self.calibrate_compass_button.config(state='disabled')
        self.correct_compass_north_button.config(state='disabled')
        self.save_compass_configuration_button.config(state='disabled')
        self.reset_compass_button.config(state='disabled')
        self.modbus_command_entry.config(state='disabled')
        # Sunk and rename
        self.start_sensors_button.config(text="Stop Sensors") # Instead of 'Start Sensors   
        self.start_sensors_button.config(relief="sunken")

    def switch_on_stop_sensors(self): 
        # Enable
        self.calibrate_compass_button.config(state='normal')
        self.correct_compass_north_button.config(state='normal')
        self.save_compass_configuration_button.config(state='normal')
        self.reset_compass_button.config(state='normal')
        self.modbus_command_entry.config(state='normal')
        # Raise and rename
        self.start_sensors_button.config(text="Start Sensors") # Instead of 'Stop Sensors 
        self.start_sensors_button.config(relief="raised")

    # Handle "Calibrate compass" button click
    def on_calibrate_compass(self): 
        if self.calibrate_compass_button.config('relief')[-1] == 'raised':            
            self.put_command_for_asyncio_loop_to_queue('StartCompassCalibration', self.mainframe)            
        else:            
            self.put_command_for_asyncio_loop_to_queue('StopCompassCalibration', self.mainframe) 
            
    def switch_on_start_compass_calibration(self): 
        # Disable
        self.connect_button.config(state='disabled')
        self.start_sensors_button.config(state='disabled')
        self.correct_compass_north_button.config(state='disabled')
        self.save_compass_configuration_button.config(state='disabled')
        self.reset_compass_button.config(state='disabled')
        self.modbus_command_entry.config(state='disabled')
        # Rename
        self.calibrate_compass_button.config(text="Stop calibrating") # Instead of 'Calibrate compass'
        self.calibrate_compass_button.config(relief="sunken")
        
    def switch_on_stop_compass_calibration(self): 
        # Enable
        self.connect_button.config(state='normal')
        self.start_sensors_button.config(state='normal')
        self.correct_compass_north_button.config(state='normal')
        self.save_compass_configuration_button.config(state='normal')
        self.reset_compass_button.config(state='normal')
        self.modbus_command_entry.config(state='normal')
        # Rename
        self.calibrate_compass_button.config(text="Calibrate compass") # Instead of 'Stop calibrating'
        self.calibrate_compass_button.config(relief="raised")
    
    # Handle "Correct Compass North" button click
    def on_correct_compass_north(self): 
        self.put_command_for_asyncio_loop_to_queue('CorrectCompassNorth', self.mainframe)            
         
    # Handle "Save Compass Configuration" button click
    def on_save_compass_configuration(self): 
        self.put_command_for_asyncio_loop_to_queue('SaveCompassConfiguration', self.mainframe)  
            
    # Handle "Reset compass" button click
    def on_reset_compass(self): 
        self.put_command_for_asyncio_loop_to_queue('ResetCompass', self.mainframe)
        
    # Handle "Reset Get CalStatus" button click
    def on_get_compass_calibration_status(self):
        self.put_command_for_asyncio_loop_to_queue('GetCompassCalibrationStatus', self.mainframe)

    async def handle_command_in_asyncio_loop(self, command_for_asyncio_loop):  
        timed_msg('-AIO: Got and handling a Tkinter command "' + command_for_asyncio_loop + '"')

        # Connect and check compass calibration status
        
        if (command_for_asyncio_loop == 'Connect'):
            async_modbus_task = asyncio.ensure_future(self.create_modbus_async_client_and_connect())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['ConnectCalled'] goes to queue_of_tasks_for_tk_loop
        
        if (command_for_asyncio_loop == 'GetCompassCalibrationStatus'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.read_cal_status_from_compass())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # 'CompassCalibrationStatusGot' Goes to queue_of_tasks_for_tk_loop
            
        # Compass configuration buttons
        
        if (command_for_asyncio_loop == 'StartCompassCalibration'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.start_compass_calibration())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['CompassCalibrationStarted'] Goes to queue_of_tasks_for_tk_loop
            
        if (command_for_asyncio_loop == 'StopCompassCalibration'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.stop_compass_calibration())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['CompassCalibrationStoped'] Goes to queue_of_tasks_for_tk_loop
            
        if (command_for_asyncio_loop == 'CorrectCompassNorth'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.correct_compass_north())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['CompassNorthCorrected'] Goes to queue_of_tasks_for_tk_loop
            
        if (command_for_asyncio_loop == 'SaveCompassConfiguration'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.save_compass_configuration())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['CompassConfigurationSaved'] Goes to queue_of_tasks_for_tk_loop

        if (command_for_asyncio_loop == 'ResetCompass'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.reset_compass())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # 'CompassResetCommited' Goes to queue_of_tasks_for_tk_loop
         
        # Sensors transaction sequence
         
        if (command_for_asyncio_loop == 'StartSensors'):
            return ['StartSensorsClicked'] # goes to queue_of_tasks_for_tk_loop 

        if (command_for_asyncio_loop == 'TransactPressure'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.transact_pressure_sensor())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['PressureTransacted', registers] Goes to queue_of_tasks_for_tk_loop            
            
        if (command_for_asyncio_loop == 'TransactCompassTempr'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.read_temperature_from_compass_sensor())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # 'CompassTemprTransacted' Goes to queue_of_tasks_for_tk_loop
            
        if (command_for_asyncio_loop == 'TransactCompassPitchHeading'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.read_pitch_heading_from_compass_sensor())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # 'CompassPitchHeadTransacted' Goes to queue_of_tasks_for_tk_loop
            
        if (command_for_asyncio_loop == 'WaitForNextIteration'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.wait_next_iteration())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # 'NexIterationWaited' goes to queue_of_tasks_for_tk_loop 

        if (command_for_asyncio_loop == 'StopSensors'):
            return ['StopSensorsClicked'] # Goes to queue_of_tasks_for_tk_loop 
            
        if (command_for_asyncio_loop == 'StopSensorsByLight'):
            if self.sensors_chain_started == True:
                return ['StopSensorsClicked'] # goes to queue_of_tasks_for_tk_loop
            else:
                return ['IdleWaited'] # goes to queue_of_tasks_for_tk_loop
            
        # Light buttons

        if (command_for_asyncio_loop == 'Light1 ON'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.turn_light1_on())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['Light1TurnedON'] goes to queue_of_tasks_for_tk_loop 
        
        if (command_for_asyncio_loop == 'Light1 OFF'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.turn_light1_off())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['Light1TurnedOFF'] goes to queue_of_tasks_for_tk_loop 

        if (command_for_asyncio_loop == 'Light2 ON'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.turn_light2_on())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['Light2TurnedON'] goes to queue_of_tasks_for_tk_loop 
        
        if (command_for_asyncio_loop == 'Light2 OFF'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.turn_light2_off())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['Light2TurnedOFF'] goes to queue_of_tasks_for_tk_loop 
            
        if (command_for_asyncio_loop == 'Light3 ON'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.turn_light3_on())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['Light3TurnedON'] goes to queue_of_tasks_for_tk_loop 
        
        if (command_for_asyncio_loop == 'Light3 OFF'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.turn_light3_off())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['Light3TurnedOFF'] goes to queue_of_tasks_for_tk_loop
            
        if (command_for_asyncio_loop == 'Light4 ON'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.turn_light4_on())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['Light4TurnedON'] goes to queue_of_tasks_for_tk_loop 
        
        if (command_for_asyncio_loop == 'Light4 OFF'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.turn_light4_off())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # ['Light4TurnedOFF'] goes to queue_of_tasks_for_tk_loop 

        # Disconnect

        if (command_for_asyncio_loop == 'Disconnect'):
            async_modbus_task = asyncio.ensure_future(self.modbus_wrapper.close_client())
            await async_modbus_task # Wait for the future
            return async_modbus_task.result() # 'Disconnected' goes to queue_of_tasks_for_tk_loop

        return ['IdleWaited'] # Goes to queue_of_tasks_for_tk_loop if command_for_asyncio_loop is unknown
        
    def handle_task_in_tk_loop(self, task_for_tk_loop):
        timed_msg('-TK: Got and handling an Asyncio task "' + task_for_tk_loop[0] + '"')
        
        # Connect button
        
        # Handle an Asincio's thread answer to Tkinter command 'Connect'
        if (task_for_tk_loop[0] == 'ConnectCalled'):
            if (self.modbus_wrapper.connection_status == 'Connected'):                                  
                self.switch_on_connect()                
                return 'GetCompassCalibrationStatus' # Goes to queue_of_commands_for_asyncio_loop
            else:                
                self.switch_on_disconnect()
                timed_msg('handle_task_in_tk_loop: task_for_tk_loop = ConnectCalled, modbus connection_status != connected')
                return 'Idle' # Goes to queue_of_commands_for_asyncio_loop
                
        # Handle an Asincio's thread answer to Tkinter command 'GetCompassCalibrationStatus'
        if (task_for_tk_loop[0] == 'CompassCalibrationStatusGot'):
            self.CalStatus_val.set(str(task_for_tk_loop[1])[:4])
            self.modbus_log_text.insert('end', 'CalStatus: ' + str(task_for_tk_loop[1]) + '\n')
            self.modbus_log_text.yview('end')
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = CompassCalibrationStatusGot')
            return 'Idle' # Goes to queue_of_commands_for_asyncio_loop

        # Compass configuration buttons

        # Handle an Asincio's thread answer to Tkinter command 'StartCompassCalibration'
        if (task_for_tk_loop[0] == 'CompassCalibrationStarted'):
            self.switch_on_start_compass_calibration()
            return 'GetCompassCalibrationStatus' # Goes to queue_of_commands_for_asyncio_loop
            
        # Handle an Asincio's thread answer to Tkinter command 'StopCompassCalibration'
        if (task_for_tk_loop[0] == 'CompassCalibrationStoped'):
            self.switch_on_stop_compass_calibration()
            return 'GetCompassCalibrationStatus' # Goes to queue_of_commands_for_asyncio_loop   
            
        # Handle an Asincio's thread answer to Tkinter command 'CorrectCompassNorth'
        if (task_for_tk_loop[0] == 'CompassNorthCorrected'):
            return 'GetCompassCalibrationStatus' # Goes to queue_of_commands_for_asyncio_loop
            
        # Handle an Asincio's thread answer to Tkinter command 'SaveCompassConfiguration'
        if (task_for_tk_loop[0] == 'CompassConfigurationSaved'):
            return 'GetCompassCalibrationStatus' # Goes to queue_of_commands_for_asyncio_loop

        # Handle an Asincio's thread answer to Tkinter command 'ResetCompass'
        if (task_for_tk_loop[0] == 'CompassResetCommited'):
            return 'GetCompassCalibrationStatus' # Goes to queue_of_commands_for_asyncio_loop
        
        # Handle Light Buttons

        # Handle an Asincio's thread answer to Tkinter command 'StopSensors'
        if (task_for_tk_loop[0] == 'Light1TurnedON'):
            self.switch_on_light1on()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = Light1TurnedON')
            return 'IdleFromLight' # Goes to queue_of_commands_for_asyncio_loop  
            
        if (task_for_tk_loop[0] == 'Light1TurnedOFF'):
            self.switch_on_light1off()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = Light1TurnedOFF')
            return 'IdleFromLight' # Goes to queue_of_commands_for_asyncio_loop

        # Handle an Asincio's thread answer to Tkinter command 'StopSensorsByLight'
        if (task_for_tk_loop[0] == 'Light2TurnedON'):
            self.switch_on_light2on()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = Light2TurnedON')
            return 'IdleFromLight' # Goes to queue_of_commands_for_asyncio_loop  
            
        if (task_for_tk_loop[0] == 'Light2TurnedOFF'):
            self.switch_on_light2off()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = Light2TurnedOFF')
            return 'IdleFromLight' # Goes to queue_of_commands_for_asyncio_loop

        # Handle an Asincio's thread answer to Tkinter command 'StopSensorsByLight'
        if (task_for_tk_loop[0] == 'Light3TurnedON'):
            self.switch_on_light3on()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = Light3TurnedON')
            return 'IdleFromLight' # Goes to queue_of_commands_for_asyncio_loop  
            
        if (task_for_tk_loop[0] == 'Light3TurnedOFF'):
            self.switch_on_light3off()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = Light3TurnedOFF')
            return 'IdleFromLight' # Goes to queue_of_commands_for_asyncio_loop
        
        # Handle an Asincio's thread answer to Tkinter command 'StopSensorsByLight'
        if (task_for_tk_loop[0] == 'Light4TurnedON'):
            self.switch_on_light4on()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = Light4TurnedON')
            return 'IdleFromLight' # Goes to queue_of_commands_for_asyncio_loop  
            
        if (task_for_tk_loop[0] == 'Light4TurnedOFF'):
            self.switch_on_light4off()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = Light4TurnedOFF')
            return 'IdleFromLight' # Goes to queue_of_commands_for_asyncio_loop

        # Sensors transaction sequence

        # Handle an Asincio's thread answer to Tkinter command 'StartSensors'
        if (task_for_tk_loop[0] == 'StartSensorsClicked'):
            self.sensors_chain_started = True
            self.switch_on_start_sensors()
            return 'TransactPressure' # Goes to queue_of_commands_for_asyncio_loop

        # Handle an Asincio's thread answer to Tkinter command 'TransactPressure'
        if (task_for_tk_loop[0] == 'PressureTransacted'):
            self.pressure_sensor_val.set(str(f"{format(task_for_tk_loop[1], '.1f')}"))
            self.modbus_log_text.insert('end', 'Pressure: ' + str(task_for_tk_loop[1]) + '\n')
            if(self.videoPlayer.recording):
                self.modbus_log_text.insert('end', 'Recording...' + '\n')
                self.videoPlayer.log_counter = self.videoPlayer.log_counter + 1
                now_time = datetime.datetime.now()
                srt_time = now_time - self.videoPlayer.start_record_time
                total_microseconds = srt_time.total_seconds() * 1000000
                rounded_milliseconds = round(total_microseconds / 1000)
                srt_time = datetime.timedelta(microseconds=rounded_milliseconds * 1000)
                self.videoPlayer.log_file.write(str(self.videoPlayer.log_counter) + '\n')
                self.videoPlayer.log_file.write(str(self.next_srt_time)[:-3].replace('.' , ',') + ' --> ' + str(srt_time)[:-3].replace('.' , ',') + '\n')
                self.videoPlayer.log_file.write('T: ' + self.next_time.strftime("%Y-%m-%d %H:%M:%S") + ' ')
                self.videoPlayer.log_file.write('D: ' + str(f"{format(self.next_depth, '.1f')}") + '\n\n')
                self.videoPlayer.log_file.flush()
                self.next_time = now_time
                self.next_depth = task_for_tk_loop[1]
                self.next_srt_time = srt_time
            self.modbus_log_text.yview('end')
            return 'TransactCompassTempr' # Goes to queue_of_commands_for_asyncio_loop

        # Handle an Asincio's thread answer to Tkinter command 'TransactCompassTempr'
        if (task_for_tk_loop[0] == 'CompassTemprTransacted'):
            self.Tempr_val.set(str(task_for_tk_loop[1])[:4])
            self.modbus_log_text.insert('end', 'Temperature: ' + str(task_for_tk_loop[1]) + '\n')
            self.modbus_log_text.yview('end')
            return 'TransactCompassPitchHeading' # Goes to queue_of_commands_for_asyncio_loop

        # Handle an Asincio's thread answer to Tkinter command 'TransactCompassPitchHeading'
        if (task_for_tk_loop[0] == 'CompassPitchHeadTransacted'):
            self.Pitch_val.set(str(task_for_tk_loop[1])[:4])
            self.Heading_val.set(str(task_for_tk_loop[2])[:4])
            self.modbus_log_text.insert('end', 'Pitch: ' + str(task_for_tk_loop[1]) + '\n') 
            self.modbus_log_text.insert('end', 'Heading: ' + str(task_for_tk_loop[2]) + '\n')
            self.modbus_log_text.yview('end')
            return 'WaitForNextIteration' # Goes to queue_of_commands_for_asyncio_loop
            
        # Handle an Asincio's thread answer to Tkinter command 'WaitForNextIteration'
        if (task_for_tk_loop[0] == 'NexIterationWaited'):        
            return 'TransactPressure' # Goes to queue_of_commands_for_asyncio_loop
            
        # Handle an Asincio's thread answer to Tkinter command 'StopSensors'
        if (task_for_tk_loop[0] == 'StopSensorsClicked'):
            self.sensors_chain_started = False
            self.switch_on_stop_sensors()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = StopSensorsClicked')
            return 'Idle' # Goes to queue_of_commands_for_asyncio_loop

        # Disconnect

        # Handle an Asincio's thread answer to Tkinter command 'Disconnect'
        if (task_for_tk_loop[0] == 'Disconnected'):
            self.switch_on_disconnect()
            timed_msg('handle_task_in_tk_loop: task_for_tk_loop = Disconnected')
            return 'Idle' # Goes to queue_of_commands_for_asyncio_loop  
            
        timed_msg('handle_task_in_tk_loop: task_for_tk_loop is unknown')
        return 'Idle' # Goes to queue_of_commands_for_asyncio_loop if task_for_tk_loop is unknown

    # Put pressure sensor label on the form
    def display_pressure_sensor(self):
        # Pressure sensors Frame
        self.frame_pressure = Frame(self.frame_sensors, bg='grey')
        self.frame_pressure.pack(side='left', anchor='nw', padx=3, pady=3)
        # Pressure sensor label
        self.pressure_sensor_label = Label(self.frame_pressure, text='Depth', font=("arial", 10, "bold"), bg='grey')
        self.pressure_sensor_label.pack(side='top', anchor='nw', padx=3, pady=3, ipady=2)
        # Pressure sensor value
        self.pressure_sensor_val_label = Label(self.frame_pressure, text='', font=("arial", 64, "bold"))
        self.pressure_sensor_val_label.pack(side='top', padx=3, pady=3, ipady=2, fill='x')
        self.pressure_sensor_val = StringVar()
        self.pressure_sensor_val_label['textvariable'] = self.pressure_sensor_val    
        self.pressure_sensor_val.set('888.8')

        
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
#        self.frame_light = Frame(self.frame_left_bottom, bg='orange')
#        self.frame_light.pack(side='right', anchor='se') # Light buttons frame.pack()
        self.frame_light = Frame(self.frame_right, bg='orange')
        self.frame_light.pack(side='top', anchor='nw', fill='x')
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
        
        self.light1_button.config(state='disabled')
        self.light2_button.config(state='disabled')
        self.light3_button.config(state='disabled')
        self.light4_button.config(state='disabled')


    def on_light1(self):
        if self.light1_button.config('relief')[-1] == 'sunken':
            self.put_command_for_asyncio_loop_to_queue('Light1 OFF', self.mainframe)
        else:
            self.put_command_for_asyncio_loop_to_queue('Light1 ON', self.mainframe) 

    def switch_on_light1on(self):
            self.light1_button.config(relief="sunken")
            self.light1_button.config(text="Light1 ON")

    def switch_on_light1off(self):
            self.light1_button.config(relief="raised")
            self.light1_button.config(text="Light1 OFF")


    def on_light2(self):
        if self.light2_button.config('relief')[-1] == 'sunken':
            self.put_command_for_asyncio_loop_to_queue('Light2 OFF', self.mainframe)
        else:
            self.put_command_for_asyncio_loop_to_queue('Light2 ON', self.mainframe)

    def switch_on_light2on(self):
            self.light2_button.config(relief="sunken")
            self.light2_button.config(text="Light2 ON")

    def switch_on_light2off(self):
            self.light2_button.config(relief="raised")
            self.light2_button.config(text="Light2 OFF")


    def on_light3(self):
        if self.light3_button.config('relief')[-1] == 'sunken':
            self.put_command_for_asyncio_loop_to_queue('Light3 OFF', self.mainframe)
        else:
            self.put_command_for_asyncio_loop_to_queue('Light3 ON', self.mainframe)

    def switch_on_light3on(self):
            self.light3_button.config(relief="sunken")
            self.light3_button.config(text="Light3 ON")

    def switch_on_light3off(self):
            self.light3_button.config(relief="raised")
            self.light3_button.config(text="Light3 OFF")


    def on_light4(self):
        if self.light4_button.config('relief')[-1] == 'sunken':
            self.put_command_for_asyncio_loop_to_queue('Light4 OFF', self.mainframe)
        else:
            self.put_command_for_asyncio_loop_to_queue('Light4 ON', self.mainframe) 

    def switch_on_light4on(self):
            self.light4_button.config(relief="sunken")
            self.light4_button.config(text="Light4 ON")

    def switch_on_light4off(self):
            self.light4_button.config(relief="raised")
            self.light4_button.config(text="Light4 OFF")


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

    # Handle Enter key press
    def on_modbus_command_enter_pressed(self, event):
        # Send a command to the modbus async client
        data = self.modbus_command_entry.get().strip()
        #message = bytearray.fromhex(data)        
        #asyncio.run(self.modbus_wrapper.send_modbus_command(message), debug=True)
        timed_msg('Function not implemented. Message: "' + data + '"')
        
        return 'break'

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

    # Handle closing the window
    def on_close_window(self):
        #if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.tk_root.destroy()
        
        # Print timestamped messsage    
def timed_msg(msg: str):
    print(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3], msg)
