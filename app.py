import os
import board
import threading
import logging
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from adafruit_motorkit import MotorKit
from adafruit_servokit import ServoKit
import adafruit_max1704x
import adafruit_tca9548a

# ========== Hardware Initialization ==========

# Shared I2C bus
i2c = board.I2C()

# Initialize multiplexer over I2C
pca = adafruit_tca9548a.TCA9548A(i2c)

# Initialize battery fuel gauges on multiplexer channels 2 and 3
piBat = adafruit_max1704x.MAX17048(pca[3])
servoBat = adafruit_max1704x.MAX17048(pca[2])

# Initialize servo motors on Servo/Motor HAT over I2C
kitServo = ServoKit(channels=16)

# Initial angle values for servos
movement0 = 90
movement1 = 90
kitServo.servo[14].angle = movement0
kitServo.servo[15].angle = movement1

# Initialize DC motors on Servo/Motor HAT (shared I2C bus)
kit = MotorKit(i2c=i2c)
motor3Speed = 1.0
motor4Speed = 1.0
motor_button_pressed = False

motor_lock = threading.Lock()

# Set up logging to file for troubleshooting
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')
print("Log file will be written to:", log_file)

logging.basicConfig(
    filename=log_file, 
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    force=True
)

logger = logging.getLogger(__name__)

logger.info('Current motor speeds: %s, %s', motor3Speed, motor4Speed)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store latest battery data globally
robot_battery_data = {"battery": "<span class='purple'>Waiting for battery data...</span>"}

# Handle client connection
@socketio.on('connect')
def handle_connect():
    print("Client connected:", request.sid)
    emit('battery_update', robot_battery_data)  

# Handle client disconnection
@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected:", request.sid)

# Listen for battery updates broadcasted by Mission Control and relayed via the server
@socketio.on('battery_update_mc')
def handle_battery_update_mc(data):
    print("Received battery_update_mc:", data)
    socketio.emit('battery_update_mc', data, skip_sid=request.sid)

def get_battery_life():
    # Determine text color based on battery percentage
    if piBat.cell_percent > 50:
        pi_font_color = 'neon'
    elif 20 < piBat.cell_percent < 50:
        pi_font_color = 'yellow'
    else:
        pi_font_color = 'red'

    if servoBat.cell_percent > 50:
        servo_font_color = 'neon'
    elif 20 < servoBat.cell_percent < 50:
        servo_font_color = 'yellow'
    else:
        servo_font_color = 'red'

    # Format battery status message as HTML with color-coded values
    return {
        "battery": (
            "<span class='amber'>ROBOT </span>"
            "PI "
            f"<span class='{pi_font_color}'>{piBat.cell_percent:.1f}%</span> / "
            f"<span class='{pi_font_color}'>{piBat.cell_voltage:.2f}V</span> "
            "SERVO "
            f"<span class='{servo_font_color}'>{servoBat.cell_percent:.1f}%</span> / "
            f"<span class='{servo_font_color}'>{servoBat.cell_voltage:.2f}V</span>"
        )
    }

def battery_life_thread():
    global robot_battery_data 
    while True:
        robot_battery_data = get_battery_life()
        socketio.emit('battery_update', robot_battery_data)
        socketio.sleep(1)

socketio.start_background_task(battery_life_thread)

@app.route('/')
def index():
    return render_template('index.html')

# Handle incoming commands to control motors and servos
@socketio.on('command')
def handle_command(command):
    global movement0, movement1, motor3Speed, motor4Speed, motor_button_pressed
    with motor_lock:
        logger.info(f"Received command: {command}")

        # --- Robot Movement Commands ---
        if command == 'forward':
            kit.motor3.throttle = 0.929
            kit.motor4.throttle = -1.0
        elif command == 'reverse':
            kit.motor3.throttle = -motor3Speed
            kit.motor4.throttle = motor4Speed
        elif command == 'left':
            kit.motor3.throttle = -1.0
            kit.motor4.throttle = -1.0
        elif command == 'right':
            kit.motor3.throttle = 1.0
            kit.motor4.throttle = 1.0
        elif command == 'stop':
            kit.motor3.throttle = 0
            kit.motor4.throttle = 0

        # --- Robot Speed Control ---
       
        elif command == 'motorSpeedDefault':
            if motor_button_pressed == False:
                motor_button_pressed = True
                motor3Speed = 1.0
                motor4Speed = 1.0
                # Uncomment to troubleshoot
                # logger.info('Current motor speeds: %s, %s', motor3Speed, motor4Speed)
            elif motor_button_pressed == True:
                motor_button_pressed = False 
                motor3Speed = motor3Speed
                motor4Speed = motor4Speed
                # Uncomment to troubleshoot
                # logger.info('Current motor speeds: %s, %s', motor3Speed, motor4Speed)
        elif command == 'motorSpeedIncrease':
            motor3Speed = min(1.0, motor3Speed + 0.025)
            motor4Speed = min(1.0, motor4Speed + 0.025)
            # Uncomment to troubleshoot
            # logger.info('Current motor speeds: %s, %s', motor3Speed, motor4Speed)
        elif command == 'motorSpeedDecrease':
            motor3Speed = max(.75, motor3Speed - 0.025)
            motor4Speed = max(.75, motor4Speed - 0.025)
            # Uncomment to troubleshoot
            # logger.info('Current motor speeds: %s, %s', motor3Speed, motor4Speed)
        # Servo (camera) commands
        elif command == 'cameraLeft':
            if movement1 < 138:
                movement1 += 8
                kitServo.servo[15].angle = movement1
        elif command == 'cameraRight':
            if movement1 > 30:
                movement1 -= 8
                kitServo.servo[15].angle = movement1
        elif command == 'cameraUp':
            if movement0 > 30:
                movement0 -= 10
                kitServo.servo[14].angle = movement0
        elif command == 'cameraDown':
            if movement0 < 120:
                movement0 += 10
                kitServo.servo[14].angle = movement0
        elif command == 'cameraCenter':
            movement0 = 90
            movement1 = 90
            kitServo.servo[14].angle = movement0
            kitServo.servo[15].angle = movement1

        else:
            logger.warning(f"Unknown command: {command}")

    emit('status', {'status': 'ok', 'command': command})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)
