from logging import root
import tkinter as tk
from tkinter import ttk

# Import the help message from Digitech_Bril_Com.py
try:
    from Digitech_Bril_Com import HELP_CMD_MSG
except ImportError:
    HELP_CMD_MSG = "Help message not available."

def start_gui(ser, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID):
    import datetime

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

    root = tk.Tk()
    root.title("TB Cmd Interface")

    # --- Add a framed, centered title label at the top ---
    title_font = ("Consolas", 18, "bold")  # Try Consolas first
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
    title_frame.grid(row=0, column=0, columnspan=3, pady=(10, 20), sticky="ew", padx=10)

    title_label = tk.Label(
        title_frame,
        text="TetraBall Command Interface",
        font=title_font,
        anchor="center",
    )
    title_label.pack(fill="both", expand=True, padx=10, pady=5)
    # ---------------------------------------------

    # --- Frames for logical grouping ---
    # New layout with all frames expanding to the same width (sticky='ew')
    board_frame = ttk.LabelFrame(root, text="Board Control", padding=10)
    board_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
    datetime_frame = ttk.LabelFrame(root, text="Date & Time", padding=10)
    datetime_frame.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
    dac_frame = ttk.LabelFrame(root, text="DAC Control", padding=10)
    dac_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
    id_frame = ttk.LabelFrame(root, text="Board ID", padding=10)
    id_frame.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
    volt_frame = ttk.LabelFrame(root, text="Voltage Thresholds", padding=10)
    volt_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
    temp_frame = ttk.LabelFrame(root, text="Temperature Thresholds", padding=10)
    temp_frame.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
    help_frame = ttk.LabelFrame(root, text="Help", padding=10)
    help_frame.grid(row=4, column=0, columnspan=2, sticky='ew', padx=5, pady=10)
    # Make columns expand equally
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    def channel_dropdown(var):
        return ttk.OptionMenu(dac_frame, var, 'a', *DAC_CHANNELS_ID.keys())

    # --- Button definitions grouped by logic ---
    # Board Control
    board_buttons = [
        ("Reset", 'reset', None, None),
        ("Get status", 'getstatus', None, None),
        ("Get configuration", 'getconf', None, None),
    ]
    # Date & Time
    datetime_buttons = [
        ("Set date (now)", 'setdate', None, None),
        ("Set time (now)", 'settime', None, None),
        ("Get datetime", 'getdatetime', None, None),
    ]
    # DAC
    dac_buttons = [
        ("Set DAC", 'setdac', ("Channel:", tk.StringVar(value='a'), channel_dropdown), ("Thr (V):", tk.StringVar(), ttk.Entry)),
        ("Get DAC", 'getdac', None, None),
    ]
    # Voltage Thresholds
    volt_buttons = [
        ("Set overV", 'setoverv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
        ("Set underV", 'setundv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
    ]
    # Temperature Thresholds
    temp_buttons = [
        ("Set overTemp", 'setovert', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
        ("Set underTemp", 'setundt', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
    ]
    # Board ID
    id_buttons = [
        ("Set ID", 'setid', ("New ID:", tk.StringVar(), ttk.Entry), None),
        ("Get ID", 'getid', None, None),
    ]

    # Helper to create buttons and their argument widgets
    def add_buttons(frame, buttons):
        row = 0
        for label, cmd, arg1, arg2 in buttons:
            def make_cmd_callback(c=cmd, a1=arg1, a2=arg2):
                def callback():
                    send(c,
                         a1[1].get() if a1 else None,
                         a2[1].get() if a2 else None)
                    if c in {'setdac', 'setoverv', 'setundv', 'setovert', 'setundt', 'setid'}:
                        if c == 'setdac':
                            if a2: a2[1].set('')
                        else:
                            if a1: a1[1].set('')
                            if a2: a2[1].set('')
                return callback
            # Special layout for setdac: channel selector and label on first line, threshold input on second, button on third
            if cmd == 'setdac':
                arg_label1, arg_var1, arg_widget1 = arg1
                ttk.Label(frame, text=arg_label1).grid(column=0, row=row, sticky='w', padx=(0,2))
                channel_dropdown(arg_var1).grid(column=1, row=row, sticky='w', padx=(0,8))
                row += 1
                arg_label2, arg_var2, arg_widget2 = arg2
                ttk.Label(frame, text=arg_label2).grid(column=0, row=row, sticky='w', padx=(0,2))
                arg_widget2(frame, textvariable=arg_var2, width=7).grid(column=1, row=row, sticky='w', padx=(0,8))
                row += 1
                frame.grid_columnconfigure(0, weight=1)
                frame.grid_columnconfigure(1, weight=1)
                ttk.Button(frame, text=label,
                           command=make_cmd_callback()
                          ).grid(column=0, row=row, columnspan=2, pady=4, sticky='ew')
                row += 1
            # For getdac and getid, make button expand to frame width
            elif cmd in {'getdac', 'getid'}:
                frame.grid_columnconfigure(0, weight=1)
                frame.grid_columnconfigure(1, weight=1)
                ttk.Button(frame, text=label,
                           command=make_cmd_callback()
                          ).grid(column=0, row=row, columnspan=2, pady=4, sticky='ew')
                row += 1
            # For other commands with arguments: each arg-label/input on its own line, button below
            elif arg1 or arg2:
                for arg in (arg1, arg2):
                    if arg:
                        arg_label, arg_var, arg_widget = arg
                        ttk.Label(frame, text=arg_label).grid(column=0, row=row, sticky='w', padx=(0,2))
                        if arg_widget == channel_dropdown:
                            arg_widget(arg_var).grid(column=1, row=row, sticky='w', padx=(0,8))
                        else:
                            arg_widget(frame, textvariable=arg_var, width=7).grid(column=1, row=row, sticky='w', padx=(0,8))
                        row += 1
                frame.grid_columnconfigure(0, weight=1)
                frame.grid_columnconfigure(1, weight=1)
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

    add_buttons(board_frame, board_buttons)
    add_buttons(datetime_frame, datetime_buttons)
    add_buttons(dac_frame, dac_buttons)
    add_buttons(volt_frame, volt_buttons)
    add_buttons(temp_frame, temp_buttons)
    add_buttons(id_frame, id_buttons)

    # --- Help button ---
    def show_help():
        help_win = tk.Toplevel(root)
        help_win.title("Help")
        help_text = tk.Text(help_win, wrap="word", width=80, height=20)
        help_text.insert("1.0", HELP_CMD_MSG)
        help_text.config(state="disabled")
        help_text.pack(padx=10, pady=10, fill="both", expand=True)
        ttk.Button(help_win, text="Close", command=help_win.destroy).pack(pady=5)

    ttk.Button(help_frame, text="Help", width=18, command=show_help).pack(pady=2)

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

    start_gui(DummySerial(), dummy_format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID)