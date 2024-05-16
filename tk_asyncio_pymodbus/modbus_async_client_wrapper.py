#!/usr/bin/python3
"""Pymodbus asynchronous client for connection to the server with sensors"""
import asyncio # for AsyncModbusTcpClient
import struct
#import helper
#import time
#import datetime
import threading # for multiple proccess 

import pymodbus.client as ModbusClient
from pymodbus import (
    ExceptionResponse,
    ModbusException,
    pymodbus_apply_logging_config,
)

class ModbusAsyncClientWrapper():
    
    # Constructor
    def __init__(self, time_between_transactions, comm, host, port, framer): # comm='tcp', framer='rtu' for sensors
        #self.modbus_transaction_callback = modbus_transaction_callback
        self.comm = comm
        self.host = host
        self.port = port
        self.framer = framer        
        self.async_client = None
        # Available statuses: 'Connected', 'Disconnected'
        self.connection_status = 'Disconnected'
        # Time interval for messaging the server
        self.time_between_transactions = time_between_transactions # sec
        # Turn on logging
        pymodbus_apply_logging_config("DEBUG")
        
        # Resource lock for multithreading
        #self.resource_lock = threading.Lock()
        

    # Setup a client for connection to the server with sensors
    def create_async_client(self):
        print('ModbusAsyncClientWrapper.create_async_client(): ', self.comm, self.host, self.port, self.framer)
        # Create a client
        if self.comm == "tcp": # Communication
            client = ModbusClient.AsyncModbusTcpClient(
                self.host,
                port=self.port,
                framer=self.framer, # ascii,binary,rtu,socket,tls - default depends on comm
                # timeout=10,
                # retries=3,
                # reconnect_delay=1,
                # reconnect_delay_max=10,
                # retry_on_empty=False,
                # TCP setup parameters:
                # source_address=("localhost", 0),
            )
        elif self.comm == "udp":
            client = ModbusClient.AsyncModbusUdpClient(
                self.host,
                port=self.port,
                framer=self.framer,
                # timeout=10,
                # retries=3,
                # retry_on_empty=False,
                # UDP setup parameters:
                # source_address=None,
            )
        elif self.comm == "serial":
            client = ModbusClient.AsyncModbusSerialClient(
                self.port,
                framer=self.framer,
                # timeout=10,
                # retries=3,
                # retry_on_empty=False,
                # Serial setup parameters:
                # strict=True,
                baudrate=9600, # Device baud rate
                bytesize=8,
                parity="N",
                stopbits=1,
                # handle_local_echo=False,
            )
        elif self.comm == "tls":
            client = ModbusClient.AsyncModbusTlsClient(
                self.host,
                port=self.port,
                framer=Framer.TLS,
                # timeout=10,
                # retries=3,
                # retry_on_empty=False,
                # TLS setup parameters:
                # sslctx=sslctx,
                # certfile=helper.get_certificate("crt"), # Import helper module
                # keyfile=helper.get_certificate("key"),  # The same
                # password="none",
                server_hostname="localhost",
            )
        else:
            #logging.warning('Protocol problem: %s', 'connection reset')
            print(f"Unknown client communication protocol {args.comm} selected")
            #print(f"Unknown client {args.comm} selected")
            return

        # pymodbus_apply_logging_config("DEBUG") # Alternative way of logging
        print("### Connection parameters are set up")
        return client    

    # Make a client connection to the server with sensors and start listening them
    async def create_and_connect(self): 
        # Setup a client connection with parameters passed in the constructor
        self.async_client = self.create_async_client()
        # Localhost
        #async_client = create_async_client(comm="tcp", host="127.0.0.1", port=10319, framer=Framer.RTU)
        # Compass
        #async_client = create_async_client(comm="tcp", host="84.237.21.184", port=4001, framer=Framer.RTU)
        # Pressure sensor
        #async_client = create_async_client(comm="tcp", host="192.168.1.67", port=4001, framer=Framer.RTU)
        
        print('async_client: ',  self.async_client)
        # Connect to the server
        try:
            await self.async_client.connect()
        except Exception as exc:
            print(f"Received Exception({exc})")
            self.async_client.close()
            
            self.connection_status = 'Disconnected'            
        else:        
            if (not self.async_client.connected):
                self.async_client.close()
                self.async_client = None
                self.connection_status = 'Disconnected'
            else:                
                print("### Connected to the server with sensors ") 
                self.connection_status = 'Connected'
               
        return ['ConnectCalled']

    # Close the client connection to the server with sensors
    async def close_client(self):
        print('async_client: ', self.async_client)
        if (self.async_client):
            self.async_client.close()
        self.connection_status = 'Disconnected'
        print("### Connection to the server closed" )
        return ['ConnectionClosed']



    async def wait_next_iteration(self):
        loop = asyncio.get_running_loop()    
        cur_time = loop.time()
        next_call_time = cur_time + self.time_between_transactions
        if (cur_time > next_call_time):
            next_call_time = cur_time
        await asyncio.sleep(next_call_time - cur_time)
        return ['WaitedForNexIter']
            
            
    # Start listening asynchronously the pressure sensor PTM RS-485
    async def modbus_transaction(self, slave, function, address, count_val):
        try:
            #print('slave=', slave , ' function=', function, ' address=', address, 'count/val=', count_val)
            
            if (function == 3):
                read_result = await self.async_client.read_holding_registers(address, count_val, slave)
            elif (function == 4):
                read_result = await self.async_client.read_input_registers(address, count_val, slave)
            elif (function == 5):
                read_result = await self.async_client.write_coil(address, count_val, slave)
            elif (function == 6):
                read_result = await self.async_client.write_register(address, value=count_val, slave=slave)

            #print('read_result type: ', type(read_result))
            #print('registers type: ', type(read_result.registers))
            print('registers len: ', len(read_result.registers))
            #print('bits type: ', type(read_result.bits))
            #print('bits len: ', len(read_result.bits))

            for i in range(len(read_result.registers)):
                print('registers [', i, '] = ', read_result.registers[i])
                print('registers i type: ', type(read_result.registers[i]))

            #if (read_result):
                #message = self.async_client.convert_from_registers(read_result.registers, self.async_client.DATATYPE.STRING)          
        
        except ModbusException as exc:
            print(f"Received ModbusException({exc}) from library")
            #self.async_client.close()
            #self.connection_status ='Closed'
            return
        if read_result.isError():
            print(f"Received Modbus library error({read_result})")
            #self.async_client.close()
            return
        if isinstance(read_result, ExceptionResponse):
            print(f"Received Modbus library exception ({read_result})")
            # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
            #self.async_client.close()
            
        return read_result.registers




    async def turn_light1_on(self):
        # Turn Light1 ON
        registers = await self.modbus_transaction(slave = 0xAA, function = 5, address = 0, count_val = True)
        #self.send_message(bytearray.fromhex('AA 05 00 00 FF 00'))
        return ['Light1TurnedON']
        
    async def turn_light1_off(self):
        # Turn Light1 OFF
        registers = await self.modbus_transaction(slave = 0xAA, function = 5, address = 0, count_val = False)
        #self.send_message(bytearray.fromhex('AA 05 00 00 00 00'))
        return ['Light1TurnedOFF']

    async def turn_light2_on(self):
        # Turn Light2 ON
        registers = await self.modbus_transaction(slave = 0xAA, function = 5, address = 1, count_val = True)
        #self.send_message(bytearray.fromhex('AA 05 00 01 FF 00'))
        return ['Light2TurnedON']
        
    async def turn_light2_off(self):
        # Turn Light2 OFF
        registers = await self.modbus_transaction(slave = 0xAA, function = 5, address = 1, count_val = False)
        #self.send_message(bytearray.fromhex('AA 05 00 01 00 00'))
        return ['Light2TurnedOFF']
        
    async def turn_light3_on(self):
        # Turn Light3 ON
        registers = await self.modbus_transaction(slave = 0xBB, function = 5, address = 0, count_val = True)
        #self.send_message(bytearray.fromhex('BB 05 00 00 FF 00'))
        return ['Light3TurnedON']
        
    async def turn_light3_off(self):
        # Turn Light3 OFF
        registers = await self.modbus_transaction(slave = 0xBB, function = 5, address = 0, count_val = False)
        #self.send_message(bytearray.fromhex('BB 05 00 00 00 00'))
        return ['Light3TurnedOFF']

    async def turn_light4_on(self):
        # Turn Light4 ON
        registers = await self.modbus_transaction(slave = 0xBB, function = 5, address = 1, count_val = True)
        #self.send_message(bytearray.fromhex('BB 05 00 01 FF 00'))
        return ['Light4TurnedON']
        
    async def turn_light4_off(self):
        # Turn Light4 OFF
        registers = await self.modbus_transaction(slave = 0xBB, function = 5, address = 1, count_val = False)
        #self.send_message(bytearray.fromhex('BB 05 00 01 00 00'))
        return ['Light4TurnedOFF']

        

    async def prepare_pressure_sensor(self): 
        print("### Start listening the pressure sensor PTM RS-485" )
        # Read serial number
        registers = await self.modbus_transaction(slave = 0xF0, function = 4, address = 7, count_val = 1)        
        return ['PressureTransactionCommited', registers[0]]

    async def transact_pressure_sensor(self):
        # Read pressure and temperature from registers
        registers = await self.modbus_transaction(slave = 0xF0, function = 4, address = 0, count_val = 2)
        # Convert to meters by multipliyng on 0.16315456
        return ['PressureTransactionCommited', convert_uint(registers[0]) * 0.16315456]


    async def start_calibrating_compass(self):
        # Write  CalStatus = 1 (to start calibrating)
        registers = await self.modbus_transaction(slave = 0x0A, function = 6, address = 0, count_val = 1)
        return ['CalibratingCompassStarted']
        
    async def stop_calibrating_compass(self):                
        # Write  CalStatus = 3 (to stop calibrating)
        registers = await  self.modbus_transaction(slave = 0x0A, function = 6, address = 0, count_val = 3)
        return ['CalibratingCompassStoped']

    async def correct_compass_north(self):
        # Write  CalStatus = 5 (current direction will be set as north)
        registers = await self.modbus_transaction(slave = 0x0A, function = 6, address = 0, count_val = 5)
        return ['CompassNorthCorrected']
        
    async def save_compass_configuration(self):                
        # Write  CalStatus = 6 (to save north configuration)
        registers = await self.modbus_transaction(slave = 0x0A, function = 6, address = 0, count_val = 6)
        return ['CompassConfigurationSaved']

    async def reset_compass(self):
        # Write  CalStatus = 7 (to reset compass) 
        registers = await self.modbus_transaction(slave = 0x0A, function = 6, address = 0, count_val = 7)
        return ['CompassResetCommited']
        
    async def read_cal_status_from_compass(self):
        print("### Start listening the compass sensor" )
        # Read CalStatus 
        registers = await self.modbus_transaction(slave = 0x0A, function = 3, address = 0, count_val = 1)
        return ['CompassCalStatusTransactionCommited', registers[0]]
        
    async def read_temperature_from_compass_sensor(self):
        # Read Tempr
        registers = await self.modbus_transaction(slave = 0x0A, function = 3, address = 1, count_val = 1)
        # Temperature should be divided by 8
        return ['CompassTemprTransactionCommited', registers[0]/8]
        
    async def read_pitch_heading_from_compass_sensor(self):
        #Read Pitch (GL_Teta) and Heading (GL_Phi)
        registers = await self.modbus_transaction(slave = 0x0A, function = 3, address = 2, count_val = 4)

        # Pack two integers in standard 
        # '>HH' big-endian, 2-byte integer, 2-byte integer
        floatPitch_bytes = struct.pack('>HH', registers[1], registers[0])
        # '>f' big-endian, 2-byte integer, 2-byte integer
        floatPitch = struct.unpack('>f', floatPitch_bytes)[0]
                
   
        floatHeading_bytes = struct.pack('>HH', registers[3], registers[2])
        floatHeading = struct.unpack('>f', floatHeading_bytes)[0]
        
        return ['CompassPitchHeadingTransactionCommited', floatPitch, floatHeading]
        
        
def convert_uint(x):
    if x >= 0x7FFF:
        x -= 0xFFFF
    return x