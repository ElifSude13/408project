import socket
import threading
import json
import time

DRONE_PORT = 5000
CENTRAL_SERVER_IP = "127.0.0.1"
CENTRAL_SERVER_PORT = 6000

sensor_data_buffer = []

def handle_sensor_connection(conn, addr):
    with conn:
        print(f"[DRONE] Sensor connected from {addr}")
        buffer = b""
        while True:
            try:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    data = json.loads(line.decode())
                    print(f"[DRONE] Received from {addr}: {data}")
                    sensor_data_buffer.append(data)
            except Exception as e:
                print(f"[DRONE] Connection error with {addr}: {e}")
                break

def drone_tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("", DRONE_PORT))
        server_socket.listen()
        print(f"[DRONE] Listening for sensors on port {DRONE_PORT}")
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_sensor_connection, args=(conn, addr), daemon=True).start()

def forward_to_central():
    while True:
        if sensor_data_buffer:
            try:
                with socket.create_connection((CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT)) as central_sock:
                    for data in sensor_data_buffer:
                        central_sock.sendall(json.dumps(data).encode() + b"\n")
                        print(f"[DRONE] Forwarded to Central: {data}")
                    sensor_data_buffer.clear()
            except Exception as e:
                print(f"[DRONE] Could not connect to Central Server: {e}")
        time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=drone_tcp_server, daemon=True).start()
    forward_to_central()
