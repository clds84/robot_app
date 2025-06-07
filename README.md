# Robot Project (Work in Progress)

This robot project is controlled via a client web interface served at `http://hostname.local:8000` using WebSockets. Using a hostname instead of an IP address makes it easy to connect, even through a mobile hotspot, when configuring or troubleshooting WiFi in the field.

For my setup, the robot is paired with a dedicated **mission control** Pi that acts as a robot client app. It sends battery sensor readings (for its own display and Pi) over sockets and opens the robot’s web interface in a browser for control via four rotary encoders and four key switches.

🔗 [Mission Control repo here](https://github.com/clds84/mission_control_app)

> A regular laptop or desktop can also be used as a client if you don’t want to build the mission control hardware.

---

## Features

- WebSocket-based communication between robot and client
- Local web interface (`index.html`) served by the robot
- Integrated camera stream via `stream.py`
- Handles onboard logic for:
  - DC motors (4-wheel drive)
  - Pan/tilt servos for camera
  - NeoPixel LED sticks
- Emits battery sensor readings over sockets
- Receives sensor input (e.g. mission control battery levels) over sockets (if using missoin control client)

---

## Hardware

- Raspberry Pi 4
- Adafruit DC Motor + Servo HAT
- Pi Camera with pan/tilt servo bracket
- 4 DC motors (one per wheel)
- 2 servo motors (for X and Y axis)
- 2 Adafruit NeoPixel sticks
- Adafruit PowerBoost charger (for LiPo battery)
- 2 Adafruit battery gauge monitors
- Adafruit I2C multiplexer
- Small display HAT (for WiFi status and battery voltage)

---

## 3D Printed Parts

Included `.stl` files for:

- Camera housing  
- NeoPixel stick holders  
- Underbody chassis cover (motor protection)  

> **Note:** The underbody was made as a quick solution for mounting and protection. It can be a little tedious to remove/install, but functional.

---

## Getting Started with build

Please refer to the included photos for build guidance. Because chassis types may vary, I didn’t document the mechanical build step-by-step, but the photos will provide some insight. 

**Tips:**

- **Breadboard or loosely wire** all components first to test functionality before permanent mounting.
- Use a **jumper wire kit** and proper standoffs for organization and flexibility.
- You may need a **conical file** to widen mounting holes on the battery gauges or multiplexer to fit standoffs.
- The **display HAT** might seem redundant since battery data is also shown in the web interface, but it’s useful for checking battery level before/after shutdown, or confirming WiFi connection with a button press.
- **Power stacking**: The PowerBoost, battery gauges, and multiplexer stack cleanly using standoffs when aligned properly.

---

## System Overview

```text
[Mission Control Pi] --> [WebSocket] --> [Robot Pi]
       |                                     |
[Encoders + Keys]                    [Motors, Servos]
[Battery Gauges]                     [Camera + Stream]
                                     [NeoPixels, Battery Gauges]

--------------------------OR------------------------------------

[generic client] --> [WebSocket] --> [Robot Pi]
       |                                     |
    [Keys]                           [Motors, Servos]
                                     [Camera + Stream]
                                     [NeoPixels, Battery Gauges]
```

---

## How to Use

Once powered on, the robot Pi automatically runs `the app.py` and `stream.py` web interface at `http://robot-hostname.local:8000` through user services. SSH can be used to troubleshoot and is used to shutdown devices. Termius is a good mobile app for communication if out in the field. 

New environment: first step after boot is to setup wifi. If running headless:
- Make use of wifi script including `nmcli` commands. 
- Use Mobile hotspot for a temporary ssh session to setup the primary wifi in that environment.
- Adjust wifi priority value with `nmcli connection modify (conncetion name) connection.autoconnect-priority: (numnber value)` (**Note:** higher value means higher priorty. This will avoid hiccups if hotspot is still on and has a higher priority than default value of new connection) 

After WiFi setup, the web interface will be properly served and `http://robot-hostname.local:8000` will include the stream from `stream.py` and the battery gauge readings from the robot and mission control (if applicable) broadcasted via WebSockets. The UI is designed for the mission control that includes a 7" display so it might feel bare on a laptop and there's room for upgrading based for a laptop/desktop use case. 

Refer to the controls below in order to use a keyboard layout on a laptop/desktop. 

> **Note:** The mission control uses rotary encoders for all functionality below except for teh ASDW layout that follows a standard QWERTY layout. 

### Physical Controls

#### Motor Movement
- **Key A** – Turn robot left
- **Key S** – Move robot in reverse
- **Key D** – Turn robot right
- **Key W** – move robot forward

##### Camera Movement
- **Key J** – Rotate camera left
- **Key L** – Rotate camera right
- **Key I** – Tilt camera up
- **Key K** – Tilt camera down
- **Key N** – Reset camera to center position.

#### LED Control
- **Key Switch Z** – Toggle LED strip.
- **Key Switch X** - Decrease LED strip brightness
- **Key Switch C** - Increase LED strip brightness

#### Speed Control
- **Key Switch F** – Toggle motor speed range
- **Key Switch G** - Decrease motor speed
- **Key Switch H** - Increase motor speed

### Code

Install dependecies as needed

Logic for interpreting control inputs and sending data is located in `app.py`.

Sensor readings from the Mission Control’s battery gauges are sent to the robot in real-time via WebSocket. There is a conditional statement for an element in `templates/index.html` to avoid crashing in the event you're not using a mission control client:

```
  // Battery reading from mission control
    socket.on('battery_update_mc', (data) => {
        const mcEl = document.getElementById('battery-status-mc')
        if (mcEl) {
            mcEl.innerHTML = data.battery;
            console.log("Got mision control update:", data);
        }
    });
```

Copy `app.service, stream.service, display_stats.service` in `~/.config/systemd/user`, and run `update_service.sh` if changes are ever made in that user services directory. This will keep service files on repo up to date with user services directory. 

Depending on your use case, you may want to adjust the camera resolution (width x height in picam2.configure(...)) and the <img> element dimensions in the HTML (width/height attributes) accordingly.


