#!/usr/bin/python3

import io
import logging
from http import server
import socketserver

from threading import Condition
import board
import adafruit_max1704x
import adafruit_tca9548a

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body style="background-color: black">
<img src="/stream.mjpg" width="780" height="460" />
</body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        logging.info(f"Client {self.client_address} requested {self.path}")
        if self.path == '/' or self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.info(f"Streaming client {self.client_address} disconnected: {e}")
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(server.HTTPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (780, 460)}))
    output = StreamingOutput()
    picam2.start_recording(JpegEncoder(), FileOutput(output))

    address = ('0.0.0.0', 8080)
    server = StreamingServer(address, StreamingHandler)
    logging.info("Starting streaming server on http://0.0.0.0:8080")
    try:
        server.serve_forever()
    finally:
        picam2.stop_recording()
