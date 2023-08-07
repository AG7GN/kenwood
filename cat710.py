import io
import re
import sys

import common710
from common710 import *
from queue import Queue

__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2022, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "2.0.8"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"


# noinspection PyTypeChecker
class Cat(object):
    """
    Kenwood TM-D710G and TM-V71A CAT implementation

    This class implements the CAT interface, enabling a computer to
    control the radio via a serial interface. The Kenwood CAT commands
    are documented at https://github.com/LA3QMA/TM-V71_TM-D710-Kenwood
    """

    class CatPtt(object):
        """
        Implements PTT via CAT command to serial port. Note that sending
        the CAT command 'TX' will cause the mic audio to be transmitted,
        not audio received on the DATA port
        """

        def __init__(self, job_queue: Queue):
            self.job_queue = job_queue
            self.ptt_active = 0

        def on(self):
            if self.job_queue is not None:
                self.job_queue.put(['cat_ptt', 'TX'])
                self.ptt_active = 1

        def off(self):
            if self.job_queue is not None:
                self.job_queue.put(['cat_ptt', 'RX'])
                self.ptt_active = 0

        @property
        def value(self):
            # There is no way to query the radio for PTT state,
            # so use the self.ptt_active variable set in the 'on' and
            # 'off' functions above for status.
            return self.ptt_active

    class DigirigPtt(object):
        """
        Implements PTT via assertion of RTS in CAT serial port. DigiRig
        devices use the RTS signal on the serial port to drive a circuit
        that controls PTT in the Mini-DIN6 connector. For CAT to work,
        a special serial cable that loops the RTS pin back to the CTS
        pin on the radio side must be used between the radio and the
        DigiRig device. This cable can be purchased from digirig.net.
        """

        def __init__(self, port):
            self.port = port

        def on(self):
            self.port.rts = True

        def off(self):
            self.port.rts = False

        @property
        def value(self):
            return int(self.port.rts)

    class CM108Ptt(object):
        """
        Implements PTT via GPIO on CM108/CM119 sound interfaces such as
        the DRA series. The most common GPIO pin for PTT on these
        devices is 3, but the user can specify any GPIO pin between 1
        and 8. 3 is the default
        """
        def __init__(self, pin: int):
            try:
                import hid
            except ModuleNotFoundError:
                print(f"{stamp()}: Python3 hidapi module not found.", file=sys.stderr)
                return
            self.pin = pin
            self.device = None
            self.ptt_active = 0
            # CM108 info: https://github.com/nwdigitalradio/direwolf/blob/master/cm108.c)
            mask = 1 << (self.pin - 1)
            self.PTT_on = bytearray([0, 0, mask, mask, 0])
            self.PTT_off = bytearray([0, 0, mask, 0, 0])
            self.CM108_ready = False
            # CM1xx sound card Vendor ID
            # self.vendor_id = common710.VENDOR_ID
            # Product IDs with known GPIO capability from the CM1xx family
            # self.product_ids = common710.PRODUCT_IDS
            self.path = None
            for device_dict in hid.enumerate(vendor_id=common710.VENDOR_ID):
                if device_dict['product_id'] in common710.PRODUCT_IDS:
                    self.path = device_dict['path']
                    # There is no way to identify individual CM1xx
                    # USB sound cards because there is no serial number.
                    # So, use the first CM1xx sound card we find.
                    break
            if self.path is None:
                print(f"{stamp()}: No CM1xx sound device with GPIO found",
                      file=sys.stderr)
                return
            else:
                self.device = hid.device()
                # Verify that we can open the HID device before
                # claiming victory
                if self._open():
                    self._close()
                    self.CM108_ready = True

        def _open(self) -> bool:
            try:
                self.device.open_path(self.path)
            except (OSError, IOError) as e:
                print(f"{stamp()}: Unable to open CM1xx sound device "
                      f"at path {self.path}: {e}",
                      file=sys.stderr)
                return False
            else:
                self.device.set_nonblocking(1)
                return True

        def _close(self):
            if self.device is not None:
                self.device.close()

        def on(self):
            if self._open():
                wrote = self.device.write(self.PTT_on)
                if wrote == len(self.PTT_on):
                    self.ptt_active = 1
                else:
                    self.ptt_active = 0
                    print(f"{stamp()}: Unable to write to CM108 GPIO {self.pin}",
                          file=sys.stderr)
                self._close()

        def off(self):
            if self._open():
                previous_ptt_state = self.ptt_active
                wrote = self.device.write(self.PTT_off)
                if wrote == len(self.PTT_off):
                    self.ptt_active = 0
                else:
                    print(f"{stamp()}: Unable to write to CM108 GPIO {self.pin}",
                          file=sys.stderr)
                    if previous_ptt_state == 0:
                        self.ptt_active = 0
                    else:
                        self.ptt_active = 1
                self._close()

        @property
        def value(self) -> int:
            return self.ptt_active

        @property
        def ready(self) -> bool:
            return self.CM108_ready

    def __init__(self, serial_port: object, ptt_pin: str, **kwargs):
        """
        Initializes a BufferedRWPair object that wraps a serial object.
        Wrapping the serial port object allows customization of the
        end-of-line character used by the radio
        :param serial_port: Serial object
        """
        if kwargs['job_queue']:
            self.job_queue = kwargs['job_queue']
        else:
            self.job_queue = None
        self.gui = None
        self.ser = serial_port
        sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser),
                               newline='\r')
        self.sio = sio
        self.state = {'A': {'mode': None, 'ch_name': None,
                            'ch_number': None, 'frequency': None,
                            'shift': None, 'reverse': None,
                            'tone': None, 'tone_frequency': None,
                            'modulation': None, 'power': None,
                            'ptt': None, 'ctrl': None, 'data': None,
                            'step': None,
                            },
                      'B': {'mode': None, 'ch_name': None,
                            'ch_number': None, 'frequency': None,
                            'shift': None, 'reverse': None,
                            'tone': None, 'tone_frequency': None,
                            'modulation': None, 'power': None,
                            'ptt': None, 'ctrl': None, 'data': None,
                            'step': None,
                            },
                      'backlight': None,
                      'vhf_aip': None,
                      'uhf_aip': None,
                      'timeout': None,
                      'lock': None,
                      'speed': None,
                      'data_side': None,
                      'gpio': None,
                      'id': '',
                      'info': {'model': '',
                               'firmware': {'main': '', 'panel': ''},
                               'serial': ''
                               }
                      }
        self.ptt_pin = ptt_pin
        if self.ptt_pin == 'none':
            # self.state['gpio'] = None
            self.ptt = None
        elif self.ptt_pin.startswith('digirig'):
            digirig = self.ptt_pin.split('@')
            try:
                digirig_device_name = digirig[1]
            except (ValueError, IndexError):
                # No '@<device>' so digirig uses same serial
                # port as controller
                self.ptt = self.DigirigPtt(self.ser)
            else:
                # User supplied a digirig serial port device name,
                # and it is different from the controller port device.
                # Set up the digirig serial port
                import serial
                digirig_device = serial.Serial(port=None)
                digirig_device.rts = False
                digirig_device.port = digirig_device_name
                try:
                    digirig_device.open()
                except serial.serialutil.SerialException:
                    # Supplied digirig device port exits, but can't open it
                    print(f"{stamp()}: Could not open digirig device "
                          f"{digirig_device_name}. Ignoring CAT PTT commands.",
                          file=sys.stderr)
                    self.ptt = None
                else:
                    self.ptt = self.DigirigPtt(digirig_device)
        elif self.ptt_pin == 'cat':
            self.ptt = self.CatPtt(self.job_queue)
        elif self.ptt_pin.startswith('cm108'):
            cm108 = self.ptt_pin.split(':')
            try:
                cm108_gpio = int(cm108[1])
            except (ValueError, IndexError):
                # No GPIO pin specified. Use 3, the most common
                # for PTT on CM1xx
                cm108_gpio = 3
            self.ptt = self.CM108Ptt(cm108_gpio)
            if not self.ptt.ready:
                print(f"{stamp()}: Unable to locate or init CM108. "
                      f"Ignoring CM108 PTT settings.",
                      file=sys.stderr)
                self.ptt = None
        else:
            try:
                from gpiozero import OutputDevice
            except (ModuleNotFoundError, Exception):
                print(f"{stamp()}: Python3 gpiozero module not found. "
                      f"Ignoring GPIO PTT settings",
                      file=sys.stderr)
                self.ptt_pin = None
                self.state['gpio'] = None
                self.ptt = None
            else:
                from gpiozero import BadPinFactory
                self.state['gpio'] = GPIO_PTT_DICT[self.ptt_pin]
                try:
                    self.ptt = OutputDevice(self.state['gpio'],
                                            active_high=True,
                                            initial_value=False)
                except BadPinFactory:
                    print(f"{stamp()}: No GPIO pins found. "
                          f"Ignoring PTT GPIO settings",
                          file=sys.stderr)
                    self.ptt_pin = None
                    self.state['gpio'] = None
                    self.ptt = None

        self.reply_queue = Queue()

    @property
    def gui_root(self) -> object:
        """
        Returns the gui tkinter root to be used for asking for
        user input. Returns None of there is no GUI
        """
        return self.gui

    @gui_root.setter
    def gui_root(self, root: object):
        self.gui = root

    def set_ptt(self, turn_on: bool):
        """
        Control the state of PTT
        :param turn_on: Desired state of PTT
        """
        if self.ptt is not None:
            if turn_on:
                self.ptt.on()
            else:
                self.ptt.off()

    def get_ptt(self):
        """
        Returns state of PTT.
        :return: 1 if PTT is active, 0 if not active or if self.ptt is None
        """
        if self.ptt is None:
            return 0
        else:
            return self.ptt.value

    def query(self, request: str) -> tuple:
        """
        Sends CAT command to Kenwood radio and returns reply as a tuple.
        Kenwood CAT commands for the TM-D710G and TM-V71A begin with a
        2 alpha character string (the command) optionally followed by
        one or more arguments, followed by a carriage return '\r'.
        The radio returns a single '?' if the radio didn't understand
        the command, or returns the original 2 character command,
        followed by the radio's answer: a comma separated string.
        See https://github.com/LA3QMA/TM-V71_TM-D710-Kenwood for
        details.
        :param: request: String containing CAT command to send to radio
        :return: Tuple containing radio's reply to the command. Returns
                empty tuple if radio returns '?' (indicating an unknown
                command) or if there's a problem communicating with the
                radio. Otherwise, it returns the original 2 character
                command followed by a comma separated containing the
                radio's reply.
        """

        # Split the request string on whitespace
        request_list = request.split(maxsplit=1)
        command = request_list[0]  # 2 character Kenwood command
        if len(request_list) > 1:  # Collect the arguments, if present
            send_string = f"{command} {request_list[1]}"
        else:
            send_string = command
        # Remove any leading/trailing whitespace from send_string and
        # append \r for EOL
        try:
            self.sio.write(f"{send_string.strip()}\r")
            self.sio.flush()  # io object buffers, so force data out
            # Replace space separating 2 character command and answer
            # with a ',' so we can include it in the returned tuple
            answer = re.sub(' ', ',', self.sio.readline())
        except Exception as error:
            raise QueryException(f"Serial Port ERROR: {error}")
        # if answer and answer != '?':
        if answer:
            # Remove trailing \r and convert string to tuple
            return tuple(answer[:-1].split(','))
        else:
            return ()

    def handle_query(self, cmd: str) -> list:
        """
        Wrapper for the query method.
        :param: cmd: String to pass to query method
        :return: List containing the output of the radio command, or
                 None if the command failed.
        """
        try:
            result = self.query(cmd)
        except QueryException as error:
            print(f"{stamp()}: No response from radio: {error}",
                  file=sys.stderr)
            return []
        else:
            return result

    def ask(self, ask_type: str, ask_msg: str):
        """
        If GUI exists, pop up a window with
        the warning message, otherwise print message to stderr.
        :param: ask_type: str of 'yesnocancel' or 'okcancel'. Used to determine
        messagebox type. Default is okcancel.
        :param: ask_msg: String containing warning message
        :return: True|False if user clicks Yes|No respectively, None if
                 user clicks Cancel
        """
        if ask_type not in ('okcancel', 'yesnocancel'):
            return False
        if self.gui is None:
            # Print ask_msg to stderr and don't prompt for answer
            # (assume YES)
            print(f"{stamp()}: {ask_msg}: YES", file=sys.stderr)
            return True
        else:
            # X running or this is Windows.
            from tkinter import messagebox
            if ask_type == 'okcancel':
                result = messagebox.askokcancel(title=f"Confirm",
                                                message=ask_msg,
                                                parent=self.gui)
            elif ask_type == 'yesnocancel':
                result = messagebox.askyesnocancel(title=f"Confirm",
                                                   message=ask_msg,
                                                   parent=self.gui)
            else:
                result = False
            return result

    @property
    def info(self) -> dict:
        """
        :return: dictionary containing model, serial and firmware version(s)
        """
        return self.state['info']

    @info.setter
    def info(self, answer: tuple):
        """
        Populate model, serial, and firmware versions in state dictionary
        :param answer: string containing CAT command result from radio
        """
        if answer[0] == 'AE':
            self.state['info']['serial'] = answer[1].split(',')[0]
        elif answer[0] == 'ID':
            self.state['info']['model'] = answer[1]
        elif answer[0] == 'FV':
            if answer[1] == '0':
                self.state['info']['firmware']['main'] = answer[3]
            if answer[1] == '1':
                self.state['info']['firmware']['panel'] = answer[3]
        else:
            self.state['info']['firmware']['panel'] = "N/A"

    def update_dictionary(self) -> dict:
        """
        Queries the radio for several parameters that are used to
        populate a state dictionary, which maps values to the onscreen
        display. Several commands are needed to obtain all the required
        information.
        :return: dictionary with the screen parameters. The dictionary
        is defined and initialized in __init__() method.
        """

        def common_elements(_mode_str: str):
            try:
                if STATE_DICT['map'][result[6]] == "ON":
                    # Tone is set
                    t = "Tone"
                    tf = TONE_FREQUENCY_DICT[t]['map'][result[9]]
                elif STATE_DICT['map'][result[7]] == "ON":
                    # CTCSS is set
                    t = "CTCSS"
                    tf = TONE_FREQUENCY_DICT[t]['map'][result[10]]
                elif STATE_DICT['map'][result[8]] == "ON":
                    # DCS is set
                    t = "DCS"
                    tf = TONE_FREQUENCY_DICT[t]['map'][result[11]]
                else:
                    t = "No Tone"
                    tf = TONE_FREQUENCY_DICT[t]
                # Save tone to state dictionary
                self.state[SIDE_DICT['map'][s]]['tone'] = t
                self.state[SIDE_DICT['map'][s]]['tone_frequency'] = tf
                # Save shift to state dictionary
                self.state[SIDE_DICT['map'][s]]['shift'] = \
                    SHIFT_DICT['map'][result[4]]
                # Save reverse status to state dictionary
                self.state[SIDE_DICT['map'][s]]['reverse'] = \
                    '{}'.format(REVERSE_DICT['map'][result[5]])
                # Save modulation to state dictionary
                self.state[SIDE_DICT['map'][s]]['modulation'] = \
                    '{}'.format(MODULATION_DICT['map'][result[13]])
                # Save the mode to the state dictionary
                self.state[SIDE_DICT['map'][s]]['mode'] = _mode_str
                # Save the RX step to state dictionary
                self.state[SIDE_DICT['map'][s]]['step'] = \
                    STEP_DICT['map'][result[3]]
                # Save the frequency to the state dictionary
                self.state[SIDE_DICT['map'][s]]['frequency'] = \
                    "{:.3f}".format(int(result[2]) / 1000000)
            except IndexError as _:
                raise

        result = []
        result = self.handle_query(f"BC")
        if not result:
            return {}
        try:
            self.state['A']['ctrl'] = 'CTRL' if result[1] == '0' else '   '
            self.state['B']['ctrl'] = 'CTRL' if result[1] == '1' else '   '
            self.state['A']['ptt'] = 'PTT' if result[2] == '0' else '   '
            self.state['B']['ptt'] = 'PTT' if result[2] == '1' else '   '
            sides = ('0', '1')
        except IndexError as _:
            raise
        for s in sides:  # '0' = A side, '1' = B side
            # Determine current mode (VFO, Memory, Call)
            result = self.handle_query(f"VM {s}")
            if not result:
                return {}
            if MODE_DICT['map'][result[2]] == 'MR':
                # This side is in Memory mode
                # Retrieve memory channel
                result = self.handle_query(f"MR {s}")
                if not result:
                    return {}
                ch_num_raw = result[2]  # Unformatted channel number
                try:
                    # Save the channel number to the state dictionary
                    self.state[SIDE_DICT['map'][s]]['ch_number'] = \
                        int(result[2])
                except IndexError as _:
                    raise
                # Retrieve state information for this memory channel
                result = self.handle_query(f"FO {s}")
                if not result:
                    return {}
                # print(f"{stamp()}: {result}", file=sys.stderr)
                try:
                    common_elements('MR')
                except IndexError as _:
                    raise
                # Retrieve the channel name
                result = self.handle_query(f"MN {ch_num_raw}")
                if not result:
                    return {}
                try:
                    if result[0] != 'N':
                        self.state[SIDE_DICT['map'][s]]['ch_name'] = \
                            result[2]
                except IndexError as _:
                    raise
            # else:
            #     print(f"{stamp()}: ERROR: Nothing in memory",
            #           file=sys.stderr)
            elif MODE_DICT['map'][result[2]] == 'VFO':
                # This side is in VFO mode. Retrieve FO data
                result = self.handle_query(f"FO {s}")
                if not result:
                    return {}
                try:
                    common_elements('VFO')
                except IndexError as _:
                    raise
                try:
                    self.state[SIDE_DICT['map'][s]]['ch_number'] = '  '
                    self.state[SIDE_DICT['map'][s]]['ch_name'] = '      '
                except IndexError as _:
                    raise
            elif MODE_DICT['map'][result[2]] == 'CALL':
                # This side is in Call mode. Retrieve CC data
                # result = self.handle_query(f"CC {s}")
                result = self.handle_query(f"FO {s}")
                if not result:
                    return {}
                try:
                    common_elements('CALL')
                except IndexError as _:
                    raise
                try:
                    self.state[SIDE_DICT['map'][s]]['ch_number'] = '  '
                    self.state[SIDE_DICT['map'][s]]['ch_name'] = '      '
                except IndexError as _:
                    raise
            elif MODE_DICT['map'][result[2]] == 'WX':
                # This side is in Call mode. Retrieve CC data
                # result = self.handle_query(f"CC {s}")
                result = self.handle_query(f"FO {s}")
                if not result:
                    return {}
                try:
                    common_elements('WX')
                except IndexError as _:
                    raise
                try:
                    self.state[SIDE_DICT['map'][s]]['ch_number'] = '  '
                    self.state[SIDE_DICT['map'][s]]['ch_name'] = '      '
                except IndexError as _:
                    raise
            else:
                pass
            # Power
            result = self.handle_query(f"PC {s}")
            if not result:
                return {}
            try:
                self.state[SIDE_DICT['map'][s]]['power'] = POWER_DICT['map'][result[2]]
            except IndexError as _:
                raise
        # Data side
        result = self.handle_query(f"MU")
        if not result:
            return {}
        try:
            if result[38] in ['0', '1']:
                self.state['data_side'] = SIDE_DICT['map'][result[38]]
            else:
                self.state['data_side'] = None
            self.state[SIDE_DICT['map']['0']]['data'] = \
                'D' if result[38] == '0' else \
                'D-TX' if result[38] == '2' else \
                'D-RX' if result[38] == '3' else \
                ' '
            self.state[SIDE_DICT['map']['1']]['data'] = \
                'D' if result[38] == '1' else \
                'D-RX' if result[38] == '2' else \
                'D-TX' if result[38] == '3' else \
                ' '
            self.state['speed'] = DATA_SPEED_DICT['map'][result[39]]
            self.state['timeout'] = TIMEOUT_DICT['map'][result[16]]
            self.state['vhf_aip'] = STATE_DICT['map'][result[11]]
            self.state['uhf_aip'] = STATE_DICT['map'][result[12]]
            self.state['backlight'] = BACKLIGHT_DICT['map'][result[28]]
        except IndexError as _:
            raise
        # Lock state
        result = self.handle_query(f"LK")
        if not result:
            return {}
        try:
            self.state['lock'] = LOCK_DICT['map'][result[1]]
        except IndexError as _:
            raise
        return self.state

    def get_dictionary(self) -> dict:
        """
        Returns state of radio as a dictionary
        :return: state dictionary
        """
        return self.state

    def run_job(self, job: list, msg_queue: Queue) -> list:
        """
        Accepts a job list and constructs the corresponding Kenwood
        CAT command string needed to fulfill the job task. Sends CAT
        command string to handle_query.
        :param job: list containing job
        :param msg_queue: Queue to which to send status messages
        :return: The job that was sent as an argument, or if the job
        was a 'command', the result of the command will be the second
        list element. Returns empty list if the job could not be
        completed.
        """

        def get_arg_list() -> list:
            """
            Creates a CAT command argument list because some CAT
            commands require interim CAT queries to construct
            the user's query.
            :return: List containing query results, or empty list if
            the query failed.
            """
            if len(job) > 1 and job[1] in ('A', 'B'):
                _arg = SIDE_DICT['inv'][job[1]]
                _answer = self.handle_query(f"VM {_arg}")
                if not _answer:
                    return []
                _, _, _m = list(_answer)
                if _m == '0':  # vfo
                    cmd = 'FO'
                elif _m == '1':  # mr
                    cmd = 'ME'
                    _answer = self.handle_query(f"MR {_arg}")
                    if not _answer:
                        return []
                    _arg = _answer[2]  # Get the channel number
                elif _m == '2':  # call
                    cmd = 'CC'
                else:  # wx
                    cmd = 'VM'
                    _arg = f"{_arg},3"
                _answer = self.handle_query(f"{cmd} {_arg}")
                if not _answer:
                    return []
                else:
                    return list(_answer)
            else:
                return []

        def get_ptt_ctrl() -> tuple:
            """
            Retrieves current PTT and CTRL state of radio
            :return: Tuple (CTRL_state, PTT_state) where CTRL_state and
            PTT_state are 0 or 1. Returns empty tuple if unable to
            retrieve data
            """
            _answer = self.handle_query("BC")
            if not _answer:
                return ()
            return _answer[1], _answer[2]

        if job[0] in ('mode',):  # 'VM' command - mode change requested
            # Save current CTRL state because radio will move CTRL to the
            # side of the radio that's changing modes. Will restore
            # state later.
            ptt_ctrl_state = get_ptt_ctrl()
            if not ptt_ctrl_state:
                return []
            arg = f"VM {SIDE_DICT['inv'][job[1]]},{job[2]}"
            if not self.handle_query(arg):
                return []
            # Restore original PTT, CTRL state
            _ctrl, _ptt = ptt_ctrl_state
            if not self.handle_query(f"BC {_ctrl},{_ptt}"):
                return []
        elif job[0] in ('ptt', 'ctrl'):  # 'BC' command
            answer = get_ptt_ctrl()
            if not answer:
                return []
            ctrl, ptt = answer
            if job[0] == 'ptt':
                arg = f"BC {ctrl},{SIDE_DICT['inv'][job[1]]}"
            else:  # Setting ctrl
                arg = f"BC {SIDE_DICT['inv'][job[1]]},{ptt}"
            if not self.handle_query(arg):
                return []
        elif job[0] in ('power',):  # 'PC' command
            arg = f"PC {SIDE_DICT['inv'][job[1]]},{job[2]}"
            if not self.handle_query(arg):
                return []
        elif job[0] in ('lock',):
            answer = self.handle_query("LK")
            if not answer:
                return []
            arg = "LK {}".format('1' if answer[1] == '0' else '0')
            if not self.handle_query(arg):
                return []
        elif job[0] in ('frequency', 'modulation', 'step',
                        'tone', 'tone_frequency', 'rev', 'shift'):
            arg_list = get_arg_list()
            if not arg_list or arg_list[0] == 'N':
                return []
            if arg_list[0] not in ['CC', 'FO', 'ME']:
                # WX or unknown mode. Skip this job.
                job[0] = None
            if job[0] in ('tone', 'tone_frequency'):
                same_type = False
                for key, value in TONE_TYPE_DICT['map'].items():
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
                    # t is tone freq., c is CTCSS freq., d is DCS freq.
                    _, t, c, d = list(TONE_TYPE_DICT['map'].keys())
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
                if job[0] == 'tone_frequency' and current_type != '0':
                    arg_list[int(current_type) + 3] = \
                        TONE_FREQUENCY_DICT[current_type]['inv'][job[2]]
            if job[0] == 'frequency':
                arg_list[2] = f"{int(job[2] * 1000000):010d}"
                arg_list[4] = frequency_shifts(int(job[2] * 1000000))[0]
                arg_list[12] = frequency_shifts(int(job[2] * 1000000))[1]
            if job[0] == 'modulation':
                arg_list[13] = job[2]
            if job[0] == 'step':
                arg_list[3] = job[2]
            if job[0] == 'shift':
                arg_list[4] = job[2]
            # if job[0] == 'rev' and arg_list[4] != '0':
            if job[0] == 'rev':
                _freq = int(arg_list[2])
                if arg_list[5] == '0':
                    # Change *TO* REV state
                    arg_list[5] = '1'
                    # Shift frequency
                    if arg_list[4] == '1':
                        # Shift +: add offset
                        _freq += int(arg_list[12])
                    if arg_list[4] == '2':
                        # Shift -: add offset
                        _freq -= int(arg_list[12])
                else:
                    # Change *FROM* REV state
                    arg_list[5] = '0'
                    # Unshift frequency
                    if arg_list[4] == '1':
                        _freq -= int(arg_list[12])
                    if arg_list[4] == '2':
                        _freq += int(arg_list[12])
                arg_list[2] = f"{_freq:010d}"
            else:
                pass
            if arg_list[0] == 'ME':
                # MR mode - If GUI, ask user to confirm modification of
                # memory location
                # First, determine whether memory contains a frequency
                # that's allowed as a VFO on this side of the radio
                #    Toggle to VFO mode and get the VFO for this side
                if not self.handle_query(f"VM {SIDE_DICT['inv'][job[1]]},0"):
                    return []
                result = self.handle_query(f"FO {SIDE_DICT['inv'][job[1]]}")
                if not result:
                    return []
                # Toggle back to Memory mode
                if not self.handle_query(f"VM {SIDE_DICT['inv'][job[1]]},1"):
                    return []
                # Is the VFO frequency in the same band as the memory freq?
                if same_frequency_band(int(result[2]), int(arg_list[2])):
                    answer = self.ask('yesnocancel',
                                      f"You are about to modify memory "
                                      f"{int(arg_list[1])}. Proceed?\n\n"
                                      f"Yes:    Modify mem {int(arg_list[1])}\n"
                                      f"No:     Copy mem {int(arg_list[1])} to VFO,\n\t"
                                      f"then modify VFO\n"
                                      f"Cancel: Do nothing")
                else:
                    # Copying memory contents to VFO is not possible
                    # because mem frequency is out of band for VFO on this
                    # side of the radio.
                    answer = self.ask('okcancel',
                                      f"You are about to modify memory "
                                      f"{int(arg_list[1])}. Continue?")
                    if not answer:
                        answer = None
                if answer:
                    # User clicked Yes/OK, so modify memory location
                    msg_queue.put(['WARNING',
                                   f"{stamp()}: WARNING: Modifying "
                                   f"memory {int(arg_list[1])}!"])
                elif answer is None:
                    # User cancelled
                    job[0] = None
                else:
                    # User clicked No
                    # Change to VFO mode and set VFO to data from memory location
                    msg_queue.put(['INFO',
                                   f"{stamp()}: Copying memory "
                                   f"{int(arg_list[1])} contents to VFO"])

                    if not self.handle_query(f"VM {SIDE_DICT['inv'][job[1]]},0"):
                        return []
                    arg_list[0] = 'FO'
                    arg_list[1] = SIDE_DICT['inv'][job[1]]
                    del arg_list[14:]
            if job[0] is not None:
                if not self.handle_query(f"{arg_list[0]} {','.join(arg_list[1:])}"):
                    return []
        elif job[0] in ('beep', 'vhf_aip', 'uhf_aip', 'speed',
                        'backlight', 'apo', 'data', 'timeout'):
            # Get the current menu state
            mu = self.handle_query('MU')
            if not mu:
                return []
            mu_list = list(mu)

            if job[0] == 'backlight':
                if self.state['backlight'] == 'green':
                    desired_color = 'amber'
                else:
                    desired_color = 'green'
                mu_list[MENU_DICT['backlight']['index']] = \
                    MENU_DICT['backlight']['values'][desired_color]
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
            if not self.handle_query(arg):
                return []
            # Workaround for screen refresh bug: Move CTRL to
            # opposite side and back to refresh screen so that
            # radio state updates correctly.
            if job[0] == 'data':
                bc = self.handle_query('BC')
                if not bc:
                    return []
                _error = False
                for _ in range(2):
                    if bc[1] == '0':
                        ctrl_temp = '1'
                    else:
                        ctrl_temp = '0'
                    bc = self.handle_query(f"BC {ctrl_temp},{bc[2]}")
                    if not bc:
                        _error = True
                        # return []
                if _error:
                    return []
        elif job[0] in ('up', 'down'):
            arg_list = get_arg_list()  # Get the channel data for current mode
            if not arg_list or arg_list[0] == 'N':
                return []
            if arg_list[0] in ('FO',):
                frequency = int(arg_list[2])
                step = int(STEP_DICT['map'][arg_list[3]]) * 1000
                if job[0] == 'down':
                    step *= -1
                frequency += step
                _min = float(FREQUENCY_LIMITS[job[1]]['min']) * 1000000
                _max = float(FREQUENCY_LIMITS[job[1]]['max']) * 1000000
                # print(f"min = {_min}, max = {_min}")
                if _min <= frequency <= _max:
                    arg_list[2] = f"{frequency:010d}"
                    arg_list[4] = frequency_shifts(frequency)[0]
                    arg_list[5] = '0'  # Disable reverse
                    # arg_list[6] = '0'  # Set tone status to no tone
                    # arg_list[7] = '0'  # Set CTCSS status to no CTCSS
                    # arg_list[8] = '0'  # Set DCS status to no DCS
                    # arg_list[9] = '08'  # Set tone frequency to default
                    # arg_list[10] = '08'  # Set CTCSS frequency to default
                    # arg_list[11] = '000'  # Set DCS frequency to default
                    arg_list[12] = frequency_shifts(frequency)[1]
                    # arg_list[13] = '0'  # Set mode to FM
                    arg = f"{arg_list[0]} {','.join(arg_list[1:])}"
                    _ans = self.handle_query(arg)
                    if not _ans:
                        return []
                else:
                    msg_queue.put(['ERROR',
                                   f"{stamp()}: Frequency "
                                   f"must be between {float(FREQUENCY_LIMITS[job[1]]['min']):.3f} "
                                   f"and {float(FREQUENCY_LIMITS[job[1]]['max']):.3f} MHz"])
            elif arg_list[0] in ('ME',):
                ctrl_moved_temporarily = False
                if self.state[job[1]]['ctrl'] != 'CTRL':
                    ctrl_moved_temporarily = True
                    ctrl = 0 if self.state['A']['ctrl'] == 'CTRL' else 1
                    ptt = 0 if self.state['A']['ptt'] == 'PTT' else 1
                    restore_arg = f"BC {ctrl},{ptt}"
                    arg = f"BC {SIDE_DICT['inv'][job[1]]},{ptt}"
                    if not self.handle_query(arg):
                        return []
                if 'up' in job[0]:
                    arg = "UP"
                else:
                    arg = "DW"
                if not self.handle_query(arg):
                    return []
                if ctrl_moved_temporarily:
                    # Restore original CTRL state
                    # noinspection PyUnboundLocalVariable
                    if not self.handle_query(restore_arg):
                        return []
            else:
                pass
        elif job[0] in ('ch_number',):
            arg_list = get_arg_list()  # Get the channel data for current mode
            if not arg_list or arg_list[0] == 'N':
                return []
            if arg_list[0] == 'ME':
                arg = f"MR {'0' if job[1] == 'A' else '1'},{job[2]}"
                _ans = self.handle_query(arg)
                if not _ans:
                    return []
                elif _ans[0] == 'N':
                    msg_queue.put(['ERROR',
                                   f"{stamp()}: Memory "
                                   f"{int(job[2])} is empty"])
        elif job[0] in ('micup', 'micdown',):
            if job[0] == 'micup':
                arg = "UP"
            else:
                arg = "DW"
            if not self.handle_query(arg):
                return []
        elif job[0] == 'cat_ptt':
            if not self.handle_query(job[1]):
                return []
        elif job[0] == 'command':
            # Wait for reply_queue to empty before accepting command.
            self.reply_queue.join()
            result = self.handle_query(job[1])
            if not result:
                return []
            else:
                self.reply_queue.put(result)
        else:
            pass
        return job
