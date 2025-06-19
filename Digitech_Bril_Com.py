
import serial
import threading
import time
import datetime
import digitech_gui
#import digitech_gui_v2



# Configure serial port
SERIAL_PORT = 'COM6'#Change to your port, e.g., '/dev/ttyUSB0' on Linux
# PC ANET: COM4 (USB destra)
# Mini PC: COM6 (USB bassa lato alimentazione)
BAUD_RATE = 115200
OUTPUT_FILE = 'received_data.txt'
CTRL_LOG_FILE = 'command_log.txt'

PERIODIC_TRIGGER_PERIOD = 20        #seconds


BOARD_ID_OFFSET = 33
BOARD__MAGIC_ID = 100 -BOARD_ID_OFFSET #a message with BOARD MAGIC ID is processed by the board wathever its actual id
BOARD_DEFAULT_ID = 0 # 
BOARD_ID = BOARD_DEFAULT_ID


BOARD_ID_BYTE = bytes.fromhex(hex(BOARD_ID + BOARD_ID_OFFSET)[2:])
CMD_TERMINATOR = bytes.fromhex('0a')

DAC_REF_VOLTAGE = 3
DAC_MAX_N = 1023



HELP_CMD_MSG = """
USER INPUT       \t     Description	        Arguments     \n
========================================================= \n
    getStatus    \t		Get Status		         --       \n
    getData      \t		Get Data		         --       \n
    SetDate      \t		Set Date		         --       \n
    SetTime      \t		Set Time		         --       \n
    getDateTime  \t		Get Date and Time	     --       \n
    getDAC       \t		Get DAC Threshold	     --       \n
    setDAC       \t		Set DAC Threshold	CHID thr_V    \n
    getID        \t		Get Board ID		              \n
    setID        \t		Set Board ID		   newID      \n
    getTemp      \t		Get Temperature		\n
    reset        \t		Soft Reset		   \n
"""


DAC_CHANNELS_ID = {
        'a' : bytes([ord("a")]),
        'b' : bytes([ord("b")]),
        'c' : bytes([ord("c")]),
        'd' : bytes([ord("d")]),
        'e' : bytes([ord("e")]),
        'f' : bytes([ord("f")]),
        'g' : bytes([ord("g")]),
        'h' : bytes([ord("h")])
        }



#Thread for serial read and log
def read_from_serial(ser):
    
    with open(OUTPUT_FILE, 'a') as file, open(CTRL_LOG_FILE,'a') as ctrl_file:
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    cur_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S");
                    print("["+cur_time+"] \t"+f"{line}")
                    if(line[0] == '>'): #control line
                        ctrl_file.write(cur_time+"\t"+line + '\n')
                        ctrl_file.flush()
                    else:               #data line
                        file.write(cur_time+"\t"+line + '\n')
                        file.flush()

            time.sleep(0.1)

"""
USER INPUT    OPCODE              Description
=========================================
    getStatus     a (0x61)	 Get Status		    
    getData       b (0x62)	 Get Data		    
    SetDate       c (0x63)	 Set Date		    
    SetTime       d (0x64)	 Set Time		    
    getDateTime   e (0x65)	 Get Date and Time	
    getDAC        f (0x66)	 Get DAC Threshold	
    setDAC        g (0x67)	 Set DAC Threshold	
    getTemp       h (0x68)	 Get Temperature		
    reset        i (0x69)	 Soft Reset		    
    setID        j (0x6a)	 Set Board ID		
    getID        k (0x6b)	 Set Board ID	
    setoverv     l           Set Over Voltage Threshold
    setundv      m           Set UnderVoltage Threshold
    setovert     n           Set Overtemperature Threshold
    setundt      o           Set Undergemperature Threshold
    getconf      p           Get Voltage and Temp ThresholdConfiguration    
    help        (--local)    Print this help message	


"""

#function for formatting command
def format_command(cmd_char, payload):
    
    command_map = {
        'getstatus' : lambda p:     BOARD_ID_BYTE+bytes([ord("a")])+CMD_TERMINATOR,
        'getdata'   : lambda p:     BOARD_ID_BYTE+bytes([ord("b")])+CMD_TERMINATOR,
        'setdate'   : lambda p:     BOARD_ID_BYTE+bytes([ord("c")])+p+CMD_TERMINATOR,
        'settime'   : lambda p:     BOARD_ID_BYTE+bytes([ord("d")])+p+CMD_TERMINATOR,
        'getdatetime':lambda p:     BOARD_ID_BYTE+bytes([ord("e")])+CMD_TERMINATOR,
        'getdac'    : lambda p:     BOARD_ID_BYTE+bytes([ord("f")])+CMD_TERMINATOR,
        'setdac'    : lambda p:     BOARD_ID_BYTE+bytes([ord("g")])+p+CMD_TERMINATOR,
        'gettemp'   : lambda p:     BOARD_ID_BYTE+bytes([ord("h")])+CMD_TERMINATOR,
        'reset'     : lambda p:     BOARD_ID_BYTE+bytes([ord("i")])+CMD_TERMINATOR,
        'setid'     : lambda p:     BOARD_ID_BYTE+bytes([ord("j")])+p+CMD_TERMINATOR,
        'getid'     : lambda p:     BOARD_ID_BYTE+bytes([ord("k")])+CMD_TERMINATOR,
        'setoverv'  : lambda p:     BOARD_ID_BYTE+bytes([ord("l")])+p+CMD_TERMINATOR,
        'setundv'   : lambda p:     BOARD_ID_BYTE+bytes([ord("m")])+p+CMD_TERMINATOR,
        'setovert'  : lambda p:     BOARD_ID_BYTE+bytes([ord("n")])+p+CMD_TERMINATOR,
        'setundt'   : lambda p:     BOARD_ID_BYTE+bytes([ord("o")])+p+CMD_TERMINATOR,
        'getconf'   : lambda p:     BOARD_ID_BYTE+bytes([ord("p")])+CMD_TERMINATOR,
    }
    formatter = command_map.get(cmd_char.lower())
    if formatter:
        return formatter(payload)
    else:
        return None



#thread for periodically triggering data messages
def periodic_trigger_msg(ser,period):
    print("Start collecting data in 10s")
    time.sleep(10)
    while True:
        time.sleep(0.1) #wait 100 ms for alignment
        try:
            formatted = format_command('getdata',0)
            if (formatted):
                ser.write(formatted)
        except:
            print("Error Periodic trigger")
        time.sleep(PERIODIC_TRIGGER_PERIOD)




#Thread for listen user inputs and send commands to board
def listen_for_commands(ser):
    while True:
        try:
            print("\nEnter \"help\" for command list")
            command = input("[Command] Enter command (format command payload): ").strip()

            #check user input
            if len(command) >= 2 and command[0].isalpha():
                cmd = command.split()[0].lower()

                # GET ID
                if cmd == 'getstatus':
                    formatted = format_command(cmd,0)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                         print(f"[Error] Invalid command ({cmd}). Example: getstatus")

                #GET DATA
                elif cmd == 'getdata':
                    formatted = format_command(cmd,0)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                        print(f"[Error] Invalid command ({cmd}). Example: getdata")

                #GET DATE AND TIME
                if cmd == 'getdatetime':
                    formatted = format_command(cmd,0)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                        print(f"[Error] Invalid command ({cmd}). Example: getdatetime")
                
                #SET TIME
                elif cmd == 'settime':
                    date = datetime.datetime.now()
                    payload = date.strftime("%H%M%S")
                    payload = bytes(payload,"ascii")
                    formatted = format_command(cmd,payload)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                        print(f"[Error] Invalid command ({cmd}). Example: settime")
                
                #SET DATE
                elif cmd == 'setdate':
                    date = datetime.datetime.now()
                    payload = date.strftime("%d%m%Y")
                    payload = bytes(payload,"ascii")
                    formatted = format_command(cmd,payload)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                        print(f"[Error] Invalid command ({cmd}). Example: setdate")

                #SET DAC THR
                if cmd == 'setdac':
                    try:
                        dac_channel_str = command.split()[1].lower()
                        #get desired DAC channel from command ("a","b",..."h")
                        payload = DAC_CHANNELS_ID.get(dac_channel_str)
                        #get desired Voltage value in V
                        thr_v = float(command.split()[2])
                        #convert desired Voltage value to mV
                        thr_n = int(thr_v*1000)
                        # get the corresponding ascii string
                        thr_k = int(thr_n/1000)
                        thr_h = int((thr_n%1000)/100)
                        thr_d = int((thr_n%100)/10)
                        thr_u = int((thr_n%10))
                        thr_str = str(thr_k)+str(thr_h)+str(thr_d)+str(thr_u)
                        #get the final command string 
                        payload = payload + bytes(thr_str,"ascii")
                        formatted = format_command(cmd,payload)
                        if formatted:
                            ser.write(formatted)
                            print(f"[Sent] {formatted}")
                        else:
                            print(f"[Error] Invalid command ({cmd}). Example: setdac a 1.3")

                    except:
                        print('Error in conversion')
                    
                
                #GET DAC THR
                if cmd == 'getdac':
                    formatted = format_command(cmd,0)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                        print(f"[Error] Invalid command ({cmd}). Example: getdac")

                #GET Temp
                if cmd == 'gettemp':
                    formatted = format_command(cmd,0)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                        print(f"[Error] Invalid command ({cmd}). Example: getdac")

                #RESET
                elif cmd == 'reset':
                    formatted = format_command(cmd,0)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                        print(f"[Error] Invalid command ({cmd}). Example: reset")

                #SET ID
                elif cmd == 'setid':
                    try:
                        num = command.split()[1]

                        if((int(num) < 62) or (int(num) == BOARD__MAGIC_ID)):    
                            num = int(num)+33 #offset ascii table
                            #payload = bytes.fromhex(hex(num)[2:])
                            payload = chr(num).encode('ASCII')
                            formatted = format_command(cmd,payload)
                            if formatted:
                                ser.write(formatted)
                                print(f"[Sent] {formatted}")
                        else:
                            print(f"[Error] Maximum id = 63 ({cmd}). Example: setid 23")
                    except:
                         print(f"[Error] Invalid command ({cmd}). Example: setid 23")

                # GET ID
                elif cmd == 'getid':
                    formatted = format_command(cmd,0)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                         print(f"[Error] Invalid command ({cmd}). Example: getid")

                #SET OVERV
                elif cmd == 'setoverv':
                    try:
                        overv_str = command.split()[1].lower()
                        thr_n = int(float(overv_str)*1000 )
                        thr_dk = int(thr_n/10000)
                        thr_k = int((thr_n%10000)/1000)
                        thr_h = int((thr_n%1000)/100)
                        thr_d = int((thr_n%100)/10)
                        thr_u = int((thr_n%10))
                        thr_str = str(thr_dk)+str(thr_k)+str(thr_h)+str(thr_d)+str(thr_u)
                        payload =  bytes(thr_str,"ascii")
                        formatted = format_command(cmd,payload)
                        if formatted:
                            ser.write(formatted)
                            print(f"[Sent] {formatted}")
                        else:
                            print(f"[Error] Invalid command ({cmd}). Example: setdac")

                    except:
                        print('Error in conversion')
                

                #SET OVERV
                elif cmd == 'setundv':
                    try:
                        undv_str = command.split()[1].lower()
                        thr_n = int(float(undv_str)*1000 )
                        thr_dk = int(thr_n/10000)
                        thr_k = int((thr_n%10000)/1000)
                        thr_h = int((thr_n%1000)/100)
                        thr_d = int((thr_n%100)/10)
                        thr_u = int((thr_n%10))
                        thr_str = str(thr_dk)+str(thr_k)+str(thr_h)+str(thr_d)+str(thr_u)
                        payload =  bytes(thr_str,"ascii")
                        formatted = format_command(cmd,payload)
                        if formatted:
                            ser.write(formatted)
                            print(f"[Sent] {formatted}")
                        else:
                            print(f"[Error] Invalid command ({cmd}). Example: setdac")

                    except:
                        print('Error in conversion')

                #SET OVERV
                elif cmd == 'setovert':
                    try:
                        overt_str = command.split()[1].lower()
                        thr_n = int(float(overt_str)*100 )
                        thr_sign = '+'
                        if (thr_n <0):
                            thr_sign = '-'
                        thr_n = abs(thr_n)
                        thr_k = int(thr_n/1000)
                        thr_h = int((thr_n%1000)/100)
                        thr_d = int((thr_n%100)/10)
                        thr_u = int((thr_n%10))
                        thr_str = thr_sign+str(thr_k)+str(thr_h)+str(thr_d)+str(thr_u)
                        payload =  bytes(thr_str,"ascii")
                        formatted = format_command(cmd,payload)
                        if formatted:
                            ser.write(formatted)
                            print(f"[Sent] {formatted}")
                        else:
                            print(f"[Error] Invalid command ({cmd}). Example: setovert 50.5")

                    except:
                        print('Error in conversion')
                
                #SET UNDERTEMPERATURE
                elif cmd == 'setundt':
                    try:
                        overt_str = command.split()[1].lower()
                        thr_n = int(float(overt_str)*100 )
                        thr_sign = '+'
                        if (thr_n <0):
                            thr_sign = '-'
                        thr_n = abs(thr_n)
                        thr_k = int(thr_n/1000)
                        thr_h = int((thr_n%1000)/100)
                        thr_d = int((thr_n%100)/10)
                        thr_u = int((thr_n%10))
                        thr_str = thr_sign+str(thr_k)+str(thr_h)+str(thr_d)+str(thr_u)
                        payload =  bytes(thr_str,"ascii")
                        formatted = format_command(cmd,payload)
                        if formatted:
                            ser.write(formatted)
                            print(f"[Sent] {formatted}")
                        else:
                            print(f"[Error] Invalid command ({cmd}). Example: setundt -5.5")

                    except:
                        print('Error in conversion')

                #GET CONFIG
                elif cmd == 'getconf':
                    formatted = format_command(cmd,0)
                    if formatted:
                        ser.write(formatted)
                        print(f"[Sent] {formatted}")
                    else:
                         print(f"[Error] Invalid command ({cmd}). Example: getconf")
                

                elif cmd == 'help':
                    print(HELP_CMD_MSG)

            else:
                print(HELP_CMD_MSG)
        except KeyboardInterrupt:
            print("\n[Info] Command input stopped.")
            break


#Program entry point
def main():
    trigger_period = 10
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser, open(OUTPUT_FILE, 'a') as file:
            print(f"Listening on {SERIAL_PORT} at {BAUD_RATE} baud...")
            threading.Thread(target=read_from_serial, args=(ser,), daemon=True).start()
            threading.Thread(target=periodic_trigger_msg, args=(ser,trigger_period), daemon=True).start()
            # Start GUI in a separate thread, passing required objects
            # threading.Thread(
                # target=digitech_gui.start_gui,
                # args=(ser, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID),
                # daemon=True
            # ).start()
            # listen_for_commands(ser)
            threading.Thread(target=listen_for_commands, args=(ser,), daemon=True).start()
            digitech_gui.start_gui(ser, format_command, DAC_CHANNELS_ID, BOARD__MAGIC_ID)
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == '__main__':
    main()
