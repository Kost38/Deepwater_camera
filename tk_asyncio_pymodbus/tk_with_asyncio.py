#!/usr/bin/python3

import asyncio # Lib for asynchronous programming
import threading # Lib for multithreaded programming 
import queue # Multithreaded queue

import tkinter # Tkinter lib for graphical interface
from tkinter import Frame # Frame - Tk themed widget set


from window_with_buttons import GUI # Class of the GUI window - form with buttons

from datetime import datetime,timedelta
import time
import sys


# Global reference to loop allows access from different environments.
asyncio_running_loop: asyncio.AbstractEventLoop = None

#----------
# A multi-producer, multi-consumer queues for multithreaded programming 
# which implements internally all the required locking semantics
# FIFO

# Queue of data to be used to create tasks for handling in asyncio service loop
queue_of_labels_for_asyncio: queue.Queue = queue.Queue()
# Queue of tasks for handling in asyncio service loop
queue_of_commands_for_asyncio: queue.Queue = queue.Queue()
# Queue of tasks for handling by Tkinter service loop
queue_of_tasks_for_tk: queue.Queue = queue.Queue()

#----------
# Time constants:

# Initial sleep time between iterations in Tk service loop
tk_sleep_time = 10#10 # Here time is in milliseconds: equal to 0.01 s

# Initial sleep time between iterations in Asyncio service loop
asyncio_sleep_time = 0.01 #0.01 # sec

# Delay after handling a command and task by the pair of queues (Tkinter + Asyncio)
min_time_between_commands =  0.1#0.1 # sec

# Time to wait before starting a next sequence of polling sensors
delay_after_chain_of_commands = 0.2#0.2 # sec

# Timeout of connection and sending packets for Async Modbus Client
modbus_timeout = 0.2




#----------
# Host address:

# Pressure sensor
#host_ip = "10.0.10.167" # current
#port_addr = "4001"
#host_ip = "192.168.1.67" # old

# Compass
#host_ip = "84.237.21.184" # old, external
#port_addr = "4001"

# Localhost
host_ip = "127.0.0.1"
port_addr = 10319


#----------
# To store the time when the command for asyncio is started
command_start_time = datetime.now()

min_timedelta_between_commands = timedelta(seconds = min_time_between_commands)
zero_timedelta = timedelta(microseconds = 0)


def check_asyncio_event_loop_is_found():
	while not asyncio_running_loop:
		time.sleep(asyncio_sleep_time)
		timed_msg('Checking in Main Thread that Asyncio running loop is got...')


def get_from_queue(queue_of_tasks: queue.Queue):
	try:
		# Get an element from the queue if possible (don't use the thread-blocking 'get' method)
		task = queue_of_tasks.get_nowait()
	except queue.Empty:
		return None
	else:
		return task


# Put a task to the queue
def put_to_queue_from_tk(task, queue_of_tasks, mainframe): #, mainframe: Frame):
	try:
		# Put a task to the tk queue if possible (don't use the thread-blocking 'put' method of queue)
		queue_of_tasks.put_nowait(task)
	except queue.Full:
		# Try to put next time
		mainframe.after(poll_interval, lambda: put_to_queue(task, queue_of_tasks, mainframe))
	else: 
		# The task was put to the queue
		#timed_msg('Task "' + task + '" was put to queue')
		pass
		
		
def put_label_to_queue_for_asyncio(label, mainframe):
	put_to_queue_from_tk(label, queue_of_labels_for_asyncio, mainframe)



# Tkinter service loop (It runs in the Main Thread)
def tk_service_loop(mainframe: Frame, gui):
	# Poll continuously while queue has work to process.
	poll_interval =  tk_sleep_time	
	#timed_msg('-TK: next call start with poll interval "' + str(poll_interval) + '"') 

	# Get a task from the queue of tasks for Tkinter if possible (don't use the thread-blocking 'get' method)
	task_for_tk = get_from_queue(queue_of_tasks_for_tk)
	
	if (task_for_tk):
		# Handle a task in Tkinter
		reply_from_tk = gui.handle_task_in_tk(task_for_tk)
		timed_msg('-TK: Task "' + task_for_tk[0] + '" handled with next Asyncio command "' + str(reply_from_tk if reply_from_tk else 'None') + '"')
		
		# Schedule a command label for asyncio if needed
		if (reply_from_tk):
			put_to_queue_from_tk(reply_from_tk, queue_of_labels_for_asyncio, mainframe)

			# Wait some more time after putting a new label for Command for Asyncio to queue
			#poll_interval = int(min_time_between_commands * 1000)

	#timed_msg('-TK: before next call with poll interval"' + str(poll_interval) + '"') 
	# Schedule a call of this function again in the tkinter event loop after the poll interval.
	mainframe.after(poll_interval, lambda: tk_service_loop(mainframe, gui))


# Asyncio service loop (This runs in the special thread)
async def asyncio_service_loop(gui, aio_loop_shutdown_initiated: threading.Event):

	# Communicate the asyncio running loop status to tkinter via a global variable
	global asyncio_running_loop
	asyncio_running_loop = asyncio.get_running_loop()
	timed_msg('In a special thread: Got asyncio running loop: ' + str(asyncio_running_loop))
	timed_msg('In a special thread: Start iterations to keep asyncio event loop running...')
	
	asyncio_loop_wait_period = asyncio_sleep_time
	
	asyncio_is_busy = False
	label_for_asyncio = None
	labeled_command_for_asyncio = None
	
	while not aio_loop_shutdown_initiated.is_set():
		#timed_msg('AIO_3: Next call after "' + str(asyncio_loop_wait_period) + '"')
		
		asyncio_loop_wait_period = asyncio_sleep_time # Here time is in seconds

		#timed_msg('AIO_0: labels' + str(list(queue_of_labels_for_asyncio.queue)))
		#timed_msg('AIO_0: comands' + str([item[0] for item in list(queue_of_commands_for_asyncio.queue)]))

		# Get a command for asyncio from the queue
		if (not labeled_command_for_asyncio):
			labeled_command_for_asyncio = get_from_queue(queue_of_commands_for_asyncio)
		
		if (labeled_command_for_asyncio):
			#timed_msg('AIO_1: got command "' + labeled_command_for_asyncio[0] + '" from asyncio queue')
			if labeled_command_for_asyncio[1].done():
				try:
					#timed_msg('AIO_1: Command "' + labeled_command_for_asyncio[0] + '" is done. Try to get the result of it.')
					# When the command for asyncio as a future is done, save the result of it in a task for tk
					task_for_tk = labeled_command_for_asyncio[1].result()
				except Exception as exc:
					timed_msg('AIO_1: Exception ' + exc.args[0] +' while waiting result of command "' + labeled_command_for_asyncio[0] + '"')
					timed_msg(labeled_command_for_asyncio[1].exception().args[0])
				else:
					# Put the task for tk  to the queue (don't use the thread-blocking 'put' method)
					queue_of_tasks_for_tk.put(task_for_tk)
					timed_msg('AIO_1: Command "' + labeled_command_for_asyncio[0] + '" is done. Put task "' + task_for_tk[0] + '" to TK queue. ')
				
				# Calculate command duration to use in sleep
				command_duration = datetime.now() - command_start_time
				#print('command_duration', command_duration)
				
				if (command_duration < min_timedelta_between_commands):
					rest_time = min_timedelta_between_commands - command_duration
				else:
					rest_time = zero_timedelta
				
				# Sleep some more time after putting a new task for Tk to queue (to give modbus some time after a command)...
				await asyncio.sleep(rest_time.total_seconds())
				# Clean to go the next iteration
				labeled_command_for_asyncio = None
				asyncio_is_busy = False
		
		# Get a Tkinter command from the queue
		if (not label_for_asyncio):
			label_for_asyncio = get_from_queue(queue_of_labels_for_asyncio)

		if (label_for_asyncio):	
			#timed_msg('AIO_2: got label "' + label_for_asyncio + '"')
			if (not asyncio_is_busy):
				# Create a future task to handle the Tkinter command asyncronously
				command_for_asyncio = asyncio.ensure_future(gui.handle_command_in_asyncio(label_for_asyncio))
				#timed_msg('AIO_2: Try to put command "' + label_for_asyncio + '" to Asyncio queue from Labels queue')
				queue_of_commands_for_asyncio.put([label_for_asyncio, command_for_asyncio])
				timed_msg('AIO_2: Put command "' + label_for_asyncio + '" to Asyncio queue from Labels queue')
				command_start_time = datetime.now()
				label_for_asyncio = None
				asyncio_is_busy = True				

		# (The usual wait command - threading.Event.wait() - would block the current thread and the asyncio loop)
		#timed_msg('AIO_3: before await "' + str(asyncio_loop_wait_period) + '"')
		await asyncio.sleep(asyncio_loop_wait_period)
		#timed_msg('AIO_3: after await "' + str(asyncio_loop_wait_period) + '"')
		
	timed_msg('In a special thread: Asyncio service loop ended.')   

   
# Set up working environments for asyncio and tkinter (This runs in the Main Thread)
def main():	
	# Create Tkinter
	tk_root = tkinter.Tk()
	mainframe = tkinter.Frame(tk_root)
	timed_msg('Tkinter created...' )
	
	# Create GUI interface in Tkinter
	gui = GUI(tk_root, mainframe, put_label_to_queue_for_asyncio, delay_after_chain_of_commands, modbus_timeout, host_ip, port_addr)
	timed_msg('GUI started...' )

	# Schedule the Tkinter service loop
	mainframe.after(0, lambda: tk_service_loop(mainframe, gui))
	timed_msg('Tkinter service loop started in the Main Thread...' )
	
	# Event for signalling between threads (asyncio.Event() is not threadsafe)
	aio_loop_shutdown_initiated = threading.Event()
	
	# Define a function for running the asyncio service loop in a special thread
	def run_in_thread(aio_loop_shutdown_initiated: threading.Event):
		asyncio.run(asyncio_service_loop(gui, aio_loop_shutdown_initiated))
	
	# Start the asyncio event loop in a new thread (the asyncio thread)
	asyncio_loop_thread = threading.Thread(
		target=run_in_thread, 
		args=(aio_loop_shutdown_initiated,), 
		name="Asyncio's Thread")
	asyncio_loop_thread.start()
	timed_msg("A special thread for Asyncio service loop is started...")
	
	# The asyncio event loop must start before the tkinter main loop.
	check_asyncio_event_loop_is_found()
		
	timed_msg('Loop Tkinter main loop forever...' )   
	tk_root.mainloop()
	timed_msg('Tkinter main loop is finished.' )
	
	aio_loop_shutdown_initiated.set()
	asyncio_loop_thread.join()
	timed_msg("The thread of Asyncio service loop is joined.")

# Print timestamped messsage
def timed_msg(msg: str):
	print(datetime.now().strftime('%H:%M:%S.%f')[:-3], msg)

if __name__ == '__main__':
	# Run main() with possible exception
	sys.exit(main())
 