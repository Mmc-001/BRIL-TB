import tkinter as tk
from tkinter import ttk
import datetime

HELP_CMD_MSG = """
    USER INPUT   \t     OPCODE      \t      Description                     \t      Arguments
    ===============================================================================================
    getStatus    \t     a (0x61)    \t      Get Status                      \t      
    getData      \t     b (0x62)    \t      Get Data                        \t      
    SetDate      \t     c (0x63)    \t      Set Date                        \t      [args]
    SetTime      \t     d (0x64)    \t      Set Time                        \t      [args]
    getDateTime  \t     e (0x65)    \t      Get Date and Time               \t      
    getDAC       \t     f (0x66)    \t      Get DAC Threshold               \t      
    setDAC       \t     g (0x67)    \t      Set DAC Threshold               \t      [CHID thr_V]
    getTemp      \t     h (0x68)    \t      Get Temperature                 \t      
    reset        \t     i (0x69)    \t      Soft Reset                      \t      
    setID        \t     j (0x6a)    \t      Set Board ID                    \t      [newID]
    getID        \t     k (0x6b)    \t      Get Board ID                    \t      
    setoverv     \t     l (0x6c)    \t      Set Over Voltage Thr            \t      [thr_V]
    setundv      \t     m (0x6d)    \t      Set Under Voltage Thr           \t      [thr_V]
    setovert     \t     n (0x6e)    \t      Set Overtemperature Thr         \t      [thr_T]
    setundt      \t     o (0x6f)    \t      Set Undertemperature Thr        \t      [thr_T]
    getconf      \t     p (0x70)    \t      Get Volt and Temp Thr Config    \t      
    start        \t     q (0x71)    \t      Start Data Acquisition          \t      
    stop         \t     r (0x72)    \t      Stop Data Acquisition           \t      
    help         \t     (--local)   \t      Print this help message         \t      
"""

def send(cmd, arg1, arg2, serial_port, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID, CTRL_FILE=None):
    try:
        if cmd in {'getstatus','getdata','getdatetime','getdac','gettemp','reset','getid','getconf','start','stop'}:
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
            if CTRL_FILE is not None:
                with open(CTRL_FILE, 'a') as ctrl_file:
                    cur_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    ctrl_file.write(f"{cur_time}\t Set DAC: CHN = {arg1}, THR = {thr_v}V\n")
                    ctrl_file.flush()
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
        if formatted: serial_port.write(formatted)
    except: pass

def channel_dropdown(var, dac_frame, DAC_CHANNELS_ID):
    return ttk.OptionMenu(dac_frame, var, 'a', *DAC_CHANNELS_ID.keys())

def add_buttons(frame, buttons, send_func, dac_frame=None, DAC_CHANNELS_ID=None, vertical=False, col=0, start_row=0):
    row = start_row
    for label, cmd, arg1, arg2 in buttons:
        def make_cmd_callback(c=cmd, a1=arg1, a2=arg2):
            def callback():
                send_func(c,
                          a1[1].get() if a1 else None,
                          a2[1].get() if a2 else None)
                # if c in {
                    # 'setdac',
                    # 'setoverv',
                    # 'setundv',
                    # 'setovert',
                    # 'setundt',
                    # 'setid'}:
                    # if c == 'setdac':
                        # if a2: a2[1].set('')
                    # else:
                        # if a1: a1[1].set('')
                        # if a2: a2[1].set('')
                if c in {'setoverv', 'setundv', 'setovert', 'setundt', 'setid'}:
                    if a1: a1[1].set('')
                    if a2: a2[1].set('')
            return callback
        if vertical and arg1 and not arg2:
            arg_label, arg_var, arg_widget = arg1
            ttk.Label(frame, text=arg_label).grid(column=col*2, row=row, sticky='ew', padx=(0,2))
            arg_widget(frame, textvariable=arg_var, width=7).grid(column=col*2+1, row=row, sticky='ew', padx=(0,8))
            frame.grid_columnconfigure(col*2, weight=1)
            frame.grid_columnconfigure(col*2+1, weight=1)
            row += 1
            ttk.Button(frame, text=label,
                       command=make_cmd_callback()
                      ).grid(column=col*2, row=row, columnspan=2, pady=4, sticky='ew')
            row += 1
        elif cmd == 'setdac':
            arg_label1, arg_var1, arg_widget1 = arg1
            arg_label2, arg_var2, arg_widget2 = arg2
            ttk.Label(frame, text=arg_label1).grid(column=0, row=row, sticky='ew', padx=(0,2))
            channel_dropdown(arg_var1, dac_frame, DAC_CHANNELS_ID).grid(column=1, row=row, sticky='ew', padx=(0,8))
            ttk.Label(frame, text=arg_label2).grid(column=2, row=row, sticky='ew', padx=(0,2))
            arg_widget2(frame, textvariable=arg_var2, width=7).grid(column=3, row=row, sticky='ew', padx=(0,8))
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(1, weight=1)
            frame.grid_columnconfigure(2, weight=1)
            frame.grid_columnconfigure(3, weight=1)
            row += 1
            ttk.Button(frame, text=label,
                       command=make_cmd_callback()
                      ).grid(column=0, row=row, columnspan=4, pady=4, sticky='ew')
            row += 1
        elif cmd == 'setid':
            arg_label, arg_var, arg_widget = arg1
            ttk.Label(frame, text=arg_label).grid(column=0, row=row, sticky='ew', padx=(0,2))
            arg_widget(frame, textvariable=arg_var, width=7).grid(column=1, row=row, columnspan=3, sticky='ew', padx=(0,8))
            for c in range(4):
                frame.grid_columnconfigure(c, weight=1)
            row += 1
            ttk.Button(frame, text=label,
                       command=make_cmd_callback()
                      ).grid(column=0, row=row, columnspan=4, pady=4, sticky='ew')
            row += 1
        elif cmd in {'getdac', 'getid'}:
            for c in range(4):
                frame.grid_columnconfigure(c, weight=1)
            ttk.Button(frame, text=label,
                       command=make_cmd_callback()
                      ).grid(column=0, row=row, columnspan=4, pady=4, sticky='ew')
            row += 1
        elif arg1 or arg2:
            for arg in (arg1, arg2):
                if arg:
                    arg_label, arg_var, arg_widget = arg
                    ttk.Label(frame, text=arg_label).grid(column=0, row=row, sticky='ew', padx=(0,2))
                    arg_widget(frame, textvariable=arg_var, width=7).grid(column=1, row=row, sticky='ew', padx=(0,8))
                    frame.grid_columnconfigure(0, weight=1)
                    frame.grid_columnconfigure(1, weight=1)
                    row += 1
            ttk.Button(frame, text=label,
                       command=make_cmd_callback()
                      ).grid(column=0, row=row, columnspan=2, pady=4, sticky='ew')
            row += 1
        else:
            frame.grid_columnconfigure(0, weight=1)
            ttk.Button(frame, text=label,
                       command=make_cmd_callback()
                      ).grid(column=0, row=row, pady=4, sticky='ew')
            row += 1
    return row

def show_help(root):
    # Use a persistent attribute on root to store the help window reference
    if hasattr(root, '_help_win') and root._help_win is not None and tk.Toplevel.winfo_exists(root._help_win):
        root._help_win.lift()
        root._help_win.focus_force()
        return
    help_win = tk.Toplevel(root)
    root._help_win = help_win
    help_win.title("Command Help")
    help_win.resizable(width=False, height=False)
    lines = HELP_CMD_MSG.strip().splitlines()
    max_line_len = max((len(line) for line in lines), default=80)
    width = min(max_line_len + 4, 120)
    height = min(len(lines) + 4, 30)
    help_text = tk.Text(help_win, wrap="none", width=width, height=height)
    help_text.insert("1.0", HELP_CMD_MSG)
    help_text.config(state="disabled")
    help_text.pack(padx=10, pady=10, fill="both", expand=True)
    def close_help():
        root._help_win = None
        help_win.destroy()
    ttk.Button(help_win, text="Close", command=close_help).pack(pady=5)
    help_win.protocol("WM_DELETE_WINDOW", close_help)

def start_gui(serial_port, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID, CTRL_FILE):
    root = tk.Tk()
    root.title('TB - Cmd Interface')
    root.resizable(width=False, height=False)
    # Title
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
    title_frame = tk.Frame(root, bd=2, relief="groove", bg="#FE5000")
    title_frame.grid(row=0, column=0, columnspan=3, pady=(10, 20), sticky='ew', padx=10)
    title_label = tk.Label(
        title_frame,
        text="TetraBall Command Interface",
        font=title_font,
        anchor="center",
    )
    title_label.pack(fill="both", expand=True, padx=10, pady=5)
    # Data Acquisition Control Frame
    daq_frame = ttk.LabelFrame(root, text="Data Acquisition Control", padding=10)
    daq_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=(0, 10))
    root.grid_rowconfigure(1, weight=0)
    daq_btn_font = (title_font[0], int(title_font[1]*1.5), "bold") if isinstance(title_font, tuple) else ("TkDefaultFont", 18, "bold")
    daq_start_btn = ttk.Button(daq_frame, text="Start Acquisition", command=lambda: send('start', None, None, serial_port, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID))
    daq_stop_btn = ttk.Button(daq_frame, text="Stop Acquisition", command=lambda: send('stop', None, None, serial_port, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID))
    try:
        daq_start_btn.config(font=daq_btn_font)
        daq_stop_btn.config(font=daq_btn_font)
    except Exception:
        pass
    daq_start_btn.grid(row=0, column=0, padx=10, pady=8, sticky='ew')
    daq_stop_btn.grid(row=0, column=1, padx=10, pady=8, sticky='ew')
    daq_frame.grid_columnconfigure(0, weight=1)
    daq_frame.grid_columnconfigure(1, weight=1)
    # Frames
    board_frame = ttk.LabelFrame(root, text="Board Control", padding=10)
    board_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
    datetime_frame = ttk.LabelFrame(root, text="Date & Time", padding=10)
    datetime_frame.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
    dac_frame = ttk.LabelFrame(root, text="DAC Control", padding=10)
    dac_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
    id_frame = ttk.LabelFrame(root, text="Board ID", padding=10)
    id_frame.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
    thresholds_frame = ttk.LabelFrame(root, text="Voltage & Temperature Thresholds", padding=10)
    thresholds_frame.grid(row=4, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
    help_frame = ttk.LabelFrame(root, text="Help", padding=10)
    help_frame.grid(row=5, column=0, columnspan=2, sticky='ew', padx=5, pady=10)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    # Button definitions
    board_buttons = [
        ("Get status", 'getstatus', None, None),
        ("Get data", 'getdata', None, None),
        ("Reset", 'reset', None, None),
    ]
    datetime_buttons = [
        ("Set date (now)", 'setdate', None, None),
        ("Set time (now)", 'settime', None, None),
        ("Get date&time", 'getdatetime', None, None),
    ]
    dac_buttons = [
        ("Set DAC", 'setdac', ("CHN:", tk.StringVar(value='a'), ttk.Entry), ("THR (V):", tk.StringVar(), ttk.Entry)),
        ("Get DAC", 'getdac', None, None),
    ]
    id_buttons = [
        # ("Set ID", 'setid', ("New ID:", tk.StringVar(), ttk.Entry), None),
        ("Get ID", 'getid', None, None),
    ]
    volt_buttons = [
        ("Set overV", 'setoverv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
        ("Set underV", 'setundv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
    ]
    temp_buttons = [
        ("Set overTemp", 'setovert', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
        ("Set underTemp", 'setundt', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
    ]
    # Partial send function for button callbacks
    send_func = lambda c, a1, a2: send(c, a1, a2, serial_port, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID, CTRL_FILE=CTRL_FILE)
    add_buttons(board_frame, board_buttons, send_func)
    add_buttons(datetime_frame, datetime_buttons, send_func)
    add_buttons(dac_frame, dac_buttons, send_func, dac_frame, DAC_CHANNELS_ID)
    add_buttons(id_frame, id_buttons, send_func)
    max_rows = max(len(volt_buttons), len(temp_buttons)) * 2
    add_buttons(thresholds_frame, volt_buttons, send_func, vertical=True, col=0, start_row=0)
    add_buttons(thresholds_frame, temp_buttons, send_func, vertical=True, col=1, start_row=0)
    # thresholds_frame.grid_columnconfigure(0, weight=1)
    # thresholds_frame.grid_columnconfigure(1, weight=1)
    # thresholds_frame.grid_columnconfigure(2, weight=1)
    # thresholds_frame.grid_columnconfigure(3, weight=1)
    for c in range(4):
        thresholds_frame.grid_columnconfigure(c, weight=1)
    ttk.Button(thresholds_frame, text="Get configuration", command=lambda: send('getconf', None, None, serial_port, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID))\
        .grid(column=0, row=max_rows, columnspan=2, pady=8, sticky='ew')
    ttk.Button(thresholds_frame, text="Get temperature", command=lambda: send('gettemp', None, None, serial_port, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID))\
        .grid(column=2, row=max_rows, columnspan=2, pady=8, sticky='ew')
    help_frame.grid_columnconfigure(0, weight=1)
    help_frame.grid_columnconfigure(1, weight=1)
    ttk.Button(help_frame, text="Print Command Help", command=lambda: show_help(root)).grid(row=0, column=0, columnspan=2, pady=2)
    root.mainloop()

if __name__ == "__main__":
    class DummySerial:
        def write(self, data):
            print(f"[DummySerial] Would send: {data}")
    def dummy_format_command(cmd, payload):
        if isinstance(payload, int): payload = b''
        return f"<{cmd}|{payload}>".encode('ascii')
    DAC_CHANNELS_ID = {k: bytes([ord(k)]) for k in 'abcdefgh'}
    BOARD__MAGIC_ID = 67  # Example value
    start_gui(DummySerial(), dummy_format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID, CTRL_FILE='ctrl_log.txt')