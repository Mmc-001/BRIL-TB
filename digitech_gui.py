import tkinter as tk
from tkinter import ttk

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
    # Create two main frames for two columns
    left_frame = ttk.Frame(root, padding=10)
    right_frame = ttk.Frame(root, padding=10)
    left_frame.grid(row=0, column=0, sticky='n')
    right_frame.grid(row=0, column=1, sticky='n')

    def channel_dropdown(var):
        return ttk.OptionMenu(right_frame, var, 'a', *DAC_CHANNELS_ID.keys())

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
        ("Set DAC", 'setdac', ("Channel:", tk.StringVar(value='a'), channel_dropdown), ("Thr (V):", tk.StringVar(), ttk.Entry)),
        ("Set ID", 'setid', ("New ID:", tk.StringVar(), ttk.Entry), None),
        ("Set overV", 'setoverv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
        ("Set underV", 'setundv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
        ("Set overTemp", 'setovert', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
        ("Set underTemp", 'setundt', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
    ]

    # Store references to StringVars for clearing
    button_vars = []

    # Place no-argument buttons in left_frame
    row = 0
    for label, cmd, arg1, arg2 in no_arg_buttons:
        def make_cmd_callback(c=cmd, a1=arg1, a2=arg2):
            def callback():
                send(c,
                     a1[1].get() if a1 else None,
                     a2[1].get() if a2 else None)
            return callback
        ttk.Button(left_frame, text=label, width=18,
                   command=make_cmd_callback()
                  ).grid(column=0, row=row, pady=2, sticky='w')
        row += 1

    # Place argument buttons in right_frame
    row = 0
    for label, cmd, arg1, arg2 in arg_buttons:
        def make_cmd_callback(c=cmd, a1=arg1, a2=arg2):
            def callback():
                send(c,
                     a1[1].get() if a1 else None,
                     a2[1].get() if a2 else None)
                # Reset fields for numeric threshold commands
                if c in {'setdac', 'setoverv', 'setundv', 'setovert', 'setundt', 'setid'}:
                    if a1: a1[1].set('')
                    if a2: a2[1].set('')
            return callback
        ttk.Button(right_frame, text=label, width=18,
                   command=make_cmd_callback()
                  ).grid(column=0, row=row, pady=2, sticky='w')
        col = 1
        for arg in (arg1, arg2):
            if arg:
                arg_label, arg_var, arg_widget = arg
                ttk.Label(right_frame, text=arg_label).grid(column=col, row=row)
                if arg_widget == channel_dropdown:
                    arg_widget(arg_var).grid(column=col+1, row=row)
                else:
                    arg_widget(right_frame, textvariable=arg_var, width=7).grid(column=col+1, row=row)
                col += 2
        row += 1

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