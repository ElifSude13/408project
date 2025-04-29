**Project:**
**Drone-Enabled Mobile Edge Computing for Environmental Monitoring**

Overview
This project simulates a system where multiple sensor nodes send environmental data (temperature, humidity) to a drone, which performs preliminary processing and forwards the data to a central server for visualization.
This partial prototype demonstrates:

TCP-based communication between components

Real-time data forwarding from sensors to the drone and then to the central server

Basic GUI interfaces for Drone and Central Server

Event logging both to console and log files



**Project Structure**

File	Description
sensor.py	Simulates an environmental sensor sending data to the drone
drone_gui.py	Drone application: receives sensor data, displays it, forwards to the central server
server_gui.py	Central server application: receives processed data and displays it
logs/	Directory for storing log files (sensor.log, drone.log, server.log)

How to Run the System
Open three or more terminals, and follow these steps:

Start the Central Server (Terminal 1):
python server_gui.py

Start the Drone (Terminal 2):
python drone_gui.py

Start Sensor Node(s) (Terminal 3 and more): Example:
python sensor.py --sensor_id sensor1
python sensor.py --sensor_id sensor2

Once started:

Sensor nodes will send data every 2 seconds.
Drone will display received sensor data and forward it every 5 seconds to the Central Server.
Central Server will display the received data.


**TCP Communication Ports**

Component	Port
Drone TCP Server	5000
Central Server TCP Server	6000
All communication happens over localhost (127.0.0.1).


**Logging**

Each component generates a separate log file inside the logs/ folder.

Logs include connection events, data sent/received, and error messages.

Example log files:

logs/sensor1.log
logs/drone.log
logs/server.log


**Notes**

Python Version: Python 3.8+ is recommended.
Dependencies: Only standard libraries (socket, threading, json, tkinter, logging).
Tkinter must be installed (default with Python, but on Linux systems you may need sudo apt install python3-tk).


**Authors:**

Seçil Gezer 29145

Elif Sude Meydan 29184

Sevdenaz Yılmaz 30300
