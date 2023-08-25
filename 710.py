#!/usr/bin/env python3
"""
Implements a GUI that allows the user to control some functions of the
Kenwood TM-D710G and TM-V71A radios via CAT.
"""
import os
import re
import sys
import signal

import common710
from common710 import stamp
from common710 import XMLRPC_PORT
from common710 import VENDOR_ID, PRODUCT_IDS
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
__version__ = "2.3.4"
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


def get_ports() -> list:
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


def get_cm1xx_devices() -> dict:
    found_devices = {}
    try:
        import hid
    except ModuleNotFoundError:
        print(f"{stamp()}: Python3 hidapi module not found.", file=sys.stderr)
    else:
        index = 0
        for device_dict in hid.enumerate(VENDOR_ID):
            if device_dict['product_id'] in PRODUCT_IDS:
                index += 1
                found_devices.update({index: device_dict['path']})
    return found_devices


def rig_choices() -> list:
    rig_list = ['none']
    if not sys.platform.startswith('win'):
        rig_list.extend(common710.GPIO_PTT)
        rig_list.extend(common710.NEXUS_PTT_GPIO_DICT.keys())
    rig_list.append('digirig')
    if len(port_list) > 1:
        digirig_ports = [f"digirig@{port}" for port in port_list]
        rig_list.extend(digirig_ports)
    if cmedia_devices:
        rig_list.append('cm108')
        for i in range(1, 9):
            rig_list.append(f'cm108:{i}')
        if len(cmedia_devices) > 1:
            for i in range(1, len(cmedia_devices)+1):
                rig_list.append(f'cm108@{i}')
                for j in range(1, 9):
                    rig_list.append(f'cm108@{i}:{j}')
    return rig_list


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    port_list = get_ports()
    if not port_list:
        print(f"{stamp()}: No serial ports found.", file=sys.stderr)
        sys.exit(1)
    default_port = port_list[0]
    cmedia_devices = get_cm1xx_devices()

    parser = argparse.ArgumentParser(prog=__title__,
                                     description=f"CAT control for Kenwood TM-D710G/TM-V71A",
                                     formatter_class=Formatter)
    parser.add_argument('-v', '--version', action='version',
                        version=f"Version: {__version__}")
    parser.add_argument("-p", "--port",
                        choices=port_list,
                        type=str, default=default_port,
                        help="Serial port connected to radio")
    parser.add_argument("--norts", action="store_true",
                        help="Disable RTS on serial port. Required when\n"
                             "DigiRig serial port is connected to radio.")
    parser.add_argument("-b", "--baudrate",
                        choices=[300, 1200, 2400, 4800, 9600, 19200,
                                 38400, 57600],
                        type=int, default=BAUD,
                        help="Serial port speed (must match radio!)")
    parser.add_argument("-s", "--small", action='store_true',
                        help="Smaller GUI window")
    parser.add_argument("--cm108_devices", action="store_true",
                        help="List attached C-Media CM1xx devices.")
    parser.add_argument("-l", "--location", type=str, metavar="x:y",
                        help="x:y: Initial x and y position (in pixels)\n"
                             "of upper left corner of GUI.")
    parser.add_argument("-x", "--xmlport", type=int,
                        choices=range(1024, 65536),
                        metavar="{1024-65535}", default=XMLRPC_PORT,
                        help="TCP port on which to listen for XML-RPC\n"
                             "rig control calls from clients such as\n"
                             "Fldigi or Hamlib rigctl[d].")
    parser.add_argument("-r", "--ptt", type=str,
                        choices=rig_choices(),
                        default='none',
                        help="How to handle XML-RPC 'rig.set_ptt' calls.\n\n"
                             "Raspberry Pi users can specify the BCM GPIO pin\n"
                             "number driving your PTT circuit. Nexus DR-X Pi users:\n"
                             "Use 'left' or 'right'. This will map to GPIO\n"
                             "pin 12 for the left radio and pin 23 for the right.\n\n"
                             "'none' (the default) means that 'rig.set_ptt' calls\n"
                             "will be ignored (meaning you'll control PTT by\n"
                             "some other means).\n\n"
                             "'digirig[@digirig-serial-port]':\n"
                             "'digirig' is for use with the DigiRig sound card\n"
                             "and (optionally) the associated special serial cable\n"
                             "between the radio and the DigiRig serial port.\n"
                             "'digirig@<digirig-serial-port>' is for use when the\n"
                             "controller is connected via a different serial port\n"
                             "than the DigiRig. In that case when an XML-RPC\n"
                             "'rig.set_ptt' call is received, the controller\n"
                             "activates RTS on <digirig-serial-port>, which\n"
                             "triggers PTT through the 6-pin minDIN connector.\n\n"
                             "'cm108[@index][:1-8]' will activate a GPIO pin on\n"
                             "CM108/CM119 sound interfaces for PTT. Masters\n"
                             "Communications DRA series of sound cards use this\n"
                             "chip and PTT mechanism.\n\n"
                             "If more than one CM108/CM119 sound card is attached,\n"
                             "the last one found will be used unless you specify\n"
                             "'@index'. You can determine the index by running this\n"
                             "program one time with only the '--cm108_devices' argument\n"
                             "to see a list of attached and compatible cm1xx devices.\n\n"
                             "You can specify the CM108 GPIO pin by appending ':x'\n"
                             "where x is 1 through 8 inclusive. 'cm108' by itself\n"
                             "will use GPIO 3, the most commonly used CM1xx GPIO pin.\n\n"
                             "'cat' will send the 'TX' or 'RX' CAT command to the\n"
                             "radio to control PTT. Note that this will transmit\n"
                             "on the side on which 'PTT' is set and will transmit\n"
                             "mic audio, *not* DATA port audio!\n\n")
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
    if arg_info.norts:
        # Needed when DigiRig serial port is used to connect to rig
        ser.rts = False

    ser.port = arg_info.port
    try:
        ser.open()
    except serial.serialutil.SerialException:
        print(f"{stamp()}: Could not open {arg_info.port}", file=sys.stderr)
        sys.exit(1)

    # Print list of C-Media devices,if requested, then exit
    if arg_info.cm108_devices:
        if cmedia_devices:
            print(f"{'Index': ^5} C-Media CM1xx Device Path")
            print(f"{'-----': ^5} -------------------------")
            for key, value in cmedia_devices.items():
                print(f"{key: ^5} {value.decode()}")
        else:
            print("No C-Media CM1xx sound cards with GPIO found.")
        sys.exit(0)

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
            print(f"No $DISPLAY environment. Only '-c' or '--cm108_devices'"
                  "options work without X", file=sys.stderr)
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
