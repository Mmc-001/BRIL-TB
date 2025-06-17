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
    frm = ttk.Frame(root, padding=10)
    frm.grid()
    row = 0

    def channel_dropdown(var):
        return ttk.OptionMenu(frm, var, 'a', *DAC_CHANNELS_ID.keys())

    # Button definitions: (label, command, [arg1_label, arg1_var, arg1_widget], [arg2_label, arg2_var, arg2_widget])
    buttons = [
        ("Get status", 'getstatus', None, None),
        ("Get data", 'getdata', None, None),
        ("Set date (now)", 'setdate', None, None),
        ("Set time (now)", 'settime', None, None),
        ("Get date and time", 'getdatetime', None, None),
        ("Get DAC", 'getdac', None, None),
        ("Get ID", 'getid', None, None),
        ("Get temperature", 'gettemp', None, None),
        ("Reset", 'reset', None, None),
        ("Get configuration", 'getconf', None, None),
        # Argument commands start here
        ("Set DAC", 'setdac', ("Channel:", tk.StringVar(value='a'), channel_dropdown), ("Thr (V):", tk.StringVar(), ttk.Entry)),
        ("Set ID", 'setid', ("New ID:", tk.StringVar(), ttk.Entry), None),
        ("Set overV", 'setoverv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
        ("Set underV", 'setundv', ("Thr (V):", tk.StringVar(), ttk.Entry), None),
        ("Set overTemp", 'setovert', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
        ("Set underTemp", 'setundt', ("Thr (°C):", tk.StringVar(), ttk.Entry), None),
    ]

    # Store references to StringVars for clearing
    button_vars = []

    for label, cmd, arg1, arg2 in buttons:
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

        ttk.Button(frm, text=label, width=14,
                   command=make_cmd_callback()
                  ).grid(column=0, row=row, pady=2, sticky='w')
        col = 1
        for arg in (arg1, arg2):
            if arg:
                arg_label, arg_var, arg_widget = arg
                ttk.Label(frm, text=arg_label).grid(column=col, row=row)
                if arg_widget == channel_dropdown:
                    arg_widget(arg_var).grid(column=col+1, row=row)
                else:
                    arg_widget(frm, textvariable=arg_var, width=7).grid(column=col+1, row=row)
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