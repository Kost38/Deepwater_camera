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

class ModbusAsyncClient():
    
    # Constructor
    def __init__(self, modbus_transaction_callback, comm, host, port, framer): # comm='tcp', framer='rtu' for sensors
        self.modbus_transaction_callback = modbus_transaction_callback
        self.comm = comm
        self.host = host
        self.port = port
        self.framer = framer        
        self.async_client = None
        # Available statuses: 'NotConnected', 'Connected', 'Closed'
        self.connection_status = 'NotConnected'
        # Time interval for messaging the server
        self.time_between_transactions = 5 # sec
        # Resource lock for multithreading
        self.resource_lock = threading.Lock()
        

    # Setup a client for connection to the server with sensors
    def setup_async_client(self):
        print(self.comm, self.host, self.port, self.framer)
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
    async def start_client(self): 
        # Turn on logging
        pymodbus_apply_logging_config("DEBUG")
        
        # Available statuses: 'NotConnected', 'Connected', 'Closed'
        self.connection_status = 'NotConnected'
        
        # Setup a client connection
        self.async_client = self.setup_async_client()
        # Localhost
        #async_client = setup_async_client(comm="tcp", host="127.0.0.1", port=10319, framer=Framer.RTU)
        # Compass
        #async_client = setup_async_client(comm="tcp", host="84.237.21.184", port=4001, framer=Framer.RTU)
        # Pressure sensor
        #async_client = setup_async_client(comm="tcp", host="192.168.1.67", port=4001, framer=Framer.RTU)
                
        # Connect to the server
        await self.async_client.connect()
        assert self.async_client.connected # test client is connected
        self.connection_status = 'Connected'
        print("### Connected to the server with sensors ")        
            
        # Listen to sensors
        task1 = asyncio.create_task(self.run_pressure_sensor())
        task2 = asyncio.create_task(self.run_compass_sensor())
        
        await task1        
        await task2
          
        # Close connection
        self.async_client.close()
        print("### Connection to the server closed" )
        
    # Make a client connection to the server with sensors and start listening them
    def stop_client(self):
        self.connection_status = 'Closed'

    # Start listening asynchronously the pressure sensor PTM RS-485
    async def modbus_transaction(self, slave, function, address, count_val):
        try:
            #print('slave=', slave , ' function=', function, ' address=', address, 'count/val=', count_val)
            
            if (function == 3):
                read_result = await self.async_client.read_holding_registers(address, count_val, slave)
            elif (function == 4):
                read_result = await self.async_client.read_input_registers(address, count_val, slave)
            elif (function == 6):
                read_result = await self.async_client.write_register(address, value=count_val, slave=slave) 

            if (read_result):
                message = self.async_client.convert_from_registers(read_result.registers, self.async_client.DATATYPE.STRING)
                self.modbus_transaction_callback(bytes(message, encoding='utf-8'))
        
        except ModbusException as exc:
            print(f"Received ModbusException({exc}) from library")
            self.async_client.close()
            self.connection_status ='Closed'
            return
        if read_result.isError():
            print(f"Received Modbus library error({read_result})")
            self.async_client.close()
            return
        if isinstance(read_result, ExceptionResponse):
            print(f"Received Modbus library exception ({read_result})")
            # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
            self.async_client.close()

        #for i in range(count_val):
        #    print(read_result.registers[i])

        return read_result


    async def read_from_sensor_in_loop(self, slave, function, address, count_val):
        loop = asyncio.get_running_loop()    
        cur_time = loop.time()
        next_call_time = cur_time
        
        while (True):
            with self.resource_lock:
                if (self.connection_status == 'Closed'):
                    break
            next_call_time += self.time_between_transactions
            await self.modbus_transaction(slave, function, address, count_val)
            
            cur_time = loop.time()
            if (cur_time > next_call_time):
                next_call_time = cur_time
            await asyncio.sleep(next_call_time - cur_time)


    # Start listening asynchronously the pressure sensor PTM RS-485
    async def run_pressure_sensor(self):
        print("### Start listening the pressure sensor PTM RS-485" )

        # Read serial number
        #regres = await self.modbus_transaction(slave = 0xF0, function = 4, address = 7, count_val = 1)        

        sec=1
        # Read pressure and temperature from registers
        await self.modbus_transaction(slave = 0xF0, function = 4, address = 0, count_val = 2)

        # Read pressure and temperature from registers in a loop
        await self.read_from_sensor_in_loop(slave = 0xF0, function = 4, address = 0, count_val = 2)


    # Start listening asynchronously the compass
    async def run_compass_sensor(self):
        print("### Start listening the compass sensor" )

        # Read CalStatus
        regres = await self.modbus_transaction(slave = 0x0A, function = 3, address = 0, count_val = 1)
        #print(regres.registers[0])
        
        # # If standard mode 
        #if (regres.registers[0] == 0):
            # # Write  CalStatus = 1 (to start calibrating)
        #await self.modbus_transaction(slave = 0x0A, function = 6, address = 0, count_val = 1)

        # # Read CalStatus
        # regres = await self.modbus_transaction(slave = 0x0A, function = 3, address = 0, count_val = 1)
        #print(regres.registers[0])
            
        # If calibration mode
        #if (regres.registers[0] == 2):
            # # Write  CalStatus = 3 (to stop calibrating)
        #    await self.modbus_transaction(slave = 0x0A, function = 6, address = 0, count_val = 3)
            
        # Read CalStatus
        #regres = await self.modbus_transaction(slave = 0x0A, function = 3, address = 0, count_val = 1)
        #print(regres.registers[0])    
        
        # Read Tempr
        regres = await self.modbus_transaction(slave = 0x0A, function = 3, address = 1, count_val = 1)
        # Temperature should be deleted by 8
        #print(regres.registers[0]/8) 
        
        #Read Pitch (GL_Teta) and Heading (GL_Phi)
        regres = await self.modbus_transaction(slave = 0x0A, function = 3, address = 2, count_val = 4)

        #print(regres.registers[2:4].hex())
        word1 = regres.registers[0]
        word2 = regres.registers[1]
        
        floatPitch_bytes = struct.pack('>HH', word1, word2)
        floatPitch = struct.unpack('>f', floatPitch_bytes)[0]
        #print(floatPitch)
        
        #print(regres.registers[2:4].hex())
        word1 = regres.registers[2]
        word2 = regres.registers[3]
        
        floatHeading_bytes = struct.pack('>HH', word1, word2)
        floatHeading = struct.unpack('>f', floatHeading_bytes)[0]
        #print(floatHeading) 

        #await self.read_from_sensor_in_loop(slave = 0xF0, function = 3, address = 2, count_val = 4)
            
            
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
    async def send_modbus_command(self, message):
        #crc = self.modbusCrc(message)
        #print("0x%04X"%(crc))
        #ba = crc.to_bytes(2, byteorder='little')
        #print("%02X %02X"%(ba[0], ba[1]))
        
        #message.append(ba[0])
        #message.append(ba[1])
        
        #self.modbus_log_text.insert('end', message.decode('utf-8') + '\n')
        #self.modbus_log_text.insert('end', 'send ' + ' '.join(re.findall('..?', message.hex()))+ '\n')
        #self.modbus_log_text.yview('end')
        #self.client_socket.send(message)
        
        slave = message[0]
        function = message[1] 
        address = message[2]
        count_val = message[3] 
        
        print('slave=', slave , ' function=', function, ' address=', address, 'count/val=', count_val)
        
        regres = await self.modbus_transaction(slave, function, address, count_val)
