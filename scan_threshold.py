import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

import serial
import serial.tools.list_ports

import os

import threading

import time
import datetime





DEBUG = False



SERIAL_PORT = ''
BAUD_RATE = 115200

BOARD_ID_OFFSET = 33
BOARD_MAGIC_ID = 67
BOARD_DEFAULT_ID = 0

CHANNELS_GROUPS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

def format_command(board=BOARD_MAGIC_ID, cmd=None, payload=None):
    SLAVE_ID = bytes.fromhex(hex(board + BOARD_ID_OFFSET)[2:])
    CMD_TERMINATOR = bytes.fromhex('0a')
    #
    commands_map = {
        'getstatus'  : lambda p:    SLAVE_ID + bytes([ord("a")]) + CMD_TERMINATOR,
        'getdata'    : lambda p:    SLAVE_ID + bytes([ord("b")]) + CMD_TERMINATOR,
        'setdate'    : lambda p:    SLAVE_ID + bytes([ord("c")]) + bytes(p, "ascii") + CMD_TERMINATOR,
        'settime'    : lambda p:    SLAVE_ID + bytes([ord("d")]) + bytes(p, "ascii") + CMD_TERMINATOR,
        'getdatetime': lambda p:    SLAVE_ID + bytes([ord("e")]) + CMD_TERMINATOR,
        'getdac'     : lambda p:    SLAVE_ID + bytes([ord("f")]) + CMD_TERMINATOR,
        'setdac'     : lambda p:    SLAVE_ID + bytes([ord("g")]) + bytes(p, "ascii") + CMD_TERMINATOR,
        'gettemp'    : lambda p:    SLAVE_ID + bytes([ord("h")]) + CMD_TERMINATOR,
        'reset'      : lambda p:    SLAVE_ID + bytes([ord("i")]) + CMD_TERMINATOR,
        'setid'      : lambda p:    SLAVE_ID + bytes([ord("j")]) + bytes(p, "ascii") + CMD_TERMINATOR,
        'getid'      : lambda p:    SLAVE_ID + bytes([ord("k")]) + CMD_TERMINATOR,
        'setoverv'   : lambda p:    SLAVE_ID + bytes([ord("l")]) + bytes(p, "ascii") + CMD_TERMINATOR,
        'setundv'    : lambda p:    SLAVE_ID + bytes([ord("m")]) + bytes(p, "ascii") + CMD_TERMINATOR,
        'setovert'   : lambda p:    SLAVE_ID + bytes([ord("n")]) + bytes(p, "ascii") + CMD_TERMINATOR,
        'setundt'    : lambda p:    SLAVE_ID + bytes([ord("o")]) + bytes(p, "ascii") + CMD_TERMINATOR,
        'getconf'    : lambda p:    SLAVE_ID + bytes([ord("p")]) + CMD_TERMINATOR,
    }
    formatter = commands_map.get(cmd.lower())
    if formatter:
        return formatter(payload)
    else:
        return None

def send_command(serial_port, formatted_command, retry=3, wait=1):
    for attempt in range(retry):
        if DEBUG: print("<" + formatted_command.decode('utf-8').strip())
        serial_port.write(formatted_command)
        time.sleep(wait)
        response = serial_port.readline().decode('utf-8').strip()
        if DEBUG: print(response)
        if response and response[0] == ">":
            return True #break
    else:
        return False










class MainWindow(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('Bril')
        self.resizable(False, False)
        
        self.lblSerialPort = tk.Label(master=self, text='Serial port:', font='sans 10')
        self.lblSerialPort.grid(row=0, column=0, padx=(5, 2), pady=(5, 0), sticky=tk.E)
        #
        self.cmbSerialPort = ttk.Combobox(master=self, width=27, font='sans 10')
        self.cmbSerialPort.bind('<<ComboboxSelected>>')
        self.cmbSerialPort.grid(row=0, column=1, padx=2, pady=(5, 0))
        #
        self.btnReScan = tk.Button(master=self, command=self.scan_serialports, text=' \u21BB ', font='sans 8')
        self.btnReScan.grid(row=0, column=2, padx=(2, 5), pady=(5, 0), sticky=tk.W)
        
        self.lblBoardID = tk.Label(master=self, text='Board ID:', font='sans 10')
        self.lblBoardID.grid(row=0, column=3, padx=(5, 2), pady=(5, 0), sticky=tk.E)
        #
        self.spbBoardID = tk.Spinbox(master=self, from_=0, to=63, width=5, font="sans 10")
        self.spbBoardID.grid(row=0, column=4, columnspan=2, padx=(2, 5), pady=(5, 0), sticky=tk.W)
        
        self.lblFile = tk.Label(master=self, text="File:", font='sans 10')
        self.lblFile.grid(row=1, column=0, padx=(5, 2), pady=(5, 0), sticky=tk.E)
        #
        self.txtFile = tk.Entry(master=self, width=50, font='sans 10')
        self.txtFile.grid(row=1, column=1, columnspan=4, padx=2, pady=(5, 0))
        #
        self.btnFile = tk.Button(master=self, command=self.select_path, text=' .. ', font='sans 8')
        self.btnFile.grid(row=1, column=5, padx=(2, 5), pady=(5, 0), sticky=tk.W)
        
        # Threshold range controls
        self.lblThresholdMin = tk.Label(master=self, text='Threshold min:', font='sans 10')
        self.lblThresholdMin.grid(row=2, column=0, padx=(5, 2), pady=(5, 0), sticky=tk.E)
        self.spbThresholdMin = tk.Spinbox(master=self, from_=0, to=1000, width=5, font="sans 10")
        self.spbThresholdMin.grid(row=2, column=1, padx=(2, 5), pady=(5, 0), sticky=tk.W)
        self.spbThresholdMin.delete(0, tk.END)
        self.spbThresholdMin.insert(0, 125)

        self.lblThresholdMax = tk.Label(master=self, text='Threshold max:', font='sans 10')
        self.lblThresholdMax.grid(row=2, column=2, padx=(5, 2), pady=(5, 0), sticky=tk.E)
        self.spbThresholdMax = tk.Spinbox(master=self, from_=0, to=1000, width=5, font="sans 10")
        self.spbThresholdMax.grid(row=2, column=3, padx=(2, 5), pady=(5, 0), sticky=tk.W)
        self.spbThresholdMax.delete(0, tk.END)
        self.spbThresholdMax.insert(0, 525)

        # Move Scan Threshold button down
        self.btnLoop = tk.Button(master=self, command=self.start_loop, text='Scan Threshold')
        self.btnLoop.grid(row=3, column=0, columnspan=6, padx=5, pady=5)

        self.scan_serialports()
        #
        self.spbBoardID.delete(0, tk.END)
        self.spbBoardID.insert(0, BOARD_DEFAULT_ID)
        #
        self.txtFile.delete(0, tk.END)
        self.txtFile.insert(0, os.path.dirname(os.path.abspath(__file__))+os.sep+"bril.csv")
    
    def scan_serialports(self):
        self.cmbSerialPort.set('')
        self.cmbSerialPort.current(None)
        #
        self.cmbSerialPort['values'] = ('',)
        for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
            self.cmbSerialPort['values'] = self.cmbSerialPort['values'] + (port,)
        #
        if len(serial.tools.list_ports.comports())==1 and len(self.cmbSerialPort['values'])==2:
            self.cmbSerialPort.current(len(self.cmbSerialPort['values'])-1)
    
    def select_path(self):
        file_path = filedialog.asksaveasfilename(initialdir=os.path.dirname(self.txtFile.get()), initialfile=os.path.basename(self.txtFile.get()), filetypes=[('File CSV', '*.csv')], defaultextension='.csv', confirmoverwrite=True)
        if file_path:
            self.txtFile.delete(0, tk.END)
            self.txtFile.insert(0, file_path)
    
    def start_loop(self):
        try:
            self.cmbSerialPort.config(state="disabled")
            self.btnReScan.config(state="disabled")
            self.spbBoardID.config(state="disabled")
            self.txtFile.config(state="disabled")
            self.btnFile.config(state="disabled")
            self.btnLoop.config(state="disabled")
            #
            self.config(cursor="wait")
            self.update()

            min_threshold = int(self.spbThresholdMin.get())
            max_threshold = int(self.spbThresholdMax.get())
            
            with serial.Serial(self.cmbSerialPort.get(), BAUD_RATE, timeout=1) as serial_port, open(self.txtFile.get(), "w") as output_file:
                
                time.sleep(1)
                
                # imposto data/ora e riavvio la scheda
                if not send_command(serial_port, format_command(int(self.spbBoardID.get()), "setDate", datetime.datetime.now().strftime("%d%m%Y"))):
                    raise RuntimeError("Communication error.")
                if not send_command(serial_port, format_command(int(self.spbBoardID.get()), "setTime", datetime.datetime.now().strftime("%H%M%S"))):
                    raise RuntimeError("Communication error.'")
                if not send_command(serial_port, format_command(int(self.spbBoardID.get()), "reset")):
                    raise RuntimeError("Communication error.")
                #
                serial_port.reset_input_buffer()
                serial_port.reset_output_buffer()
                
                time.sleep(5)
                
                # preparo il file
                output_file.write("DATE\tTIME\t")
                for ch in range(48):
                    output_file.write("CH_"+str(ch+1).rjust(2, "0")+"\t")
                output_file.write("THRESHOLD\n")
                output_file.flush()
                
                for mv in range(min_threshold, max_threshold + 1, 50):    # ciclo sulle soglie
                    for grp in CHANNELS_GROUPS:    # ciclo sui dac
                        if not send_command(serial_port, format_command(int(self.spbBoardID.get()), "setDAC", grp+str(mv).rjust(4, "0"))):
                            raise RuntimeError("Communication error.")
                    
                    # pulisco eventuali dati vecchi
                    if DEBUG: print("*Cleaning buffer...")
                    serial_port.write( format_command(int(self.spbBoardID.get()), "getData") )
                    time.sleep(1)
                    while True:
                        line = serial_port.readline().decode('utf-8', errors='ignore').strip()
                        if not line:
                            break
                    #
                    serial_port.reset_input_buffer()
                    serial_port.reset_output_buffer()
                    
                    # acquisisco i dati per la taratura
                    if DEBUG: print("*Waiting for data acquisition...")
                    time.sleep(10)
                    #
                    if DEBUG: print("<" + format_command(int(self.spbBoardID.get()), "getData").decode('utf-8').strip())
                    serial_port.write( format_command(int(self.spbBoardID.get()), "getData") )
                    time.sleep(1)
                    while True:
                        line = serial_port.readline().decode('utf-8', errors='ignore').strip()
                        if line and line[0] != ">":
                            if DEBUG: print(">"+line)
                            parts = line.split("\t")
                            if parts:
                                output_file.write(parts[0]+"\t"+parts[1]+"\t")
                                for ch in range(48):
                                    output_file.write(parts[ch+2]+"\t")
                        else:
                            break
                        #
                        output_file.write(str("%.3f" % (mv/1000))+"\n")
                        output_file.flush()
                    
                if DEBUG: print("*End.")
                messagebox.showinfo(title=self.title(), message="Completed.")
        except serial.SerialException as ex:
            messagebox.showerror(title=self.title(), message="Connection error.")
        except FileNotFoundError as ex:
            messagebox.showerror(title=self.title(), message="File not found.")
        except Exception as ex:
            messagebox.showerror(title=self.title(), message=str(ex))
        finally:
            self.cmbSerialPort.config(state="normal")
            self.btnReScan.config(state="normal")
            self.spbBoardID.config(state="normal")
            self.txtFile.config(state="normal")
            self.btnFile.config(state="normal")
            self.btnLoop.config(state="normal")
            #
            self.config(cursor="")
            self.update()



if __name__ == "__main__":
    window = MainWindow()
    window.mainloop()
