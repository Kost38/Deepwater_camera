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

ssh root@10.1.10.80 12345 camera
ssh root@10.0.10.165 router
10.0.10.167:4001 moxa

# tc qdisc fq_codel 0: dev eth0 root refcnt 2 limit 10240p flows 1024 quantum 1514 target 5.0ms interval 100.0ms memory_limit 4Mb ecn
# tc qdisc add dev eth0 root tbf rate 4000kbit peakrate 4020kbit mtu 1400 latency 1000ms buffer 8192
# tc qdisc add dev eth0 root tbf rate 3000kbit peakrate 3020kbit mtu 1400 latency 1000ms buffer 8192



