import socket
import threading
import json
import time

# Port for receiving data from sensors
DRONE_PORT = 5000

# Central server address and port
CENTRAL_SERVER_IP = "127.0.0.1"
CENTRAL_SERVER_PORT = 6000

# Buffer to temporarily store incoming sensor data
sensor_data_buffer = []

# Handle incoming connection from a single sensor node
def handle_sensor_connection(conn, addr):
    with conn:
        print(f"[DRONE] Sensor connected from {addr}")
        buffer = b""
        while True:
            try:
                chunk = conn.recv(1024)
                if not chunk:
                    break  # connection closed
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    data = json.loads(line.decode())
                    print(f"[DRONE] Received from {addr}: {data}")
                    sensor_data_buffer.append(data)
            except Exception as e:
                print(f"[DRONE] Connection error with {addr}: {e}")
                break

# Start a TCP server to listen for sensor connections
def drone_tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("", DRONE_PORT))
        server_socket.listen()
        print(f"[DRONE] Listening for sensors on port {DRONE_PORT}")
        while True:
            conn, addr = server_socket.accept()
            # Start a new thread to handle each sensor connection
            threading.Thread(target=handle_sensor_connection, args=(conn, addr), daemon=True).start()

# Periodically forward buffered sensor data to the central server
def forward_to_central():
    while True:
        if sensor_data_buffer:
            try:
                # Establish connection with central server
                with socket.create_connection((CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT)) as central_sock:
                    for data in sensor_data_buffer:
                        # Send each sensor data as JSON over TCP
                        central_sock.sendall(json.dumps(data).encode() + b"\n")
                        print(f"[DRONE] Forwarded to Central: {data}")
                    # Clear the buffer after sending
                    sensor_data_buffer.clear()
            except Exception as e:
                print(f"[DRONE] Could not connect to Central Server: {e}")
        # Wait 5 seconds before next attempt
        time.sleep(5)

# Entry point: start TCP server in a separate thread and begin forwarding loop
if __name__ == "__main__":
    threading.Thread(target=drone_tcp_server, daemon=True).start()
    forward_to_central()
