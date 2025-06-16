import tkinter as tk
from tkinter import ttk, messagebox
import threading
import serial
import datetime
import time
from Digitech_Bril_Com import (
    SERIAL_PORT, BAUD_RATE, OUTPUT_FILE, BOARD_ID_BYTE, CMD_TERMINATOR,
    DAC_CHANNELS_ID, format_command, HELP_CMD_MSG
)

class DigiTechGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Digitech Bril Board Control")
        self.ser = None
        self.create_widgets()
        self.connect_serial()

    def create_widgets(self):
        # Command buttons
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        # Command buttons
        cmds = [
            ("Get Status", "getstatus"),
            ("Get Data", "getdata"),
            ("Set Date", "setdate"),
            ("Set Time", "settime"),
            ("Get DateTime", "getdatetime"),
            ("Get DAC Thr", "getdac"),
            ("Get Temp", "gettemp"),
            ("Reset", "reset"),
            ("Get ID", "getid"),
            ("Get Conf", "getconf"),
        ]
        row = 0
        for label, cmd in cmds:
            ttk.Button(frame, text=label, command=lambda c=cmd: self.send_command(c)).grid(row=row, column=0, sticky="ew", pady=2)
            row += 1

        # Set DAC
        ttk.Label(frame, text="Set DAC Thr:").grid(row=row, column=0, sticky="w")
        self.dac_channel = ttk.Combobox(frame, values=list(DAC_CHANNELS_ID.keys()), width=2)
        self.dac_channel.grid(row=row, column=1)
        self.dac_value = ttk.Entry(frame, width=5)
        self.dac_value.grid(row=row, column=2)
        ttk.Button(frame, text="Send", command=self.set_dac).grid(row=row, column=3)
        row += 1

        # Set ID
        ttk.Label(frame, text="Set ID:").grid(row=row, column=0, sticky="w")
        self.id_value = ttk.Entry(frame, width=5)
        self.id_value.grid(row=row, column=1)
        ttk.Button(frame, text="Send", command=self.set_id).grid(row=row, column=2)
        row += 1

        # Set OverV/UnderV/OverT/UnderT
        for label, cmd in [("Set OverVoltage Thr:", "setoverv"), ("Set UnderVoltage Thr:", "setundv"), ("Set OverTemp Thr:", "setovert"), ("Set UnderTemp Thr:", "setundt")]:
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
            entry = ttk.Entry(frame, width=7)
            entry.grid(row=row, column=1)
            ttk.Button(frame, text="Send", command=lambda c=cmd, e=entry: self.set_threshold(c, e)).grid(row=row, column=2)
            setattr(self, f"{cmd}_entry", entry)
            row += 1

        # Output box
        self.output = tk.Text(self.root, height=18, width=70, state="disabled", bg="#222", fg="#0f0")
        self.output.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Help button
        ttk.Button(self.root, text="Help", command=self.show_help).grid(row=1, column=0, sticky="ew", padx=10, pady=5)

    def connect_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            self.log(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
            threading.Thread(target=self.read_serial, daemon=True).start()
        except Exception as e:
            self.log(f"Serial error: {e}")

    def read_serial(self):
        while True:
            try:
                if self.ser and self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        cur_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        self.log(f"[{cur_time}] {line}")
                time.sleep(0.1)
            except Exception as e:
                self.log(f"Serial read error: {e}")
                break

    def log(self, msg):
        self.output.config(state="normal")
        self.output.insert("end", msg + "\n")
        self.output.see("end")
        self.output.config(state="disabled")

    def send_command(self, cmd):
        try:
            payload = 0
            if cmd == "setdate":
                date = datetime.datetime.now()
                payload = bytes(date.strftime("%d%m%Y"), "ascii")
            elif cmd == "settime":
                date = datetime.datetime.now()
                payload = bytes(date.strftime("%H%M%S"), "ascii")
            formatted = format_command(cmd, payload)
            if formatted and self.ser:
                self.ser.write(formatted)
                self.log(f"[Sent] {cmd}")
            else:
                self.log(f"[Error] Could not send {cmd}")
        except Exception as e:
            self.log(f"[Error] {e}")

    def set_dac(self):
        try:
            ch = self.dac_channel.get().lower()
            val = float(self.dac_value.get())
            payload = DAC_CHANNELS_ID.get(ch)
            thr_n = int(val * 1000)
            thr_k = int(thr_n / 1000)
            thr_h = int((thr_n % 1000) / 100)
            thr_d = int((thr_n % 100) / 10)
            thr_u = int((thr_n % 10))
            thr_str = f"{thr_k}{thr_h}{thr_d}{thr_u}"
            payload = payload + bytes(thr_str, "ascii")
            formatted = format_command("setdac", payload)
            if formatted and self.ser:
                self.ser.write(formatted)
                self.log(f"[Sent] setdac {ch} {val}")
            else:
                self.log("[Error] Invalid DAC command")
        except Exception as e:
            self.log(f"[Error] {e}")

    def set_id(self):
        try:
            num = int(self.id_value.get())
            if num < 62:
                num = num + 33
                payload = chr(num).encode('ASCII')
                formatted = format_command("setid", payload)
                if formatted and self.ser:
                    self.ser.write(formatted)
                    self.log(f"[Sent] setid {num-33}")
                else:
                    self.log("[Error] Invalid setid command")
            else:
                self.log("[Error] Maximum id = 63")
        except Exception as e:
            self.log(f"[Error] {e}")

    def set_threshold(self, cmd, entry):
        try:
            val = float(entry.get())
            if cmd in ["setoverv", "setundv"]:
                thr_n = int(val * 1000)
                thr_dk = int(thr_n / 10000)
                thr_k = int((thr_n % 10000) / 1000)
                thr_h = int((thr_n % 1000) / 100)
                thr_d = int((thr_n % 100) / 10)
                thr_u = int((thr_n % 10))
                thr_str = f"{thr_dk}{thr_k}{thr_h}{thr_d}{thr_u}"
            else:
                thr_n = int(val * 100)
                thr_sign = '+' if thr_n >= 0 else '-'
                thr_n = abs(thr_n)
                thr_k = int(thr_n / 1000)
                thr_h = int((thr_n % 1000) / 100)
                thr_d = int((thr_n % 100) / 10)
                thr_u = int((thr_n % 10))
                thr_str = f"{thr_sign}{thr_k}{thr_h}{thr_d}{thr_u}"
            payload = bytes(thr_str, "ascii")
            formatted = format_command(cmd, payload)
            if formatted and self.ser:
                self.ser.write(formatted)
                self.log(f"[Sent] {cmd} {val}")
            else:
                self.log(f"[Error] Invalid {cmd} command")
        except Exception as e:
            self.log(f"[Error] {e}")

    def show_help(self):
        messagebox.showinfo("Help", HELP_CMD_MSG)

if __name__ == "__main__":
    root = tk.Tk()
    app = DigiTechGUI(root)
    root.mainloop()