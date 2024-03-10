#!/usr/bin/python3

#import tkinter as tk
from tkinter import Tk, Frame, Scrollbar, Label, END, Entry, Text, VERTICAL, Button, messagebox

class GUI:

    def __init__(self, master):
        self.toggle_btn = Button(text="Toggle", width=12, relief="raised", command=self.toggle)
        self.toggle_btn.pack(pady=5)


    def toggle(self):

        if self.toggle_btn.config('relief')[-1] == 'sunken':
            self.toggle_btn.config(relief="raised")
        else:
            self.toggle_btn.config(relief="sunken")

    def on_close_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()
            #self.client_socket.close()
            exit(0)



#root = tk.Tk()
#toggle_btn = tk.Button(text="Toggle", width=12, relief="raised", command=toggle)
#toggle_btn.pack(pady=5)
#root.mainloop()

root = Tk()
gui = GUI(root)
root.protocol("WM_DELETE_WINDOW", gui.on_close_window)
root.mainloop()



