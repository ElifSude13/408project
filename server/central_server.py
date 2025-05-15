import socket
import threading
import json

CENTRAL_PORT = 6000  # Port number on which the central server listens for drone connections

def handle_drone_connection(conn, addr):
    """
    Handle communication with a connected drone.
    
    Parameters:
    conn (socket.socket): The socket object for the drone connection.
    addr (tuple): The address of the connected drone.
    """
    with conn:
        print(f"[CENTRAL] Drone connected from {addr}")
        buffer = b""  # Buffer to accumulate incoming bytes until a full JSON message is received
        while True:
            try:
                chunk = conn.recv(1024)  # Receive up to 1024 bytes from the drone
                if not chunk:
                    # Connection closed by drone
                    break
                buffer += chunk  # Append received bytes to the buffer
                # Process all complete messages delimited by newline character '\n'
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)  # Extract one message
                    data = json.loads(line.decode())  # Decode JSON message
                    print(f"[CENTRAL] Received: {data}")
            except Exception as e:
                # Handle any errors during receiving or decoding
                print(f"[CENTRAL] Connection error with {addr}: {e}")
                break

def central_server():
    """
    Main server function that listens for incoming drone connections
    and spawns a new thread to handle each connection concurrently.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("", CENTRAL_PORT))  # Bind to all network interfaces on CENTRAL_PORT
        server_socket.listen()  # Start listening for incoming connections
        print(f"[CENTRAL] Listening on port {CENTRAL_PORT}")
        while True:
            conn, addr = server_socket.accept()  # Accept new connection
            # Start a new daemon thread to handle the connected drone independently
            threading.Thread(target=handle_drone_connection, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    central_server()  # Run the central server when the script is executed

