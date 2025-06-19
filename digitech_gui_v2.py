from logging import root
import tkinter as tk
from tkinter import ttk

import threading
import queue

# v2: Added DAC control tab with 8 setdac inputs/buttons and 8 getdac outputs

def start_gui(ser, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID):
    import datetime

    # --- GUI setup ---
    root = tk.Tk()
    root.title("TB Cmd Interface v2")
    root.resizable(False, False)

    # Move StringVar creation here, after root is created
    getdac_values = {k: tk.StringVar(value='') for k in DAC_CHANNELS_ID.keys()}
    last_setdac = {k: None for k in DAC_CHANNELS_ID.keys()}
    setdac_vars = {k: tk.StringVar() for k in DAC_CHANNELS_ID.keys()}
    serial_queue = queue.Queue()

    def send(cmd, arg1=None, arg2=None):
        try:
            if cmd in {'getstatus','getdata','getdatetime','getdac','gettemp','reset','getid','getconf'}:
                formatted = format_command(cmd, 0)
            elif cmd == 'settime':
                payload = datetime.datetime.now().strftime("%H%M%S").encode("ascii")
                formatted = format_command(cmd, payload)
            elif cmd == 'setdate':
                payload = datetime.datetime.now().strftime("%d%m%Y").encode("ascii")
                formatted = format_command(cmd, payload)
            elif cmd == 'setdac':
                if not arg1 or not arg2: return
                payload = DAC_CHANNELS_ID.get(arg1.lower())
                if payload is None: return
                try: thr_v = float(arg2)
                except: return
                thr_n = int(thr_v * 1000)
                thr_str = f"{thr_n//1000}{(thr_n%1000)//100}{(thr_n%100)//10}{thr_n%10}"
                payload += thr_str.encode("ascii")
                formatted = format_command(cmd, payload)
                # Track last set value for getdac fallback
                last_setdac[arg1.lower()] = arg2
            elif cmd == 'setid':
                if not arg1: return
                try: num = int(arg1)
                except: return
                if num < 62 or num == BOARD__MAGIC_ID:
                    payload = chr(num+33).encode('ASCII')
                    formatted = format_command(cmd, payload)
                else: return
            elif cmd in {'setoverv','setundv'}:
                if not arg1: return
                try: val = float(arg1)
                except: return
                thr_n = int(val * 1000)
                thr_str = f"{thr_n//10000}{(thr_n%10000)//1000}{(thr_n%1000)//100}{(thr_n%100)//10}{thr_n%10}"
                payload = thr_str.encode("ascii")
                formatted = format_command(cmd, payload)
            elif cmd in {'setovert','setundt'}:
                if not arg1: return
                try: val = float(arg1)
                except: return
                thr_n = int(val * 100)
                thr_sign = '-' if thr_n < 0 else '+'
                thr_n = abs(thr_n)
                thr_str = f"{thr_sign}{thr_n//1000}{(thr_n%1000)//100}{(thr_n%100)//10}{thr_n%10}"
                payload = thr_str.encode("ascii")
                formatted = format_command(cmd, payload)
            else:
                return
            if formatted: ser.write(formatted)
        except: pass

    def serial_reader():
        # Read lines from serial and put in queue
        while True:
            try:
                if hasattr(ser, 'in_waiting') and ser.in_waiting:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        serial_queue.put(line)
                else:
                    # For DummySerial
                    import time
                    time.sleep(0.1)
            except Exception:
                pass

    def process_serial_queue():
        # Called periodically in mainloop
        while not serial_queue.empty():
            line = serial_queue.get()
            # Try to parse getdac output: e.g. '>DAC: a=1.234 b=2.345 ...'
            if line.startswith('>') and 'DAC:' in line:
                try:
                    parts = line.split('DAC:')[1].strip().split()
                    for part in parts:
                        if '=' in part:
                            ch, val = part.split('=')
                            ch = ch.strip().lower()
                            if ch in getdac_values:
                                getdac_values[ch].set(val)
                except Exception:
                    pass
        root.after(200, process_serial_queue)

    def getdac_all():
        send('getdac')
        # If no serial output, fallback to last set value
        root.after(500, update_getdac_fallback)

    def update_getdac_fallback():
        # If getdac_values are still empty, use last_setdac
        for ch in DAC_CHANNELS_ID.keys():
            if not getdac_values[ch].get() and last_setdac[ch] is not None:
                getdac_values[ch].set(last_setdac[ch])

    # Notebook (tabs)
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # --- Main tab (original interface) ---
    main_tab = ttk.Frame(notebook)
    notebook.add(main_tab, text="Main")

    # --- Add a framed, centered title label at the top ---
    title_font = ("Consolas", 18, "bold")
    try:
        import tkinter.font as tkfont
        available = tkfont.families()
        if "Consolas" in available:
            title_font = ("Consolas", 18, "bold")
        elif "Menlo" in available:
            title_font = ("Menlo", 18, "bold")
        elif "Courier New" in available:
            title_font = ("Courier New", 18, "bold")
    except:
        pass

    # Visually appealing title area
    title_frame = ttk.Frame(main_tab, padding=10, style="Title.TFrame")
    title_frame.grid(row=0, column=0, columnspan=2, pady=(10, 20), sticky="ew", padx=10)
    main_tab.grid_columnconfigure(0, weight=1)
    main_tab.grid_columnconfigure(1, weight=1)

    title_label = ttk.Label(
        title_frame,
        text="TetraBall Command Interface",
        font=title_font,
        anchor="center",
        style="Title.TLabel"
    )
    title_label.pack(fill="both", expand=True, padx=10, pady=5)

    # Create a visually balanced frame for the controls
    controls_frame = ttk.Frame(main_tab, padding=10)
    controls_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')
    controls_frame.grid_columnconfigure(0, weight=1)
    controls_frame.grid_columnconfigure(1, weight=1)

    # Left: no-argument buttons in a vertical group
    left_group = ttk.LabelFrame(controls_frame, text="Quick Commands", padding=10)
    left_group.grid(row=0, column=0, sticky='nsew', padx=(0, 10), pady=5)
    # Right: argument commands in a vertical group
    right_group = ttk.LabelFrame(controls_frame, text="Advanced Commands", padding=10)
    right_group.grid(row=0, column=1, sticky='nsew', padx=(10, 0), pady=5)

    controls_frame.grid_rowconfigure(0, weight=1)
    left_group.grid_columnconfigure(0, weight=1)
    right_group.grid_columnconfigure(0, weight=1)

    # Split buttons into no-argument and argument commands
    no_arg_buttons = [
        ("Get status", 'getstatus', None, None),
        ("Get data", 'getdata', None, None),
        ("Set date (now)", 'setdate', None, None),
        ("Set time (now)", 'settime', None, None),
        ("Get datetime", 'getdatetime', None, None),
        ("Get DAC", 'getdac', None, None),
        ("Get ID", 'getid', None, None),
        ("Get temperature", 'gettemp', None, None),
        ("Reset", 'reset', None, None),
        ("Get configuration", 'getconf', None, None),
    ]
    arg_buttons = [
        # setdac omitted from main tab
        ("Set ID", 'setid', ("New ID:", tk.StringVar(), ttk.Entry), None),
        ("Set overV", 'setoverv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
        ("Set underV", 'setundv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
        ("Set overTemp", 'setovert', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
        ("Set underTemp", 'setundt', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
    ]

    # Place no-argument buttons in left_group
    row = 0
    for label, cmd, arg1, arg2 in no_arg_buttons:
        def make_cmd_callback(c=cmd, a1=arg1, a2=arg2):
            def callback():
                send(c,
                     a1[1].get() if a1 else None,
                     a2[1].get() if a2 else None)
            return callback
        ttk.Button(left_group, text=label, width=20,
                   command=make_cmd_callback()
                  ).grid(column=0, row=row, pady=4, sticky='ew')
        row += 1

    # Place argument buttons in right_group
    row = 0
    for label, cmd, arg1, arg2 in arg_buttons:
        def make_cmd_callback(c=cmd, a1=arg1, a2=arg2):
            def callback():
                send(c,
                     a1[1].get() if a1 else None,
                     a2[1].get() if a2 else None)
                # Reset fields for numeric threshold commands
                if c in {'setoverv', 'setundv', 'setovert', 'setundt', 'setid'}:
                    if a1: a1[1].set('')
                    if a2: a2[1].set('')
            return callback
        ttk.Button(right_group, text=label, width=20,
                   command=make_cmd_callback()
                  ).grid(column=0, row=row, pady=4, sticky='ew')
        col = 1
        for arg in (arg1, arg2):
            if arg:
                arg_label, arg_var, arg_widget = arg
                ttk.Label(right_group, text=arg_label).grid(column=col, row=row, padx=2)
                arg_widget(right_group, textvariable=arg_var, width=10).grid(column=col+1, row=row, padx=2)
                col += 2
        row += 1

    # Add a style for the title
    style = ttk.Style()
    style.configure("Title.TFrame", background="#FE5000")
    style.configure("Title.TLabel", background="#FE5000", foreground="#fff", font=title_font)

    # --- DAC control tab ---
    dac_tab = ttk.Frame(notebook)
    notebook.add(dac_tab, text="DAC control")

    # Visually appealing title area for DAC tab
    dac_title_frame = ttk.Frame(dac_tab, padding=10, style="Title.TFrame")
    dac_title_frame.grid(row=0, column=0, columnspan=8, pady=(10, 20), sticky="ew", padx=10)
    ttk.Label(
        dac_title_frame,
        text="DAC Channel Control",
        font=(title_font[0], 14, "bold"),
        anchor="center",
        style="Title.TLabel"
    ).pack(fill="both", expand=True, padx=10, pady=5)

    # SetDAC controls group
    setdac_group = ttk.LabelFrame(dac_tab, text="Set DAC (V)", padding=10)
    setdac_group.grid(row=1, column=0, columnspan=8, sticky='ew', padx=10, pady=(0, 10))
    for idx, ch in enumerate(DAC_CHANNELS_ID.keys()):
        ttk.Label(setdac_group, text=f"Channel {ch.upper()}").grid(row=0, column=idx, padx=5, pady=2)
        ttk.Entry(setdac_group, textvariable=setdac_vars[ch], width=7).grid(row=1, column=idx, padx=5, pady=2)
        def make_setdac_callback(channel=ch):
            def cb():
                val = setdac_vars[channel].get()
                send('setdac', channel, val)
                setdac_vars[channel].set('')
            return cb
        ttk.Button(setdac_group, text="Set", command=make_setdac_callback()).grid(row=2, column=idx, pady=2)

    # GetDAC controls group
    getdac_group = ttk.LabelFrame(dac_tab, text="Get DAC (last read or set)", padding=10)
    getdac_group.grid(row=2, column=0, columnspan=8, sticky='ew', padx=10, pady=(0, 10))
    for idx, ch in enumerate(DAC_CHANNELS_ID.keys()):
        ttk.Label(getdac_group, text=f"Ch {ch.upper()}").grid(row=0, column=idx, padx=5, pady=2)
        ttk.Label(getdac_group, textvariable=getdac_values[ch], relief="sunken", width=7).grid(row=1, column=idx, padx=5, pady=2)

    ttk.Button(getdac_group, text="Get All DACs", command=getdac_all).grid(row=2, column=0, columnspan=8, pady=10)

    # Start serial reader thread if not DummySerial
    if hasattr(ser, 'in_waiting'):
        threading.Thread(target=serial_reader, daemon=True).start()
        root.after(200, process_serial_queue)

    root.mainloop()

if __name__ == "__main__":
    class DummySerial:
        def write(self, data):
            print(f"[DummySerial] Would send: {data}")
        in_waiting = False
        def readline(self):
            return b''

    def dummy_format_command(cmd, payload):
        if isinstance(payload, int): payload = b''
        return f"<{cmd}|{payload}>".encode('ascii')

    DAC_CHANNELS_ID = {k: bytes([ord(k)]) for k in 'abcdefgh'}
    BOARD__MAGIC_ID = 67  # Example value

    start_gui(DummySerial(), dummy_format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID)
