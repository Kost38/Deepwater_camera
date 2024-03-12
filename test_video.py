#!/usr/bin/python3
import sys, os
from tkinter import *
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst
from gi.repository import GObject, GstVideo
Gst.init(None)
Gst.debug_set_active(True)
Gst.debug_set_default_threshold(1)


def set_frame_handle(bus, message, frame_id):
    if not message.get_structure() is None:
        print(message.get_structure().get_name())
        if message.get_structure().get_name() == 'prepare-window-handle':
            display_frame = message.src
            display_frame.set_property('force-aspect-ratio', True)
            display_frame.set_window_handle(frame_id)

window = Tk()
window.title('')
window.geometry('500x400')

GObject.threads_init()


display_frame = Frame(window,bg='#000000')
display_frame.pack(side=TOP,expand=YES,fill=BOTH)
frame_id = display_frame.winfo_id()

player = Gst.ElementFactory.make('playbin', None)

#filepath = sys.argv[1]   #os.path.realpath('kbps.mp4')
#filepath2 = "file:///" + filepath.replace('\\', '/').replace(':', '|')
#gst-launch-1.0 rtspsrc protocols=tcp location=rtsp://root:12345@192.168.0.123/stream0 ! application/x-rtp, media=video ! rtpjitterbuffer ! rtph264depay ! avdec_h264 ! glimagesink sync=false
#player.set_property('uri', filepath2 )

#pipeline = Gst.Pipeline.new("player")
#pipeline = Gst.parse_launch('rtspsrc protocols=tcp location=rtsp://root:12345@192.168.0.123/stream0 ! application/x-rtp, media=(string)video, encoding-name=(string)H264, payload=(int)96 !rtph264depay ! decodebin ! videoconvert ! appsink name=out_sink')
pipeline = Gst.parse_launch('rtspsrc protocols=tcp location=rtsp://root:12345@192.168.0.123/stream0 ! application/x-rtp, media=(string)video, encoding-name=(string)H264, payload=(int)96 !rtph264depay ! decodebin ! videoconvert ! autovideosink')
#pipeline = Gst.parse_launch("videotestsrc num-buffers=1000 ! autovideosink")

bus = pipeline.get_bus()
bus.enable_sync_message_emission()
bus.connect('sync-message::element', set_frame_handle, frame_id)

pipeline.set_state(Gst.State.PLAYING)

window.mainloop()


