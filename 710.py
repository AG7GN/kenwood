#!/usr/bin/env python3
import serial
import sys
import queue
from threading import Thread
import signal
import tkinter as tk
import datetime
import kenwoodTM

version = "1.2.0"
running = True
device = '/dev/ttyUSB0'
baud = 57600
exit_code = 0


def sigint_handler(sig, frame):
    print(f"{stamp()}: Signal handler caught {sig} {frame}")
    global running
    if running:
        running = False
    else:
        cleanup()


def stop_q_reader():
    global running
    running = False


def cleanup():
    print(f"{stamp()}: Start cleanup()")
    global running
    if running:
        running = False
    try:
        q_thread.join(timeout=2)
    except RuntimeError as _:
        print(f"{stamp()}: Thread stopped")
    ser.close()
    root.quit()
    root.update()
    print(f"{stamp()}: cleanup() completed")


def handle_query(cmd: str):
    myscreen.msg.mq.put(['INFO', f"{stamp()}: Sending '{cmd}'"])
    result = mycat.query(cmd)
    if mycat.serial_port_error:
        print(f"{stamp()}: ERROR in handle_query: No response from radio",
              file=sys.stderr)
        global exit_code
        exit_code = 1
        return None
    else:
        return result


def stamp():
    return datetime.datetime.now().strftime('%Y%m%dT%H%M%S')


def q_reader(sq: object):
    def get_arg_list():
        if len(job) > 1 and job[1] in ('A', 'B'):
            _arg = mycat.side_dict['inv'][job[1]]
            _answer = handle_query(f"VM {_arg}")
            if _answer is None:
                return None
            _, _, _m = list(_answer)
            if _m == '0':  # vfo
                cmd = 'FO'
            elif _m == '1':  # mr
                cmd = 'ME'
                _answer = handle_query(f"MR {_arg}")
                if _answer is None:
                    return None
                _arg = _answer[2]  # Get the channel number
            elif _m == '2':  # call
                cmd = 'CC'
            else:  # wx
                return None
            _answer = handle_query(f"{cmd} {_arg}")
            if _answer is None:
                return None
            else:
                return list(_answer)
        else:
            return None

    global running
    current_color = None
    while running:
        if sq.empty():  # queue is empty, so just update screen
            # print("queue empty. update display")
            data = mycat.get_radio_status()
            if mycat.serial_port_error:
                print(f"{stamp()}: q_reader ERROR: Could not retrieve "
                      f"data from radio", file=sys.stderr)
                global exit_code
                exit_code = 1
                break
            if data:
                for s in ('A', 'B'):
                    for key in data[s]:
                        myscreen.screen_label[s][key]. \
                            config(text=data[s][key])
                        myscreen.screen_label[s][key]. \
                            pack(fill=tk.BOTH, expand=True)
                        myscreen.screen_label[s][key].update()
                if current_color != data['backlight']:
                    # Update display to current background color
                    myscreen.change_bg(color=data['backlight'])
                    current_color = data['backlight']
                myscreen.timeout_button.config(text=f"TX Timeout {data['timeout']}")
                myscreen.timeout_button.update()
                myscreen.lock_button.config(text=f"Lock is {data['lock']}")
                myscreen.lock_button.update()
                myscreen.vhf_aip_button.config(text=f"VHF AIP is {data['vhf_aip']}")
                myscreen.vhf_aip_button.update()
                myscreen.uhf_aip_button.config(text=f"UHF AIP is {data['uhf_aip']}")
                myscreen.uhf_aip_button.update()
                myscreen.speed_button.config(text=f"{data['speed']}")
                myscreen.speed_button.update()
                root.update()
            else:  # No response from radio
                root.update()
                break
        else:  # queue not empty. Process the job in the queue
            job = sq.get()  # Get job from queue
            if job[0] == 'quit':
                break
            myscreen.msg.mq.put(['INFO', f"{stamp()}: Working on {job}"])
            if job[0] in ('mode',):  # 'VM' command
                arg = f"VM {mycat.side_dict['inv'][job[1]]},{job[2]}"
                if handle_query(arg) is None:
                    break
            elif job[0] in ('tone', 'tone_frequency'):
                # Get the channel data for current mode (VFO, MR, CALL)
                arg_list = get_arg_list()
                if arg_list is None or arg_list[0] == 'N':
                    break
                same_type = False
                for key, value in mycat.tone_type_dict['map'].items():
                    if arg_list[int(key)] == '1':
                        # Found the current tone type
                        current_type = key
                        if job[0] == 'tone' and job[2] == key:
                            # Requested tone type is the same as current
                            same_type = True
                        break
                else:  # Current type is 'No Tone'
                    current_type = '0'  # No Tone
                    if current_type == job[2]:
                        same_type = True
                if job[0] == 'tone' and not same_type:
                    # Need to change the tone type.
                    # Set all tones to off for now...
                    _, t, c, d = list(mycat.tone_type_dict['map'].keys())
                    arg_list[int(t)] = '0'
                    arg_list[int(c)] = '0'
                    arg_list[int(d)] = '0'
                    if job[2] != '0':
                        # Change to requested tone type
                        arg_list[int(job[2])] = '1'
                        # Also set the tone frequency for the new tone
                        # type to the first dictionary entry for that
                        # type because don't know what the user will
                        # want it to be. Tone frequency is always 3
                        # elements up in the list from the tone type
                        # arg_list[int(job[2]) + 3] = \
                        #     list(mycat.tone_frequency_dict[job[2]]
                        #          ['map'].keys())[0]
                if job[0] == 'tone_frequency' and current_type != '0':
                    arg_list[int(current_type) + 3] = \
                        mycat.tone_frequency_dict[current_type]['inv'][job[2]]
                # Prepare the new command to change tone or tone frequency
                arg = f"{arg_list[0]} {','.join(arg_list[1:])}"
                if handle_query(arg) is None:
                    break
            elif job[0] in ('ptt', 'ctrl'):  # 'BC' command
                answer = handle_query("BC")
                if answer is None:
                    break
                ctrl = answer[1]
                ptt = answer[2]
                if job[0] == 'ptt':
                    arg = f"BC {ctrl},{mycat.side_dict['inv'][job[1]]}"
                else:  # Setting ctrl
                    arg = f"BC {mycat.side_dict['inv'][job[1]]},{ptt}"
                if handle_query(arg) is None:
                    break
            elif job[0] in ('power',):  # 'PC' command
                arg = f"PC {mycat.side_dict['inv'][job[1]]},{job[2]}"
                if handle_query(arg) is None:
                    break
            elif job[0] in ('rev',):
                answer = handle_query(f"AS {mycat.side_dict['inv'][job[1]]}")
                if answer is None:
                    break
                arg = f"AS {mycat.side_dict['inv'][job[1]]},"
                arg += '{}'.format('1' if answer[2] == '0' else '0')
                if handle_query(arg) is None:
                    break
            elif job[0] in ('lock',):
                answer = handle_query("LK")
                if answer is None:
                    break
                arg = "LK {}".format('1' if answer[1] == '0' else '0')
                if handle_query(arg) is None:
                    break
            elif job[0] in ('frequency', 'modulation', 'step'):
                if job[0] == 'frequency':
                    # Change to VFO mode if frequency change was requested
                    arg = f"VM {mycat.side_dict['inv'][job[1]]},0"
                    if handle_query(arg) is None:
                        break
                    _mode = 'vfo'
                arg_list = get_arg_list()  # Get the channel data for current mode
                if arg_list is None or arg_list[0] == 'N':
                    break
                # print(f"PRE:  {arg_list}")
                if job[0] == 'frequency':
                    # Modify the frequency value in the VFO channel info
                    arg_list[2] = f"{int(job[2] * 1000000):010d}"
                if job[0] == 'modulation':
                    arg_list[13] = job[2]
                if job[0] == 'step':
                    arg_list[3] = job[2]
                else:
                    pass
                # print(f"POST: {arg_list}")
                arg = f"{arg_list[0]} {','.join(arg_list[1:])}"
                if handle_query(arg) is None:
                    break
            elif job[0] in ('beep', 'vhf_aip', 'uhf_aip', 'speed',
                            'backlight', 'apo', 'data', 'timeout'):
                # Get the current menu settings
                mu = handle_query('MU')
                if mu is None:
                    break
                mu_list = list(mu)

                if job[0] == 'backlight':
                    if current_color == 'green':
                        desired_color = 'amber'
                    else:
                        desired_color = 'green'
                    mu_list[mycat.menu_dict['backlight']['index']] = \
                        mycat.menu_dict['backlight']['values'][desired_color]
                elif job[0] == 'data':
                    mu_list[38] = job[1]
                elif job[0] == 'speed':
                    mu_list[39] = job[1]
                elif job[0] == 'timeout':
                    mu_list[16] = job[1]
                elif job[0] == 'vhf_aip':
                    mu_list[11] = '0' if mu_list[11] == '1' else '1'
                elif job[0] == 'uhf_aip':
                    mu_list[12] = '0' if mu_list[12] == '1' else '1'
                else:
                    pass
                arg = f"MU {','.join(mu_list[1:])}"
                if handle_query(arg) is None:
                    break
            elif job[0] in ('up', 'down'):
                arg_list = get_arg_list()  # Get the channel data for current mode
                if arg_list is None or arg_list[0] == 'N':
                    break
                if arg_list[0] == 'FO':
                    frequency = int(arg_list[2])
                    step = int(mycat.step_dict['map'][arg_list[3]]) * 1000
                    if job[0] == 'down':
                        step *= -1
                    frequency += step
                    _min = float(myscreen.frequency_limits[job[1]]['min']) * 1000000
                    _max = float(myscreen.frequency_limits[job[1]]['max']) * 1000000
                    # print(f"min = {_min}, max = {_min}")
                    if _min <= frequency <= _max:
                        arg_list[2] = f"{frequency:010d}"
                elif arg_list[0] == 'ME':
                    channel = int(arg_list[1])
                    step = 1
                    if job[0] == 'down':
                        step *= -1
                    channel += step
                    _min = myscreen.memory_limits['min']
                    _max = myscreen.memory_limits['max']
                    if _min <= channel <= _max:
                        arg_list.clear()
                        arg_list = ['MR', '0' if job[1] == 'A' else '1',
                                    f"{channel:03d}"]
                else:
                    pass
                arg = f"{arg_list[0]} {','.join(arg_list[1:])}"
                _ans = handle_query(arg)
                if _ans is None:
                    break
                elif arg_list[0] == 'MR' and _ans[0] == 'N':
                    myscreen.msg.mq.put(['ERROR',
                                         f"{stamp()}: Memory "
                                         f"{channel} is empty"])
            elif job[0] in ('ch_number',):
                arg_list = get_arg_list()  # Get the channel data for current mode
                if arg_list is None or arg_list[0] == 'N':
                    break
                if arg_list[0] == 'ME':
                    arg = f"MR {'0' if job[1] == 'A' else '1'},{job[2]}"
                    _ans = handle_query(arg)
                    if _ans is None:
                        break
                    elif _ans[0] == 'N':
                        myscreen.msg.mq.put(['ERROR',
                                             f"{stamp()}: Memory "
                                             f"{int(job[2])} is empty"])
            elif job[0] in ('micup', 'micdown',):
                if job[0] == 'micup':
                    arg = "UP"
                else:
                    arg = "DW"
                if handle_query(arg) is None:
                    break
            else:
                pass
            sq.task_done()
            # print(f'{stamp()}: Finished {job}')
            myscreen.msg.mq.put(['INFO', f"{stamp()}: Finished {job}"])
    print(f"{stamp()}: Leaving q_reader thread")
    cleanup()


if __name__ == "__main__":
    import argparse
    from serial.tools import list_ports

    signal.signal(signal.SIGINT, sigint_handler)
    parser = argparse.ArgumentParser(description="CAT control for Kenwood TM-D710G/TM=V71A")

    parser.add_argument('-v', '--version', action='version',
                        version=f"Version: {version}")
    parser.add_argument("-p", "--port",
                        choices=[comport.device for comport
                                 in serial.tools.list_ports.comports()],
                        type=str, default=device,
                        help="Serial port connected to radio")
    # parser.add_argument("-p", "--port",
    #                     choices=serialportlist.serial_ports(),
    #                     type=str, default=device,
    #                     help="Serial port")
    parser.add_argument("-b", "--baudrate",
                        choices=[300, 1200, 2400, 4800, 9600, 19200,
                                 38400, 57600],
                        type=int, default=baud,
                        help="Serial port speed (must match radio)")
    parser.add_argument("-c", "--command",
                        type=str, help="CAT command to send to radio (no GUI)")
    arg_info = parser.parse_args()
    if not arg_info.command:
        print(f"{stamp()}: Using {arg_info.port} @ {arg_info.baudrate} bps")

    try:
        ser = serial.Serial(arg_info.port, arg_info.baudrate, timeout=0.1,
                            writeTimeout=0.1)
    except serial.serialutil.SerialException:
        print(f"{stamp()}: ERROR: Could not open serial port",
              file=sys.stderr)
        sys.exit(1)
    mycat = kenwoodTM.KenwoodTMCat(ser)

    if arg_info.command:
        query_answer = mycat.query(arg_info.command)
        if query_answer:
            print(f"{query_answer[0]} {','.join(query_answer[1:])}")
            sys.exit(0)
        else:
            print(f"{stamp()}: ERROR: Could not communicate with radio.",
                  file=sys.stderr)
            sys.exit(1)

    root = tk.Tk()
    q = queue.Queue()
    myscreen = kenwoodTM.KenwoodTMScreen(root, version, q)

    # Commands to verify we can communicate with the radio. If all work,
    # then there's a good chance the port isn't in use by another app
    test_queries = ('MS', 'AE', 'ID')
    for test in test_queries:
        query_answer = mycat.query(test)
        if not query_answer:
            print(f"{stamp()}: ERROR: Could not communicate with radio.")
            sys.exit(1)
    print(f"{stamp()}: Found {query_answer[1]}")
    myscreen.msg.mq.put(['INFO', f"{stamp()}: Found {query_answer[1]}"])
    q_thread = Thread(target=q_reader, args=(q,))
    q_thread.start()

    # root.bind('<Escape>', lambda e: cleanup())
    # Stop program if Esc key pressed
    # root.bind('<Escape>', lambda e: signal.raise_signal(signal.SIGINT))
    root.bind('<Escape>', lambda e: stop_q_reader())
    # Stop program if window is closed at OS level ('X' in upper right
    # corner or red dot in upper left on Mac)
    # root.protocol("WM_DELETE_WINDOW",
    #               lambda: signal.raise_signal(signal.SIGINT))
    root.protocol("WM_DELETE_WINDOW",
                  lambda: stop_q_reader())
    print(f"{stamp()}: Starting mainloop")
    root.mainloop()
    print(f"{stamp()}: Mainloop stopped")
    sys.exit(exit_code)
