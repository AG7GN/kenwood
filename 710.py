#!/usr/bin/env python3
"""
Implements a GUI that allows the user to control some functions of the
Kenwood TM-D710G and TM-V71A radios via CAT.
"""
import os
import re
import sys
import signal
from common710 import stamp
from common710 import XMLRPC_PORT
from common710 import GPIO_PTT_DICT
try:
    import argparse
except ModuleNotFoundError:
    print(f"{stamp()}: Python3 argparse module not found.", file=sys.stderr)
    sys.exit(1)

__title__ = os.path.basename(sys.argv[0] if "python" not in sys.argv[0]
                             else sys.argv[1])
__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2023, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "2.2.0"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"
BAUD = 57600


class Formatter(argparse.RawTextHelpFormatter,
                argparse.ArgumentDefaultsHelpFormatter):
    """
    Add additional formatting ability to argparse Help text.
    """
    pass


def sigint_handler(_, __):
    # print(f"{stamp()}: Signal handler caught {sig} {frame}")
    cleanup()


def cleanup():
    if controller:
        controller.stop()


def get_ports():
    """
    Windows: Looks for COM ports
    Mac/Linux: Walks /dev searching for paths with filenames or
    symlinks to filenames containing ^tty(AMA[0-9]|S[0-9]|USB[0-9]).
    :returns: A list of the serial ports available on the system or
    an empty list if no serial ports are found.
    """
    ports = []
    if sys.platform.startswith('win'):
        try:
            import serial.tools.list_ports_windows as list_ports_windows
        except ModuleNotFoundError:
            print(f"{stamp()}: Python3 serial module not found. "
                  f"To install: pip install pyserial",
                  file=sys.stderr)
            sys.exit(1)
        for p in list_ports_windows.comports():
            ports.append(str(p).split(" ")[0])
    else:
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
    port_list = get_ports()
    if not port_list:
        default_port = ''
    else:
        default_port = port_list[0]
    signal.signal(signal.SIGINT, sigint_handler)
    if sys.platform.startswith('win'):
        # Omit GPIO pin options if OS is Windows
        ptt_list = [key for key, val in GPIO_PTT_DICT.items() if val is None]
    else:
        ptt_list = list(GPIO_PTT_DICT.keys())

    parser = argparse.ArgumentParser(prog=__title__,
                                     description=f"CAT control for Kenwood TM-D710G/TM-V71A",
                                     formatter_class=Formatter)
    parser.add_argument('-v', '--version', action='version',
                        version=f"Version: {__version__}")
    parser.add_argument("-p", "--port",
                        choices=port_list,
                        type=str, default=default_port,
                        help="Serial port connected to radio")
    parser.add_argument("-b", "--baudrate",
                        choices=[300, 1200, 2400, 4800, 9600, 19200,
                                 38400, 57600],
                        type=int, default=BAUD,
                        help="Serial port speed (must match radio!)")
    parser.add_argument("-s", "--small", action='store_true',
                        help="Smaller GUI window")
    parser.add_argument("-l", "--location", type=str, metavar="x:y",
                        help="x:y: Initial x and y position (in pixels)\n"
                             "of upper left corner of GUI.")
    parser.add_argument("-x", "--xmlport", type=int,
                        choices=range(1024, 65536),
                        metavar="{1024-65535}", default=XMLRPC_PORT,
                        help="TCP port on which to listen for XML-RPC\n"
                             "rig control calls from clients such as\n"
                             "Fldigi or Hamlib rigctl[d].")
    parser.add_argument("-r", "--rig", type=str.lower,
                        choices=ptt_list,
                        default='none',
                        help="PTT device to use if you want to control \n"
                             "PTT via an XML-RPC 'rig.set_ptt' call.\n"
                             "Pi users can specify the BCM GPIO pin number\n"
                             "driving your PTT circuit. Nexus DR-X Pi users:\n"
                             "Use 'left' or 'right'. This will map to GPIO\n"
                             "pin 12 for the left radio and pin 23 for the right.\n\n"
                             "'none' means that 'rig.set_ptt' calls will be ignored\n"
                             "(meaning you'll control PTT by some other means).\n\n"
                             "'digirig' is for use with the DigiRig interface\n"
                             "and associated special serial cable. Disables\n"
                             "RTS on the serial port because on the DigiRig,\n"
                             "RTS controls PTT via a separate circuit.\n\n"
                             "'cat' will, when 'rig.set_ptt' calls are received,\n"
                             "send the 'TX' or 'RX' CAT command to the radio\n"
                             "to control PTT. Note that this will activate PTT\n"
                             "on the side on which PTT is set and will transmit\n"
                             "mic audio, *not* the DATA port audio!\n\n")
    parser.add_argument("-c", "--command",
                        type=str, help="CAT command to send to radio (no GUI)")
    arg_info = parser.parse_args()
    if not port_list:
        print(f"{stamp()}: No serial ports found.", file=sys.stderr)
        sys.exit(1)
    # if not arg_info.command:
    #     print(f"{stamp()}: Opening {arg_info.port} @ {arg_info.baudrate} bps",
    #           file=sys.stderr)
    try:
        import serial
    except ModuleNotFoundError:
        print(f"{stamp()}: Python3 serial module not found.", file=sys.stderr)
        sys.exit(1)
    ser = serial.Serial(port=None, baudrate=arg_info.baudrate,
                        timeout=0.1,
                        writeTimeout=0.1)
    if arg_info.rig == 'digirig':
        ser.rts = False
    ser.port = arg_info.port
    try:
        ser.open()
    except serial.serialutil.SerialException:
        print(f"{stamp()}: Could not open {arg_info.port}", file=sys.stderr)
        sys.exit(1)
    from controller710 import Controller
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

    if not sys.platform.startswith('win'):
        if os.environ.get('DISPLAY', '') == '' and sys.platform != 'darwin':
            print(f"No $DISPLAY environment. "
                  f"Only '-c' option works without X", file=sys.stderr)
            sys.exit(1)
            # os.environ.__setitem__('DISPLAY', ':0.0')

    # Commands to verify we can communicate with the radio. If all work,
    # then there's a good chance the port isn't in use by another app
    queries = ('AE', 'FV 0', 'FV 1', 'ID')
    for query in queries:
        query_answer = controller.send_command(query)
        if not query_answer:
            print(f"{stamp()}: Could not communicate with "
                  f"radio on {arg_info.port} @ {arg_info.baudrate}",
                  file=sys.stderr)
            sys.exit(1)
        controller.set_info(query_answer)
    # noinspection PyUnboundLocalVariable
    print(f"{stamp()}: Found {query_answer[1]} on {arg_info.port} @ "
          f"{arg_info.baudrate}", file=sys.stderr)

    try:
        import tkinter as tk
    except ModuleNotFoundError:
        print(f"{stamp()}: Python3 tk module not found.", file=sys.stderr)
        sys.exit(1)
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
