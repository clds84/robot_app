import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import board
from adafruit_motorkit import MotorKit
from adafruit_servokit import ServoKit
import logging

logging.basicConfig(filename='app.log', level=logging.INFO)
logger = logging.getLogger(__name__)

motor_lock = threading.Lock()

kitServo = ServoKit(channels=16)
movement0 = 90
movement1 = 90
kitServo.servo[14].angle = movement0
kitServo.servo[15].angle = movement1
kit = MotorKit(i2c=board.I2C())

motor3Speed = 1.0
motor4Speed = 1.0

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('command')
def handle_command(command):
    global movement0, movement1, motor3Speed, motor4Speed
    with motor_lock:
        logger.info(f"Received command: {command}")

        # Movement commands
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

        # Motor speed commands
        elif command.startswith('motorSpeed'):
            try:
                speed_val = int(command.replace('motorSpeed', '')) / 100
                motor3Speed = speed_val
                motor4Speed = speed_val
                logger.info(f"Set motor speeds to {speed_val}")
            except ValueError:
                logger.warning(f"Invalid motor speed command: {command}")

        # Servo (camera) commands
        elif command == 'cameraLeft':
            if movement1 < 138:
                movement1 += 24
                kitServo.servo[15].angle = movement1
        elif command == 'cameraRight':
            if movement1 > 30:
                movement1 -= 24
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
