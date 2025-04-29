import tkinter as tk
from tkinter import ttk
import threading
import socket
import json
import logging
import os

CENTRAL_PORT = 6000

# Log ayarları
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Central Server Dashboard")

        self.tree = ttk.Treeview(root, columns=("Sensor ID", "Temperature", "Humidity", "Timestamp"), show="headings")
        for col in ("Sensor ID", "Temperature", "Humidity", "Timestamp"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)

        threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(("", CENTRAL_PORT))
            server_socket.listen()
            logging.info(f"Central Server listening on port {CENTRAL_PORT}")
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_drone, args=(conn, addr), daemon=True).start()

    def handle_drone(self, conn, addr):
        with conn:
            logging.info(f"Drone connected from {addr}")
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
                        self.root.after(0, self.update_gui, data)
                        logging.info(f"Received data from Drone: {data}")
                except Exception as e:
                    logging.error(f"Connection error with Drone: {e}")
                    break

    def update_gui(self, data):
        self.tree.insert("", tk.END, values=(data["sensor_id"], data["temperature"], data["humidity"], data["timestamp"]))

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()
