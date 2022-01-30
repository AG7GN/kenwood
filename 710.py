#!/usr/bin/env python3
"""
Implements a GUI that allows the user to control some functions of the
Kenwood TM-D710G and TM-V71A radios.
"""
import serial
import os
import re
import sys
from queue import Queue
from threading import Thread
import signal
import tkinter as tk
from common710 import stamp
from common710 import QueryException
from cat710 import Cat
from gui710 import Display
from xmlrpc710 import RigXMLRPC

__title__ = "710.py"
__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2022, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "2.0.1"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"
running = True
device = '/dev/ttyUSB0'
baud = 57600
xmlrpc_port = 12345
exit_code = 0


def print_error(err: str):
    """
    If X windows environment detected, pop up a window with
    the message, otherwise print error to the console (stderr).
    :param err: String containing error message
    :return: None
    """
    if os.environ.get('DISPLAY', '') == '':
        print(f"{stamp()}: {err}", file=sys.stderr)
    else:
        from tkinter import messagebox
        try:
            root.withdraw()
        except NameError as e:
            # root window hasn't been created yet. Make a new root
            # for messagebox
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror(title=f"{__title__} ERROR!", message=err,
                                 parent=error_root)
            error_root.destroy()
        else:
            # Root window exists. Use it for messagebox.
            messagebox.showerror(title=f"{__title__} ERROR!", message=err)


def sigint_handler(sig, frame):
    # print(f"{stamp()}: Signal handler caught {sig} {frame}")
    cleanup()


def cleanup():
    print(f"{stamp()}: Starting cleanup")
    global running
    if running:
        running = False
    try:
        controller_thread.join(timeout=2)
    except RuntimeError as _:
        print(f"{stamp()}: Controller thread stopped")
    if xmlrpc_server:
        print(f"{stamp()}: Stopping XML-RPC server")
        xmlrpc_server.stop()
        xmlrpc_thread.join(timeout=1)
    ser.close()
    print(f"{stamp()}: Cleanup completed")
    if root:
        root.quit()
        root.update()


def get_ports():
    """
    Walks /dev searching for paths with filenames or symlinks to
    filenames containing ^tty(AMA[0-9]|S[0-9]|USB[0-9]).
    Returns a list of matching paths, or empty list if there are
    no matches.
    """
    ports = []
    excludes = ["char", "by-path"]
    for _root, dirs, files in os.walk('/dev'):
        dirs[:] = [dirname for dirname in dirs if dirname not in excludes]
        for filename in files:
            path = os.path.join(_root, filename)
            if os.path.islink(path):  # Found a symlink
                target_path = os.readlink(path)
                # Resolve relative symlinks
                if not os.path.isabs(target_path):
                    target_path = os.path.join(os.path.dirname(path),
                                               target_path)
                if os.path.exists(target_path) and \
                        re.match('^tty(AMA[0-9]|S[0-9]|USB[0-9]|.usbserial)',
                                 os.path.basename(os.readlink(path))):
                    ports.append(path)
            elif re.match('^tty(AMA[0-9]|S[0-9]|USB[0-9]|.usbserial)', filename):
                # Not a symlink. Look for the usual serial port names and add them to list
                ports.append(path)
            else:  # Not interested in anything else
                continue
    return ports


def controller():
    """
    Updates the display while looking for and handling commands.
    :return: None
    """
    global running
    print(f"{stamp()}: Starting controller")
    while running:
        if cmd_queue.empty():
            try:
                rig_dictionary = rig.update_dictionary()
            except IndexError as e:
                print_error(f"Error communicating with radio on {arg_info.port}")
                running = False
                break
            if rig_dictionary is None:
                running = False
                break
            else:
                gui.update_display(rig_dictionary)
                if root:
                    root.update()
        else:
            job = cmd_queue.get()  # Get job from queue
            if job[0] == 'quit':
                break
            msg_queue.put(['INFO', f"{stamp()}: Queued {job}"])
            result = rig.run_job(job, msg_queue)
            if result is None:
                running = False
            else:
                msg_queue.put(['INFO', f"{stamp()}: Finished {job}"])
            cmd_queue.task_done()
    print(f"{stamp()}: Controller stopped")
    cleanup()


if __name__ == "__main__":
    import argparse

    port_list = get_ports()
    if not port_list:
        # print(f"{stamp()}: ERROR: No serial ports found.",
        #       file=sys.stderr)
        print_error(f"No serial ports found.")
        sys.exit(1)
    if device not in port_list:
        device = port_list[0]
    signal.signal(signal.SIGINT, sigint_handler)
    parser = argparse.ArgumentParser(prog=__title__,
                                     description=f"CAT control for Kenwood TM-D710G/TM-V71A",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version',
                        version=f"Version: {__version__}")
    parser.add_argument("-p", "--port",
                        choices=port_list,
                        type=str, default=device,
                        help="Serial port connected to radio")
    parser.add_argument("-b", "--baudrate",
                        choices=[300, 1200, 2400, 4800, 9600, 19200,
                                 38400, 57600],
                        type=int, default=baud,
                        help="Serial port speed (must match radio)")
    parser.add_argument("-s", "--small", action='store_true',
                        help="Smaller GUI window")
    parser.add_argument("-l", "--location", type=str, metavar="x:y",
                        help="x:y: Initial x and y position (in pixels) "
                             "of upper left corner of GUI.")
    parser.add_argument("-x", "--xmlport", type=int,
                        choices=range(1024, 65536),
                        metavar="[1024-65535]", default=xmlrpc_port,
                        help="TCP port on which to listen for "
                             "XML-RPC rig control calls from "
                             "clients such as Fldigi or Hamlib")
    parser.add_argument("-r", "--rig", type=str,
                        choices=('none', 'left', 'right'),
                        default='none',
                        help="Nexus DR-X Users: Select left or right "
                             "radio if you want to control GPIO PTT via "
                             "an XML-RPC 'rig.set_ptt' call. This will "
                             "map to GPIO pin 12 for the left radio and "
                             "pin 23 for the right. 'none' "
                             "means that 'rig.set_ptt' calls will be ignored. "
                             "In any case, PTT activation via CAT command "
                             "is never used.")
    parser.add_argument("-c", "--command",
                        type=str, help="CAT command to send to radio (no GUI)")
    arg_info = parser.parse_args()
    if not arg_info.command:
        print(f"{stamp()}: Opening {arg_info.port} @ {arg_info.baudrate} bps",
              file=sys.stderr)

    try:
        ser = serial.Serial(arg_info.port, arg_info.baudrate, timeout=0.1,
                            writeTimeout=0.1)
    except serial.serialutil.SerialException:
        # print(f"{stamp()}: ERROR: Could not open serial port",
        #       file=sys.stderr)
        print_error(f"Could not open {arg_info.port}")
        sys.exit(1)
    cmd_queue = Queue()
    rig = Cat(ser, arg_info.rig)
    if arg_info.command:
        query_answer = rig.handle_query(arg_info.command)
        if query_answer:
            print(f"{query_answer[0]} {','.join(query_answer[1:])}")
            sys.exit(0)
        else:
            # print(f"{stamp()}: ERROR: Could not communicate with radio.",
            #       file=sys.stderr)
            print_error(f"Could not communicate with radio on {arg_info.port}.")
            sys.exit(1)

    if os.environ.get('DISPLAY', '') == '':
        print(f"No $DISPLAY environment. "
              f"Only '-c' option works without X", file=sys.stderr)
        sys.exit(1)
        # os.environ.__setitem__('DISPLAY', ':0.0')

    if arg_info.small:
        size = 'small'
    else:
        size = 'normal'

    root = tk.Tk()

    loc = None
    if arg_info.location:
        loc = arg_info.location.split(':')
        try:
            x_loc = int(loc[0])
            y_loc = int(loc[1])
        except (ValueError, IndexError):
            print(f"{stamp()}: '{arg_info.location}' is an invalid "
                  f"screen position. Using defaults instead.",
                  file=sys.stderr)
            loc = None
        else:
            y_max = root.winfo_screenheight()
            x_max = root.winfo_screenwidth()
            if 0 <= x_loc < x_max - 100 and 0 <= y_loc < y_max - 100:
                loc = (x_loc, y_loc)
            else:
                print(f"{stamp()}: '{arg_info.location}' is an invalid "
                      f"screen position. Using defaults instead.",
                      file=sys.stderr)
                loc = None
    # Commands to verify we can communicate with the radio. If all work,
    # then there's a good chance the port isn't in use by another app
    test_queries = ('MS', 'AE', 'ID')
    for test in test_queries:
        query_answer = rig.handle_query(test)
        if not query_answer:
            # print(f"{stamp()}: ERROR: Could not communicate with radio.")
            print_error(f"Could not communicate with "
                        f"radio on {arg_info.port}")
            sys.exit(1)
    print(f"{stamp()}: Found {query_answer[1]}", file=sys.stderr)
    rig.set_id(query_answer[1])

    # Set up XML-RPC server and corresponding thread.
    try:
        xmlrpc_server = RigXMLRPC(arg_info.xmlport, rig, cmd_queue)
    except OSError as error:
        # print(f"ERROR: XML-RPC port {arg_info.xmlport} is already in use")
        print_error(f"XML-RPC port {arg_info.xmlport} is already in use.\n\n"
                    f"Is Flrig running? Close it before running {__title__}.")
        ser.close()
        sys.exit(1)
    xmlrpc_thread = Thread(target=xmlrpc_server.start)
    # Kill this thread when the main app terminates
    xmlrpc_thread.setDaemon(True)

    # Set up the GUI
    msg_queue = Queue()
    gui = Display(root=root, version=__version__,
                  cmd_queue=cmd_queue, msg_queue=msg_queue,
                  size=size, initial_location=loc)
    msg_queue.put(['INFO', f"{stamp()}: Found {query_answer[1]}"])
    controller_thread = Thread(target=controller)
    controller_thread.start()

    # Wait until radio is read and state dictionary to be populated
    # before starting the XML-RPC server so we have something to serve
    while rig.get_dictionary()['speed'] is None:
        pass
    print(f"{stamp()}: Starting XML-RPC server", file=sys.stderr)
    xmlrpc_thread.start()

    # Stop program if Esc key pressed
    root.bind('<Escape>', lambda e: cleanup())
    # Stop program if window is closed at OS level ('X' in upper right
    # corner or red dot in upper left on Mac)
    root.protocol("WM_DELETE_WINDOW",
                  lambda: cleanup())
    print(f"{stamp()}: Starting mainloop", file=sys.stderr)
    root.mainloop()
    print(f"{stamp()}: Mainloop stopped", file=sys.stderr)
    # SIGTERM is necessary if there's a connected TCP socket
    this_process = os.getpid()
    os.kill(this_process, signal.SIGTERM)
