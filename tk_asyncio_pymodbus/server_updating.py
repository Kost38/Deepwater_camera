#!/usr/bin/python3
"""Pymodbus asynchronous Server with updating task Example.

An example of an asynchronous server and
a task that runs continuously alongside the server and updates values.

usage::

	server_updating.py [-h] [--comm {tcp,udp,serial,tls}]
					   [--framer {ascii,binary,rtu,socket,tls}]
					   [--log {critical,error,warning,info,debug}]
					   [--port PORT] [--store {sequential,sparse,factory,none}]
					   [--slaves SLAVES]

	-h, --help
		show this help message and exit
	-c, --comm {tcp,udp,serial,tls}
		set communication, default is tcp
	-f, --framer {ascii,binary,rtu,socket,tls}
		set framer, default depends on --comm
	-l, --log {critical,error,warning,info,debug}
		set log level, default is info
	-p, --port PORT
		set port
		set serial device baud rate
	--store {sequential,sparse,factory,none}
		set datastore type
	--slaves SLAVES
		set number of slaves to respond to

The corresponding client can be started as:
	python3 client_sync.py
"""
import asyncio
import logging
import sys


try:
	import server_async
except ImportError:
	print("*** ERROR --> THIS EXAMPLE needs the example directory, please see \n\
		  https://pymodbus.readthedocs.io/en/latest/source/examples.html\n\
		  for more information.")
	sys.exit(-1)

from pymodbus.datastore import (
	ModbusSequentialDataBlock,
	ModbusSparseDataBlock,
	ModbusServerContext,
	ModbusSlaveContext,
)


_logger = logging.getLogger(__name__)


async def updating_task(serverContext):
	"""Update values in server.

	This task runs continuously beside the server
	It will increment some values each two seconds.

	It should be noted that getValues and setValues are not safe
	against concurrent use.
	"""

	# incrementing loop
	while True:
		await asyncio.sleep(1)
		
		# Pressure sensor (pressure + temperature)
		slave_id = 0xF0
		fc_as_hex = 0x04		
		address = 0x00

		values = serverContext[slave_id].getValues(fc_as_hex, address, count=2)
		values[0] += 1 #/0.16315456
		values[1] += 2
		
		serverContext[slave_id].setValues(fc_as_hex, address, values)		 
		print(f"updating_task: incremented values: {values!s} at address {address!s} at slave {slave_id!s} by func {fc_as_hex!s}")

		# Compass sensor (compass + temperature)
		slave_id = 0x0A
		fc_as_hex = 0x06		
		address = 0x00

		values = serverContext[slave_id].getValues(fc_as_hex, address, count=6)
		values = [v + 1 for v in values]
		
		serverContext[slave_id].setValues(fc_as_hex, address, values)		 
		print(f"updating_task: incremented values: {values!s} at address {address!s} at slave {slave_id!s} by func {fc_as_hex!s}")


def setup_updating_server(cmdline=None):
	"""Run server setup."""
	# The datastores only respond to the addresses that are initialized
	# If you initialize a DataBlock to addresses of 0x00 to 0xFF, a request to
	# 0x100 will respond with an invalid address exception.
	# This is because many devices exhibit this kind of behavior (but not all)

	# Pressure sensor (pressure + temperature)
	pressureSlaveContext = ModbusSlaveContext(ir = ModbusSparseDataBlock({0: [0, 10], 7: [111]}),  zero_mode=True)
	# Compass sensor (compass + temperature)
	compassSlaveContext = ModbusSlaveContext(hr = ModbusSequentialDataBlock(0x00, [0]*6), zero_mode=True)	
	# Light 1 and 2
	light12SlaveContext = ModbusSlaveContext(co = ModbusSequentialDataBlock(0x00, [0]*2), zero_mode=True)
	# Light 3 and 4
	light34SlaveContext = ModbusSlaveContext(co = ModbusSequentialDataBlock(0x00, [0]*2), zero_mode=True)
	
	serverContext = ModbusServerContext(
		slaves={0xF0: pressureSlaveContext, 
				0x0A: compassSlaveContext,
				0xAA: light12SlaveContext,
				0xBB: light34SlaveContext
		}, single=False)
	return server_async.setup_server(
		description="Run asynchronous server.", context=serverContext, cmdline=cmdline
	)


async def run_updating_server(args):
	"""Start updating_task concurrently with the current task."""
	task = asyncio.create_task(updating_task(args.context))
	task.set_name("example updating task")
	await server_async.run_async_server(args)  # start the server
	task.cancel()


async def main(cmdline=None):
	"""Combine setup and run."""
	run_args = setup_updating_server(cmdline=cmdline)
	await run_updating_server(run_args)


if __name__ == "__main__":
	asyncio.run(main(), debug=True)
