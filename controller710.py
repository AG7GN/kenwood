import sys
import os
import serial
import argparse
from time import time
from queue import Queue
from threading import Thread
from cat710 import Cat
from gui710 import Display
from common710 import stamp
from common710 import UpdateDisplayException
from xmlrpc710 import RigXMLRPC

__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2022, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "1.0.0"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"


class Controller(object):
    """
    Object Manager Object for the Kenwood TM-D710G and TM-V71A controller
    """
    def __init__(self, o_serial: serial, args: argparse, **kwargs):
        """
        Instantiate Controller and Cat classes.
        :param o_serial: Serial port object from Serial module
        :param args: Command line arguments from argparse
        :param kwargs: 'version', the program version for inclusion
        on the GUI title bar
        """
        self.version = kwargs.get('version', '')
        self.o_serial = o_serial
        self.serial_port = args.port
        self.baudrate = args.baudrate
        self.ptt_side = args.rig
        self.xmlrpc_port = args.xmlport
        self.loc = args.location
        if args.small:
            self.size = 'small'
        else:
            self.size = 'normal'
        self.root = None
        self.msg_queue = None
        self.gui = None
        self.xmlrpc_server = None
        self.title = None
        self.cat = Cat(self.o_serial, self.ptt_side)
        self.cmd_queue = Queue()
        self.controller_thread = None
        self.controller_running = False
        try:
            self.xmlrpc_server = RigXMLRPC(self.xmlrpc_port, self.cat,
                                           self.cmd_queue)
        except OSError as _:
            self.print_error(f"XML-RPC port {self.xmlrpc_port} is already in use.\n\n"
                             f"Is this program or already Flrig running?\n"
                             f"Close it before running this program.")
            self.stop()
        else:
            self.xmlrpc_thread = Thread(target=self.xmlrpc_server.start)
            # Kill this thread when the main app terminates
            self.xmlrpc_thread.setDaemon(True)

    def _start_xmlrpc_server(self):
        time_current = time()
        # Wait until radio parameters have been read and state
        # dictionary populated before starting the XML-RPC server
        # so that we have something to serve.
        while self.cat.get_dictionary()['speed'] is None:
            # Exit if we receive no data from radio in 5 seconds
            if time() >= time_current + 5:
                self.print_error(f"{stamp()}: No data received from "
                                 f"radio in 5 seconds")
                # sys.exit(1)
                self.stop()
        print(f"{stamp()}: Starting XML-RPC server...", file=sys.stderr)
        self.xmlrpc_thread.start()
        print(f"{stamp()}: XML-RPC server running.", file=sys.stderr)

    def start_gui(self, root: object):
        self.root = root
        self.msg_queue = Queue()
        if self.loc is not None:
            loc = self.loc.split(':')
            try:
                x_loc = int(loc[0])
                y_loc = int(loc[1])
            except (ValueError, IndexError):
                print(f"{stamp()}: '{self.loc}' is an invalid "
                      f"screen position. Using defaults instead.",
                      file=sys.stderr)
                loc = None
            else:
                y_max = self.root.winfo_screenheight()
                x_max = self.root.winfo_screenwidth()
                if 0 <= x_loc < x_max - 100 and 0 <= y_loc < y_max - 100:
                    loc = (x_loc, y_loc)
                else:
                    print(f"{stamp()}: '{self.loc}' is an invalid "
                          f"screen position. Using defaults instead.",
                          file=sys.stderr)
                    loc = None
        else:
            loc = None
        model = self.cat.get_id()
        self.title = f"Kenwood {model} Controller"
        self.gui = Display(root=self.root,
                           title=self.title,
                           version=self.version,
                           cmd_queue=self.cmd_queue,
                           msg_queue=self.msg_queue,
                           size=self.size,
                           initial_location=loc)
        self.msg_queue.put(['INFO', f"{stamp()}: Found {model} on "
                            f"{self.serial_port} @ {self.baudrate}"])
        self.controller_running = True
        self.controller_thread = Thread(target=self.controller)
        self.controller_thread.setDaemon(True)
        print(f"{stamp()}: Starting controller...", file=sys.stderr)
        self.controller_thread.start()
        print(f"{stamp()}: Controller running.", file=sys.stderr)
        self._start_xmlrpc_server()

    def controller(self):
        while self.controller_running:
            if self.cmd_queue.empty():
                try:
                    rig_dictionary = self.cat.update_dictionary()
                except IndexError as _:
                    self.print_error(f"Error communicating with radio on "
                                     f"{self.serial_port}")
                    break
                else:
                    try:
                        self.gui.update_display(rig_dictionary)
                    except UpdateDisplayException as _:
                        self.print_error(f"Error communicating with "
                                         f"radio on {self.serial_port}")
                        break
                    else:
                        if self.root:
                            self.root.update()
            else:
                job = self.cmd_queue.get()  # Get job from queue
                if job[0] == 'quit':
                    break
                self.msg_queue.put(['INFO', f"{stamp()}: Queued {job}"])
                # result = rig.run_job(job, msg_queue)
                if self.cat.run_job(job, self.msg_queue):
                    self.msg_queue.put(['INFO', f"{stamp()}: Finished {job}"])
                else:
                    break
                self.cmd_queue.task_done()
        self.stop()

    def print_error(self, err: str):
        """
        If X Windows environment detected, pop up a window with
        the message, otherwise print message to stderr.
        :param err: String containing message
        :return: None
        """
        if os.environ.get('DISPLAY', '') == '':
            # X not running. Print to stderr.
            print(f"{stamp()}: {err}", file=sys.stderr)
        else:
            # X running. Use existing tkinter root if set
            from tkinter import messagebox
            try:
                self.root.withdraw()
            except (NameError, AttributeError) as _:
                # tkinter root window doesn't exist.
                # Make a new root for messagebox
                import tkinter as tk
                error_root = tk.Tk()
                error_root.withdraw()
                messagebox.showerror(title=f"Controller ERROR!",
                                     message=err,
                                     parent=error_root)
                error_root.destroy()
            else:
                # Root window exists. Use it for messagebox.
                messagebox.showerror(title=f"Controller ERROR!",
                                     message=err,
                                     parent=self.root)

    def send_command(self, cmd: str) -> list:
        return self.cat.handle_query(cmd)

    def set_id(self, model: str):
        self.cat.set_id(model)

    def stop(self):
        print(f"{stamp()}: Stopping controller...",
              file=sys.stderr)
        self.controller_running = False
        if self.controller_thread and self.controller_thread.is_alive():
            try:
                self.controller_thread.join(timeout=2)
            except RuntimeError as _:
                print(f"{stamp()}:   Controller thread stopped",
                      file=sys.stderr)
        if self.xmlrpc_server:
            self.xmlrpc_server.stop()
            if self.controller_thread.is_alive():
                self.xmlrpc_thread.join(timeout=1)
            print(f"{stamp()}:   XML-RPC server stopped",
                  file=sys.stderr)
        print(f"{stamp()}: Controller stopped.", file=sys.stderr)
        if self.root:
            self.root.quit()
            self.root.update()
        self.o_serial.close()
