# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Modified by clds84, 2025

# -*- coding: utf-8 -*-

import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
import adafruit_max1704x
import adafruit_tca9548a
import atexit
import signal
import sys

# Shared I2C bus
i2c = board.I2C()  

# Initialize multiplexer over I2C
pca = adafruit_tca9548a.TCA9548A(i2c)

# Initialize battery fuel gauges on multiplexer channels 2 and 3
piBat = adafruit_max1704x.MAX17048(pca[3])
servoBat = adafruit_max1704x.MAX17048(pca[2])

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Setup button hardware
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input()
buttonB.switch_to_input()
# buttonA.switch_to_input(pull=digitalio.Pull.UP)
# buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 270

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
readings_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 25) 
ssid_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22) 
device_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)  

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
#use False if using buttons, so we start with backlight off
backlight.value = True

def cleanup():
    backlight.value = False

def handle_sigterm(signum, frame):
    cleanup()
    sys.exit(0)

atexit.register(cleanup)
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)  # also handle Ctrl+C gracefully

while True:
    try:
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        # =========================== Shell scripts for system monitoring from here: ============================
        # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load

        # For pressing B
        cmd = "hostname -I | cut -d' ' -f1"
        IP = "IP: " + subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = "hostname"
        Hostname = "Host: " + subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = "iwgetid wlan0 -r"
        SSID = "SSID: " + subprocess.check_output(cmd, shell=True).decode("utf-8")   
        # =======================================================================================================
        
        # for buttonB.value and buttonA.value (display without pressing A or B)
        battery_line_1 = "      Pi       Servo"
        battery_line_2 = f"V:  {piBat.cell_voltage:.2f}v    {servoBat.cell_voltage:.2f}v"    
        battery_line_3 = f"C:  {piBat.cell_percent:.1f}%   {servoBat.cell_percent:.1f}%" 
        battery_line_4 = f"D: {piBat.charge_rate:.1f}%    {servoBat.charge_rate:.1f}%"
        
        if buttonB.value and buttonA.value:
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            y = top
            draw.text((x, y), battery_line_1, font=device_font, fill="#00FF00")
            y += font.getsize(battery_line_1)[1]
            y += 20  
            draw.text((x, y), battery_line_2, font=readings_font, fill="#00FF00")
            y += font.getsize(battery_line_2)[1]
            draw.text((x, y), battery_line_3, font=readings_font, fill="#00FF00")
            y += font.getsize(battery_line_3)[1]
            draw.text((x, y), battery_line_4, font=readings_font, fill="#00FF00")
            y += font.getsize(battery_line_4)[1]
            disp.image(image, rotation)
            time.sleep(0.1)
        if buttonA.value and not buttonB.value: #button A pressed and display toggled on/off
            if backlight.value == True:
                backlight.value = False
                time.sleep(.5)
            elif backlight.value == False:
                backlight.value = True
                time.sleep(.5)
        if buttonB.value and not buttonA.value: #button B pressed and IP/Hostname/SSID toggled on/off
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            y = top
            draw.text((x, y), IP, font=font, fill="#FFFFFF")
            y += font.getsize(IP)[1]
            draw.text((x, y), Hostname, font=font, fill="#FF00FF")
            y += font.getsize(Hostname)[1]
            draw.text((x, y), SSID, font=ssid_font, fill="#FF4051")
            disp.image(image, rotation)
            time.sleep(0.1)
    except KeyboardInterrupt:
        cleanup()
        sys.exit(0)
