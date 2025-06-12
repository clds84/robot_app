import board
import neopixel
import logging
import signal
import sys
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)

# Set up logging to file for troubleshooting
logging.basicConfig(filename='app.log', level=logging.INFO)
logger = logging.getLogger(__name__)
# socketio = SocketIO(app)
socketio = SocketIO(app, cors_allowed_origins=["http://headless4.local:8000", "http://headless4.local:9000"])

# Setup for pixels1 (LED above camera)
pixel1_pin = board.D21
num_pixels1 = 8
pixel1_order = neopixel.GRBW
brightness = 1.0

# Setup for pixels2 (LED below camera)
pixel2_pin = board.D12
num_pixels2 = 8
pixel2_order = neopixel.GRBW
brightness = 1.0

# Initialize NeoPixel
pixels1 = neopixel.NeoPixel(pixel1_pin, num_pixels1, brightness=brightness, pixel_order=pixel1_order)
pixels2 = neopixel.NeoPixel(pixel2_pin, num_pixels2, brightness=brightness, pixel_order=pixel2_order)

leds_on = False
led_button_state = False

# Listen for battery updates broadcasted by Mission Control and relayed via the server
@socketio.on('led_encoder_button_state')
def handle_led_button_state(data):
    global led_button_state
    print("Received led_button_state:", data)
    # led_button_state = data
    led_button_state = str(data).strip() == 'True'
    print(f"{time.time():.2f} - led_button_state updated: {led_button_state}")



@socketio.on('command')
def handle_command(command):
    global pixels1, pixels2,leds_on, brightness, led_button_state
    print(f"{time.time():.2f} - command received: {command}, led_button_state={led_button_state}")
    if command == 'led_toggle_on_off':
        if leds_on == False and led_button_state == False:
            brightness = 1.0
            pixels1.deinit()
            pixels2.deinit()
            pixels1 = neopixel.NeoPixel(pixel1_pin, num_pixels1, brightness=brightness, pixel_order=pixel1_order)
            pixels2 = neopixel.NeoPixel(pixel2_pin, num_pixels2, brightness=brightness, pixel_order=pixel2_order)
            pixels1.fill((255,255,255))
            pixels2.fill((255,255,255))
            leds_on = True
            logger.info('Current pixel1/2 brightness: %s, %s', pixels1.brightness, pixels2.brightness)
        elif leds_on == True and led_button_state == True:
            brightness = 0.0
            pixels1.deinit()
            pixels2.deinit()
            pixels1 = neopixel.NeoPixel(pixel1_pin, num_pixels1, brightness=brightness, pixel_order=pixel1_order)
            pixels2 = neopixel.NeoPixel(pixel2_pin, num_pixels2, brightness=brightness, pixel_order=pixel2_order)
            pixels1.fill((0, 0, 0, 0))  
            pixels2.fill((0, 0, 0, 0))  
            leds_on = False
            logger.info('Current pixel1/2 brightness: %s, %s', pixels1.brightness, pixels2.brightness)
    elif command == 'led_brightness_increase' and leds_on == True:
        brightness = min(1.0, brightness + 0.1)
        pixels1.deinit()
        pixels2.deinit()
        pixels1 = neopixel.NeoPixel(pixel1_pin, num_pixels1, brightness=brightness, pixel_order=pixel1_order)
        pixels2 = neopixel.NeoPixel(pixel2_pin, num_pixels2, brightness=brightness, pixel_order=pixel2_order)
        pixels1.fill((255,255,255))
        pixels2.fill((255,255,255))
        logger.info('Current pixel1/2 brightness: %s, %s', pixels1.brightness, pixels2.brightness)
    elif command == 'led_brightness_decrease' and leds_on == True:
        brightness = max(0.1, brightness - 0.1)
        pixels1.deinit()
        pixels2.deinit()
        pixels1 = neopixel.NeoPixel(pixel1_pin, num_pixels1, brightness=brightness, pixel_order=pixel1_order)
        pixels2 = neopixel.NeoPixel(pixel2_pin, num_pixels2, brightness=brightness, pixel_order=pixel2_order)
        pixels1.fill((255,255,255))
        pixels2.fill((255,255,255))
        logger.info('Current pixel1/2 brightness: %s, %s', pixels1.brightness, pixels2.brightness)

def cleanup_and_exit(signum=None, frame=None):
    print("Turning off LEDs...")
    pixels1.fill((0, 0, 0, 0))
    pixels2.fill((0, 0, 0, 0))
    pixels1.deinit()
    pixels2.deinit()
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup_and_exit)
signal.signal(signal.SIGINT, cleanup_and_exit)

if __name__ == '__main__':
    try:
        socketio.run(app, host='0.0.0.0', port=9000)
    finally:
        cleanup_and_exit()