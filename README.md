# Deepwater_camera

gst-launch-1.0 udpsrc port=5600 caps='application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H265' ! rtpjitterbuffer ! rtph265depay ! avdec_h265 ! glimagesink sync=false

gst-launch-1.0 rtspsrc protocols=tcp location=rtsp://root:12345@10.1.10.80/stream=0 ! application/x-rtp, media=video ! rtpjitterbuffer ! rtph265depay ! avdec_h265 ! glimagesink sync=false
