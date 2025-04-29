import socket
import threading
import json

CENTRAL_PORT = 6000

def handle_drone_connection(conn, addr):
    with conn:
        print(f"[CENTRAL] Drone connected from {addr}")
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
                    print(f"[CENTRAL] Received: {data}")
            except Exception as e:
                print(f"[CENTRAL] Connection error with {addr}: {e}")
                break

def central_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("", CENTRAL_PORT))
        server_socket.listen()
        print(f"[CENTRAL] Listening on port {CENTRAL_PORT}")
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_drone_connection, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    central_server()
