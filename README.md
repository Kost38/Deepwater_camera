# Deepwater_camera

gst-launch-1.0 udpsrc port=5600 caps='application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H265' ! rtpjitterbuffer ! rtph265depay ! avdec_h265 ! glimagesink sync=false

gst-launch-1.0 rtspsrc protocols=tcp location=rtsp://root:12345@10.1.10.80/stream=0 ! application/x-rtp, media=video ! rtpjitterbuffer ! rtph265depay ! avdec_h265 ! glimagesink sync=false

Relay board modbus
http://www.chinalctech.com/m/view.php?aid=455

Pressure sensor modbus
https://www.stssensors.com/wp-content/uploads/2020/11/PTM-Modbus-communication-example.pdf

For having Modbus library in Python run:
pip install pymodbus

Modbus adress table:

| adr  | dev             |
|------|-----------------|
| 0xF0 | Pressure sensor |
| 0xAA | Relay board 1   |
| 0xBB | Relay board 2   |


![1.7mm](/cam/1.7mm.png)
![2.5mm](/cam/2.5mm.png)
![5mm](/cam/5mm.png)
