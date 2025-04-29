import tkinter as tk
from tkinter import ttk
import threading
import socket
import json

CENTRAL_PORT = 6000

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Central Server Dashboard")

        # Data Table
        self.tree = ttk.Treeview(root, columns=("Sensor ID", "Temperature", "Humidity", "Timestamp"), show="headings")
        for col in ("Sensor ID", "Temperature", "Humidity", "Timestamp"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Start TCP Server
        threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(("", CENTRAL_PORT))
            server_socket.listen()
            print(f"[CENTRAL] Listening on port {CENTRAL_PORT}")
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_drone, args=(conn, addr), daemon=True).start()

    def handle_drone(self, conn, addr):
        with conn:
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
                except Exception as e:
                    print(f"[CENTRAL] Connection error: {e}")
                    break

    def update_gui(self, data):
        self.tree.insert("", tk.END, values=(data["sensor_id"], data["temperature"], data["humidity"], data["timestamp"]))

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()
