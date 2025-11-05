#!/usr/bin/python3
#import sys, os
from datetime import datetime,timedelta
import time
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst
from gi.repository import GObject, GstVideo

class VideoPlayer:

	def __init__(self, frame_id):
		print('Init VideoPlayer...')
		self.recording = False
		Gst.init(None)
		Gst.debug_set_active(True)
		Gst.debug_set_default_threshold(1)

		GObject.threads_init()
		
		self.pipeline = Gst.parse_launch(
			"udpsrc port=5600 ! application/x-rtp, media=video !" 
			"rtpjitterbuffer ! rtph265depay ! tee name=tee ! avdec_h265 !"
			"videocrop left=240 right=240 ! glimagesink") # glimagesink instead of autovideosink

		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.enable_sync_message_emission()
		self.bus.connect('sync-message::element', self.set_frame_handle, frame_id)
		
		self.pipeline.set_state(Gst.State.PLAYING)
		self.recordpipe = None

	def set_frame_handle(self, bus, message, frame_id):
		if not message.get_structure() is None:
			if message.get_structure().get_name() == 'prepare-window-handle':
				display_frame = message.src
				display_frame.set_property('force-aspect-ratio', True)
				display_frame.set_window_handle(frame_id)

	def start_record(self):
		print("Starting record...")
		self.start_record_time = datetime.now()
		
		self.prev_srt_subtitle_time = timedelta(microseconds = 1)
		self.prev_time = datetime.now()
		self.prev_depth = 0
		
		filename = self.start_record_time.strftime("%Y-%m-%d_%H-%M-%S")
		self.log_file = open(filename + ".srt", 'w')
		self.log_counter = 0
		print(filename)
		self.recording = True
		
		self.recordpipe = Gst.parse_bin_from_description("queue name=filequeue ! h265parse ! mp4mux ! filesink location=" + filename + ".mp4", True)
		self.pipeline.add(self.recordpipe)
		self.pipeline.get_by_name("tee").link(self.recordpipe)
		self.recordpipe.set_state(Gst.State.PLAYING)
		
	def write_pressure_to_subtitle_file(self, pressure):
		self.log_counter = self.log_counter + 1
		now_time = datetime.now()
		srt_subtitle_time = now_time - self.start_record_time
		total_microseconds = srt_subtitle_time.total_seconds() * 1000000
		rounded_milliseconds = round(total_microseconds / 1000)
		srt_subtitle_time = timedelta(microseconds=rounded_milliseconds * 1000)
		self.log_file.write(str(self.log_counter) + '\n')
		self.log_file.write(str(self.prev_srt_subtitle_time)[:-3].replace('.' , ',') + ' --> ' + str(srt_subtitle_time)[:-3].replace('.' , ',') + '\n')
		self.log_file.write('T: ' + self.prev_time.strftime("%Y-%m-%d %H:%M:%S") + ' ')
		self.log_file.write('D: ' + str(f"{format(self.prev_depth, '.1f')}") + '\n\n')
		self.log_file.flush()
		self.prev_time = now_time
		self.prev_depth = pressure
		self.prev_srt_subtitle_time = srt_subtitle_time
		
	def stop_record(self):
		print("Stopping record...")
		self.recording = False
		self.log_file.close()
		self.prev_srt_subtitle_time = timedelta(microseconds = 1)
		self.prev_time = datetime.now()
		self.prev_depth = 0
		
		self.pipeline.get_by_name("tee").unlink(self.recordpipe)
		self.recordpipe.send_event(Gst.Event.new_eos())
		
		# Commented out # while self.bus.have_pending():
		time.sleep(0.1)
		
	def stop_video(self):
		if (self.recording):
			self.stop_record()	
  
		print("Cleaning up VideoPlayer...")
		
		self.bus.remove_signal_watch()		
		self.pipeline.set_state(Gst.State.NULL)
		if (self.recordpipe):
			self.recordpipe.set_state(Gst.State.NULL)  

	def __del__(self):
		self.stop_video()
		print("Destructing VideoPlayer...")
