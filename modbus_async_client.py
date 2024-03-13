#!/usr/bin/python3
"""Pymodbus asynchronous client for connection to the server with sensors"""
#Tkinter Python Module for GUI
import asyncio
#import helper
import struct
import time
#import datetime
import threading # for multiple proccess 

import pymodbus.client as ModbusClient
from pymodbus import (
    ExceptionResponse,
    Framer,
    ModbusException,
    pymodbus_apply_logging_config,
)
from tkinter import Tk
from client_gui import GUI

connection_status = None

# Setup a client for connection to the server with sensors
def setup_async_client(comm, host, port, framer=Framer.SOCKET):
    # Create a client
    if comm == "tcp": # Communication
        client = ModbusClient.AsyncModbusTcpClient(
            host,
            port=port,            
            framer=framer, # ascii,binary,rtu,socket,tls - default depends on comm
            # timeout=10,
            # retries=3,
            # reconnect_delay=1,
            # reconnect_delay_max=10,
            # retry_on_empty=False,
            # TCP setup parameters:
            # source_address=("localhost", 0),
        )
    elif comm == "udp":
        client = ModbusClient.AsyncModbusUdpClient(
            host,
            port=port,
            framer=framer,
            # timeout=10,
            # retries=3,
            # retry_on_empty=False,
            # UDP setup parameters:
            # source_address=None,
        )
    elif comm == "serial":
        client = ModbusClient.AsyncModbusSerialClient(
            port,
            framer=framer,
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
    elif comm == "tls":
        client = ModbusClient.AsyncModbusTlsClient(
            host,
            port=port,
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
    

# Start listening asynchronously the pressure sensor PTM RS-485
async def modbus_transaction(async_client, slave, function, address, count_val):
    try:    
        if (function == 3):        
            read_result = await async_client.read_holding_registers(address, count_val, slave)
        elif (function == 4):
            read_result = await async_client.read_input_registers(address, count_val, slave)
        elif (function == 6):
            read_result = await async_client.write_register(address, value=count_val, slave=slave)     
            
        #assert len(read_result.registers) == count_val
    
    except ModbusException as exc:
        print(f"Received ModbusException({exc}) from library")
        async_client.close()
        connection_status ='Closed'
        return
    if read_result.isError():
        print(f"Received Modbus library error({read_result})")
        async_client.close()
        return
    if isinstance(read_result, ExceptionResponse):
        print(f"Received Modbus library exception ({read_result})")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        async_client.close()

    #for i in range(count_val):
    #    print(read_result.registers[i])

    return read_result

        
async def read_from_sensor_in_loop(future, async_client, slave, function, address, count_val):
    cur_time = time.time()        
    
    while (connection_status != 'Closed'):
        # print(datetime.datetime.now()) # May be needed       
        next_call_time = cur_time + 1
        
        await modbus_transaction(async_client, slave, function, address, count_val)          
        
        cur_time = time.time()
        if (cur_time > next_call_time):
            next_call_time = cur_time
        time.sleep(next_call_time - cur_time)
        
    future.set_result(cur_time)


# Start listening asynchronously the pressure sensor PTM RS-485
async def run_pressure_sensor(async_client):
    print(f"### Start listening the pressure sensor PTM RS-485" )

    # Read serial number
    registers = await modbus_transaction(
        async_client, slave = 0xF0, function = 4, address = 7, count_val = 1)

    # Get the current event loop.
    loop = asyncio.get_running_loop()
    # Create a new Future object.
    future = loop.create_future()

    # Read pressure and temperature from registers in a loop
    loop.create_task(
        read_from_sensor_in_loop(
            future, async_client, slave = 0xF0, function = 4, address = 0, count_val = 2))

    # Wait until *future* has a result
    await future

# Start listening asynchronously the pressure sensor PTM RS-485
async def run_compass_sensor(async_client):
    print(f"### Start listening the compass sensor" )

    # Read CalStatus
    regres = await modbus_transaction(async_client, slave = 0x0A, function = 3, address = 0, count_val = 1)
    print(regres.registers[0])
    
    # # If standard mode 
    if (regres.registers[0] == 0):
        # # Write  CalStatus = 1 (to start calibrating)
        await modbus_transaction(async_client, slave = 0x0A, function = 6, address = 0, count_val = 1)        

    # # Read CalStatus
    # regres = await modbus_transaction(async_client, slave = 0x0A, function = 3, address = 0, count_val = 1)
    # print(regres.registers[0])        
        
    # If calibration mode
    #if (regres.registers[0] == 2):
        # # Write  CalStatus = 3 (to stop calibrating)
    #    await modbus_transaction(async_client, slave = 0x0A, function = 6, address = 0, count_val = 3)
        
    # Read CalStatus
    regres = await modbus_transaction(async_client, slave = 0x0A, function = 3, address = 0, count_val = 1)
    print(regres.registers[0])    
    
    # Read Tempr
    regres = await modbus_transaction(async_client, slave = 0x0A, function = 3, address = 1, count_val = 1)    
    # Temperature should be deleted by 8
    print(regres.registers[0]/8) 
    
    #Read pitch (GL_Teta) and Heading (GL_Phi)
    regres = await modbus_transaction(async_client, slave = 0x0A, function = 3, address = 2, count_val = 4)    
    print(regres.registers[2:4].hex()) 
    
    first_word = regres.registers[2]
    secnd_word = regres.registers[3]
    
    hi_byte = first_word >> 8
    print(hi_byte)
    
    low_byte = first_word & 0xFF
    print(low_byte)
    
    bytes_of_values = bytes()
    #print(bytes_of_values)
    

    #print(regres.registers[2:4]) 
    
    #print(struct.unpack('f', b'\xdb\x0fI@'))
    #print(struct.unpack('f', bytes(regres.registers[0:2])))


# Make a client connection to the server with sensors and start listening them
async def main(cmdline=None): 
    # Turn on logging
    pymodbus_apply_logging_config("DEBUG")
    
    # Available statuses: 'NotConnected', 'Connected', 'Closed'
    connection_status = 'NotConnected'
    
    # Setup a client connection
    # Localhost
    #async_client = setup_async_client(comm="tcp", host="127.0.0.1", port=10319, framer=Framer.RTU)
    # Compass
    async_client = setup_async_client(comm="tcp", host="84.237.21.184", port=4001, framer=Framer.RTU)
    # Pressure sensor
    #async_client = setup_async_client(comm="tcp", host="192.168.1.67", port=4001, framer=Framer.RTU)
            
    # Connect to the server
    await async_client.connect()
    assert async_client.connected # test client is connected
    print(f"### Connected to the server with sensors ")
    connection_status = 'Connected'
        
    # Listen to sensors
    #await run_pressure_sensor(async_client)
    await run_compass_sensor(async_client)
    #await run_video_camera(async_client)
    
    # Close connection
    async_client.close()
    print(f"### Connection to the server closed" )

if __name__ == "__main__":
    asyncio.run(main(), debug=True)
