#!/usr/bin/python3
#import sys, os
from datetime import datetime
import time
#import gi
# gi.require_version('Gst', '1.0')
# gi.require_version('GstVideo', '1.0')
# from gi.repository import Gst
# from gi.repository import GObject, GstVideo

class VideoPlayer():

    def __init__(self, frame_id):
        print('Starting video...')
        self.recording = False
        # For now
        return
        
        Gst.init(None)
        Gst.debug_set_active(True)
        Gst.debug_set_default_threshold(1)

        GObject.threads_init()

        player = Gst.ElementFactory.make('playbin', None)

        #filepath = sys.argv[1]   #os.path.realpath('kbps.mp4')
        #filepath2 = "file:///" + filepath.replace('\\', '/').replace(':', '|')
        #gst-launch-1.0 rtspsrc protocols=tcp location=rtsp://root:12345@192.168.0.123/stream0 ! application/x-rtp, media=video ! rtpjitterbuffer ! rtph264depay ! avdec_h264 ! glimagesink sync=false
        #player.set_property('uri', filepath2 )

        #pipeline = Gst.Pipeline.new("player")
        #pipeline = Gst.parse_launch('rtspsrc protocols=tcp location=rtsp://root:12345@192.168.0.123/stream0 ! application/x-rtp, media=(string)video, encoding-name=(string)H264, payload=(int)96 !rtph264depay ! decodebin ! videoconvert ! appsink name=out_sink')
        #self.pipeline = Gst.parse_launch("rtspsrc protocols=tcp location=rtsp://root:12345@192.168.0.123/stream0 ! application/x-rtp, media=video ! rtpjitterbuffer ! rtph264depay ! h264parse ! mp4mux ! filesink location=" + filename)
        #pipeline = Gst.parse_launch("videotestsrc num-buffers=1000 ! autovideosink")

        # self.pipeline = Gst.parse_launch('rtspsrc protocols=tcp location=rtsp://root:12345@192.168.0.123/stream0 ! application/x-rtp, media=video ! rtpjitterbuffer ! rtph264depay ! tee name=tee ! avdec_h264 ! videocrop left=240 right=240 ! autovideosink')
        # self.pipeline = Gst.parse_launch('rtspsrc protocols=tcp location=rtsp://root:12345@10.1.10.80/stream=0 ! application/x-rtp, media=video ! rtpjitterbuffer ! rtph265depay ! tee name=tee ! avdec_h265 ! videocrop left=240 right=240 ! autovideosink')
        self.pipeline = Gst.parse_launch(
            "udpsrc port=5600 ! application/x-rtp, media=video ! rtpjitterbuffer ! rtph265depay ! tee name=tee ! avdec_h265 ! videocrop left=240 right=240 ! autovideosink")

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::eos', self.on_eos)
        bus.connect('message::error', self.on_error)
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.set_frame_handle, frame_id)
        
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_eos(self, bus, msg):
        print('on_eos(): seeking to start of video')
        self.pipeline.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            0
        )

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())

    def set_frame_handle(self, bus, message, frame_id):
        if not message.get_structure() is None:
            print(message.get_structure().get_name())
            if message.get_structure().get_name() == 'prepare-window-handle':
                display_frame = message.src
                display_frame.set_property('force-aspect-ratio', True)
                display_frame.set_window_handle(frame_id)

    def start_record(self):
        #self.pipeline.send_event(Gst.Event.new_eos())
        print("Start record")
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".mp4"
        print(filename)
        self.recording = True
        
        return
        self.recordpipe = Gst.parse_bin_from_description("queue name=filequeue ! h265parse ! matroskamux ! filesink location=" + filename, True)
        self.pipeline.add(self.recordpipe)
        #self.recordpipe = Gst.parse_launch("queue name=filequeue ! h264parse ! mp4mux ! filesink location=" + filename)
        self.pipeline.get_by_name("tee").link(self.recordpipe)
        self.recordpipe.set_state(Gst.State.PLAYING)
        
    def stop_record(self):
        print("Stop record")
        
        self.recording = False
        return
        #self.filequeue = self.recordpipe.get_by_name("filequeue")
        #self.filequeue.get_static_pad("src").add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, self.probe_block)
        self.pipeline.get_by_name("tee").unlink(self.recordpipe)
        #self.filequeue.get_static_pad("sink").send_event(Gst.Event.new_eos())
        self.recordpipe.send_event(Gst.Event.new_eos())

    def probe_block(self, pad, buf):
        print("Blocked")
        return True
        
    def __del__(self):
        if (self.recording):
            self.stop_record()
        print("Closing video...")
