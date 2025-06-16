import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import queue
import sys
import os

SCRIPT = os.path.join(os.path.dirname(__file__), "Digitech_Bril_Com.py")

class DigiTechGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Digitech Bril Board CLI Wrapper")
        self.proc = None
        self.output_queue = queue.Queue()
        self.create_widgets()
        self.start_cli_process()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
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
        self.dac_channel = ttk.Combobox(frame, values=[chr(ord('a')+i) for i in range(8)], width=2)
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
        self.thresh_entries = {}
        for label, cmd in [
            ("Set OverVoltage Thr:", "setoverv"),
            ("Set UnderVoltage Thr:", "setundv"),
            ("Set OverTemp Thr:", "setovert"),
            ("Set UnderTemp Thr:", "setundt")]:
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
            entry = ttk.Entry(frame, width=7)
            entry.grid(row=row, column=1)
            ttk.Button(frame, text="Send", command=lambda c=cmd, e=entry: self.set_threshold(c, e)).grid(row=row, column=2)
            self.thresh_entries[cmd] = entry
            row += 1

        # Output box
        self.output = tk.Text(self.root, height=18, width=70, state="disabled", bg="#222", fg="#0f0")
        self.output.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Help button
        ttk.Button(self.root, text="Help", command=self.show_help).grid(row=1, column=0, sticky="ew", padx=10, pady=5)

    def start_cli_process(self):
        self.proc = subprocess.Popen(
            [sys.executable, SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        threading.Thread(target=self.read_output, daemon=True).start()

    def read_output(self):
        for line in self.proc.stdout:
            self.output_queue.put(line)
            self.root.after(0, self.display_output)

    def display_output(self):
        while not self.output_queue.empty():
            line = self.output_queue.get_nowait()
            self.output.config(state="normal")
            self.output.insert("end", line)
            self.output.see("end")
            self.output.config(state="disabled")

    def send_command(self, cmd):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.write(cmd + "\n")
                self.proc.stdin.flush()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send command: {e}")

    def set_dac(self):
        ch = self.dac_channel.get().strip().lower()
        val = self.dac_value.get().strip()
        if ch and val:
            try:
                float(val)
                cmd = f"setdac {ch} {val}"
                self.send_command(cmd)
            except ValueError:
                messagebox.showerror("Error", "Invalid DAC value")

    def set_id(self):
        val = self.id_value.get().strip()
        if val:
            try:
                int(val)
                cmd = f"setid {val}"
                self.send_command(cmd)
            except ValueError:
                messagebox.showerror("Error", "Invalid ID value")

    def set_threshold(self, cmd, entry):
        val = entry.get().strip()
        if val:
            try:
                float(val)
                self.send_command(f"{cmd} {val}")
            except ValueError:
                messagebox.showerror("Error", "Invalid threshold value")

    def show_help(self):
        self.send_command("help")

    def on_close(self):
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DigiTechGUI(root)
    root.mainloop()