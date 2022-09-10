#!/usr/bin/env python3
"""
Implements a GUI that allows the user to control some functions of the
Kenwood TM-D710G and TM-V71A radios.
"""
import serial
import os
import re
import sys
import signal
import tkinter as tk
from common710 import stamp
from common710 import XMLRPC_PORT
from common710 import GPIO_PTT_DICT
from controller710 import Controller

__title__ = "710.py"
__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2022, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "2.1.5"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"
DEVICE = '/dev/ttyUSB0'
BAUD = 57600


def sigint_handler(_, __):
    # print(f"{stamp()}: Signal handler caught {sig} {frame}")
    cleanup()


def cleanup():
    if controller:
        controller.stop()


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


if __name__ == "__main__":
    import argparse

    port_list = get_ports()
    if not port_list:
        # print(f"{stamp()}: ERROR: No serial ports found.",
        #       file=sys.stderr)
        print(f"{stamp()}: No serial ports found.", file=sys.stderr)
        sys.exit(1)
    if DEVICE not in port_list:
        DEVICE = port_list[0]
    signal.signal(signal.SIGINT, sigint_handler)
    parser = argparse.ArgumentParser(prog=__title__,
                                     description=f"CAT control for Kenwood TM-D710G/TM-V71A",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version',
                        version=f"Version: {__version__}")
    parser.add_argument("-p", "--port",
                        choices=port_list,
                        type=str, default=DEVICE,
                        help="Serial port connected to radio")
    parser.add_argument("-b", "--baudrate",
                        choices=[300, 1200, 2400, 4800, 9600, 19200,
                                 38400, 57600],
                        type=int, default=BAUD,
                        help="Serial port speed (must match radio)")
    parser.add_argument("-s", "--small", action='store_true',
                        help="Smaller GUI window")
    parser.add_argument("-l", "--location", type=str, metavar="x:y",
                        help="x:y: Initial x and y position (in pixels) "
                             "of upper left corner of GUI.")
    parser.add_argument("-x", "--xmlport", type=int,
                        choices=range(1024, 65536),
                        metavar="[1024-65535]", default=XMLRPC_PORT,
                        help="TCP port on which to listen for "
                             "XML-RPC rig control calls from "
                             "clients such as Fldigi or Hamlib")
    parser.add_argument("-r", "--rig", type=str,
                        choices=list(GPIO_PTT_DICT.keys()),
                        default='none',
                        help="BCM GPIO pin number for PTT control. "
                             "Nexus DR-X Users: Select left or right "
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
        print(f"{stamp()}: Could not open {arg_info.port}", file=sys.stderr)
        sys.exit(1)

    controller = Controller(ser, arg_info, version=__version__)

    if arg_info.command:
        query_answer = controller.send_command(arg_info.command)
        if query_answer:
            print(f"{query_answer[0]} {','.join(query_answer[1:])}")
            sys.exit(0)
        else:
            # print(f"{stamp()}: ERROR: Could not communicate with radio.",
            #       file=sys.stderr)
            print(f"{stamp()}: Could not communicate with radio on {arg_info.port}.")
            sys.exit(1)

    if os.environ.get('DISPLAY', '') == '':
        print(f"No $DISPLAY environment. "
              f"Only '-c' option works without X", file=sys.stderr)
        sys.exit(1)
        # os.environ.__setitem__('DISPLAY', ':0.0')

    # Commands to verify we can communicate with the radio. If all work,
    # then there's a good chance the port isn't in use by another app
    test_queries = ('MS', 'AE', 'ID')
    for test in test_queries:
        query_answer = controller.send_command(test)
        if not query_answer:
            # print(f"{stamp()}: ERROR: Could not communicate with radio.")
            print(f"{stamp()}: Could not communicate with "
                  f"radio on {arg_info.port} @ {arg_info.baudrate}",
                  file=sys.stderr)
            sys.exit(1)
    print(f"{stamp()}: Found {query_answer[1]} on {arg_info.port} @ "
          f"{arg_info.baudrate}", file=sys.stderr)
    controller.set_id(query_answer[1])

    root = tk.Tk()
    controller.start_gui(root)

    # Stop program if Esc key or Ctrl-C pressed
    root.bind('<Escape>', lambda e: controller.stop())
    root.bind('<Control-c>', lambda e: controller.stop())
    # Stop program if window is closed at OS level ('X' in upper right
    # corner of GUI window)
    root.protocol("WM_DELETE_WINDOW",
                  lambda: controller.stop())
    print(f"{stamp()}: Starting mainloop", file=sys.stderr)
    root.mainloop()
    print(f"{stamp()}: Mainloop stopped", file=sys.stderr)
    # SIGTERM is necessary if there's a connected TCP socket from an
    # XMLRPC client, otherwise the GUI stays open.
    this_process = os.getpid()
    os.kill(this_process, signal.SIGTERM)
