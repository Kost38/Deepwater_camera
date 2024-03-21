import asyncio
import concurrent.futures
import queue
import sys
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from typing import Optional
from window_with_buttons import GUI

# Global reference to loop allows access from different environments.
aio_running_loop: Optional[asyncio.AbstractEventLoop] = None

#asyncio_blocker_callback = None

 

# Asynchronously block the thread and put a work package into Tkinter's work queue.
async def asyncio_blocker(tk_queue: queue.Queue, gui) -> None:
    """ 
    This is a producer for Tkinter's work queue. It will run in the same thread as the asyncio loop.     
    Args:
        task_id: Sequentially issued tkinter task number.
        tk_queue: tkinter's work queue.
        block: block time
    Returns:
        Nothing. The work package is returned via the threadsafe tk_queue.
    """
    
    # The statement 'await asyncio.sleep(block)' can be replaced with any awaitable blocking code.
    #await asyncio.sleep(0.1)

    # Exceptions for testing handlers. Uncomment these to see what happens when exceptions are raised.
    # raise IOError('Just testing an expected error.')
    # raise ValueError('Just testing an unexpected error.')
    
    await gui.wait_async_modbus()
    work_package = 'Asynchronous World.'
    
    #global asyncio_blocker_callback
    #work_package = await asyncio_blocker_callback()
    
    
    # Put the work package into the tkinter's work queue.
    while True:
        try:
            # Put a work package to the queue (but don't wait). Asyncio can't wait for the thread-blocking 'put' method
            tk_queue.put_nowait(work_package)            
        except queue.Full:
            # Give control back to asyncio's loop.
            await asyncio.sleep(0)            
        else:
            # The work package has been placed in the queue so we're done.
            break

# Exception handler for future coroutine callbacks (It runs in the Main Thread.)
def asyncio_exception_handler(mainframe: ttk.Frame, asyncio_blocker_future: concurrent.futures.Future, first_call: bool = True) -> None:
    """ 
    This non-coroutine function uses tkinter's event loop to wait for the future to finish.
    Args:
        mainframe: The after method of this object is used to poll this function.
        future: The future running the future coroutine callback.
        first_call: The first call if true.
    """
    poll_interval = 100  # milliseconds
    
    try:
        # Python will not raise exceptions during future execution until `future.result` is called.
        # A zero timeout is required to avoid blocking the thread.
        asyncio_blocker_future.result(0)
        print(asyncio_blocker_future)
    # If the future hasn't completed, reschedule this function on tkinter's event loop.
    except concurrent.futures.TimeoutError:
        mainframe.after(poll_interval, lambda: asyncio_exception_handler(mainframe, asyncio_blocker_future, first_call=False))
    # Handle an expected error.
    except IOError as exc:
        print(f'asyncio_exception_handler: {exc!r} was handled correctly.')


# Block the thread and put a work package into Tkinter's work queue.
# (It will run in a special thread created solely for running this function. )
def io_blocker(tk_queue: queue.Queue) -> None:
    """This is a producer for Tkinter's work queue.     
    Args:
        task_id: Sequentially issued tkinter task number.
        tk_queue: tkinter's work queue.
        block: block time
    Returns:
        Nothing. The work package is returned via the threadsafe tk_queue.
    """
    
    # The statement 'time.sleep(block)' can be replaced with any non-awaitable blocking code.
    #time.sleep(0.1)

    # Exceptions for testing handlers. Uncomment these to see what happens when exceptions are raised.
    # raise IOError('Just testing an expected error.')
    # raise ValueError('Just testing an unexpected error.')

    work_package = 'Threading World'
    tk_queue.put(work_package)

# Exception handler for non-awaitable blocking callback.
def io_exception_handler(tk_queue: queue.Queue) -> None:
    """ It will run in a special thread created solely for running io_blocker.
    Args:
        tk_queue: tkinter's work queue.
    """
    try:
        io_blocker(tk_queue)
    except IOError as exc:
        print(f'io_exception_handler: {exc!r} was handled correctly.')

#  Start the consumer loop of the work queue. (It runs in the Main Thread. )
def tk_work_queue_consumer_loop(tk_queue: queue.Queue, mainframe: ttk.Frame, gui):
    """ 
    This is the consumer for Tkinter's work queue. 
    After starting, it runs continuously until the GUI is closed by the user.
    """
    # Poll continuously while queue has work to process.
    poll_interval = 0    
    try:
        # Get a work package (but don't wait). Tkinter can't wait for the thread-blocking 'get' method...
        work_package = tk_queue.get_nowait()
    except queue.Empty:
        # ...so be prepared for an empty queue and slow the polling rate.
        poll_interval = 40
    else:
        # Process a work package
        gui.update_modbus_log_callback(work_package)
    finally:
        # Schedule a call of this function again in the tkinter event loop after the poll interval.
        mainframe.after(poll_interval, lambda: tk_work_queue_consumer_loop(tk_queue, mainframe, gui))

# 
# Start the tkinter work queue loop and producers callbacks (This runs in the Main Thread.)
def tk_work_queue_producers(mainframe: ttk.Frame, gui):
    """
    Args:
        mainframe: The mainframe of the GUI used for displaying results from the work queue.       
    """    
    # Create the work queue and start its consumer loop.
    tk_queue = queue.Queue()
    tk_work_queue_consumer_loop(tk_queue, mainframe, gui)



    # Schedule the async blocker (with exception handler).
    # This is a concurrent.futures.Future not an asyncio.Future because it isn't threadsafe.
    # Also, it doesn't have a wait with timeout which we shall need.
    asyncio_blocker_future = asyncio.run_coroutine_threadsafe(asyncio_blocker(tk_queue, gui), aio_running_loop)

    # Can't use Future.add_done_callback here. It doesn't return until the future is done 
    # and that would block tkinter's event loop.
    asyncio_exception_handler(mainframe, asyncio_blocker_future)
    
    
    # futures = []
    # for i in range(3):
        # # Create a new Future object.
        # futures += [loop.create_future()]
        # # Run "set_after()" coroutine in a parallel Task.
        # loop.create_task(set_after(futures[i], 1 - 0.1*i, 'Connect to ' + str(i) + ' clicked at:' + str(1 - 0.1*i)))
        
    # for i in range(3):
        # await futures[i]
        
    # Uncomment if needed
    # Run the sync blocker (with exception handler) in a new thread.
    # io_blocker_thread = threading.Thread(
        # target=io_exception_handler, 
        # args=(tk_queue,),
        # name=f'IO Blocking Thread')
    # io_blocker_thread.start()
    
# Run the asyncio permanent loop service for tkinter (This runs in asyncio thread)
async def asyncio_loop_service(aio_loop_shutdown_initiated: threading.Event):
    """ 
    This provides an always available service for tkinter to make any number 
    of simultaneous blocking IO calls. 'Any number' includes zero.
    """   
    # Communicate the asyncio running loop status to tkinter via a global variable
    global aio_running_loop
    aio_running_loop = asyncio.get_running_loop()
    
    # If there are no awaitables left in the work queue asyncio will close.
    # The usual wait command - Event.wait() - would block the current thread and the asyncio loop
    while not aio_loop_shutdown_initiated.is_set():
        await asyncio.sleep(0)
        
    print('Asyncio loop service Exit...')

#  Create tkinter, work queue and run tkinter event loop (This runs in the Main Thread)
def tk_main_loop():
    # Create the Tk root and mainframe.
    tk_root = tk.Tk()
    mainframe = ttk.Frame(tk_root)
    
    #global asyncio_blocker_callback
    gui=GUI(tk_root, mainframe)  
    
    print('GUI started...' )
    # Schedule the tkinter work queue loop and producers callbacks in the tkinter event loop
    mainframe.after(0, lambda: tk_work_queue_producers(mainframe, gui))
    print('Tkinter work queue loop started...' )
    
    # The asyncio permanent loop must start before the tkinter event loop.
    while not aio_running_loop:
        time.sleep(0)
    
    print('Time to start Tkinter main loop...' )        
    # Start the tkinter event loop
    tk_root.mainloop()
    print('Tkinter main loop started (now after mainloop)...' )
    
# Set up working environments for asyncio and tkinter (This runs in the Main Thread)
def main():    
    # Event for signalling between threads (asyncio.Event() is not threadsafe)
    aio_loop_shutdown_initiated = threading.Event()
    
    def run_asyncio_loop_service(aio_loop_shutdown_initiated: threading.Event):
        asyncio.run(asyncio_loop_service(aio_loop_shutdown_initiated))
    
    # Start the permanent asyncio loop in a new thread
    aio_loop_service_thread = threading.Thread(
        target=run_asyncio_loop_service, 
        args=(aio_loop_shutdown_initiated,), 
        name="Asyncio's Thread")        
    aio_loop_service_thread.start()
    
    # Run tkinter event loop
    tk_main_loop()
    
    print('Tkinter Exit...')
    
    # Close the asyncio permanent loop and join the thread in which it runs
    aio_loop_shutdown_initiated.set()
    aio_loop_service_thread.join()    

if __name__ == '__main__':
    # Run main() with possible exception
    sys.exit(main())
 
