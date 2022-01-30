import io
import re
import sys
from common710 import *
from queue import Queue
from gpiozero import OutputDevice

__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2022, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "2.0.0"
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

    def __init__(self, serial_port: object, nexus_side: str):
        """
        Initializes a BufferedRWPair object that wraps a serial object.
        Wrapping the serial port allows customization of the end-of-line
        character used by the radio
        :param serial_port: Serial object
        """
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
                      'id': ''
                      }
        self.nexus_side = nexus_side
        if self.nexus_side == 'none':
            self.state['gpio'] = None
            self.ptt = None
        else:
            self.state['gpio'] = gpio_ptt_dict[self.nexus_side]
            self.ptt = OutputDevice(self.state['gpio'],
                                    active_high=True,
                                    initial_value=False)
        self.reply_queue = Queue()

    def set_ptt(self, turn_on: bool):
        """
        If radio side (self.ptt object) was supplied as a parameter,
        change the corresponding GPIO pin to True (PTT on) or
        False (PTT off).
        :param turn_on: Desired state of PTT
        :return: None
        """
        if self.ptt is not None:
            if turn_on:
                self.ptt.on()
            else:
                self.ptt.off()

    def get_ptt(self):
        """
        Returns state of PTT GPIO.
        :return: 1 if high, 0 if low or self.ptt is None
        """
        if self.ptt is None:
            return 0
        else:
            return self.ptt.value

    def query(self, request: str) -> tuple:
        """
        Sends CAT command to Kenwood radio and returns reply as a tuple.
        Kenwood CAT commands for the TM-D710G and Tm-V71A begin with a
        2 alpha character string (the command) optionally followed by
        one or more arguments, followed by a carriage return '\r'.
        The radio returns a single '?' if the radio didn't understand
        the command, or returns the original 2 character command,
        followed by the radio's answer: a comma separated string.
        See https://github.com/LA3QMA/TM-V71_TM-D710-Kenwood for
        details.

        :param request: String containing CAT command to send
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
        :param cmd: String to pass to query method
        :return: List containing the output of the radio command, or
                 None if the command failed.
        """
        try:
            result = self.query(cmd)
        except QueryException as error:
            print(f"{stamp()}: No response from radio: {error}",
                  file=sys.stderr)
            return None
        else:
            return result

    def set_id(self, radio_id: str):
        self.state['id'] = radio_id

    def get_id(self) -> str:
        return self.state['id']

    def update_dictionary(self) -> dict:
        """
        Queries the radio for several parameters that are used to
        populate a state dictionary, which maps values to the GUI.
        Several commands are needed to obtain all of the required
        information.

        :return: dictionary with the screen parameters. The dictionary
        is defined and initialized in __init__() method.
        """

        def common_elements(_mode_str: str):
            try:
                if state_dict['map'][result[6]] == "ON":
                    # Tone is set
                    t = "Tone"
                    tf = tone_frequency_dict[t]['map'][result[9]]
                elif state_dict['map'][result[7]] == "ON":
                    # CTCSS is set
                    t = "CTCSS"
                    tf = tone_frequency_dict[t]['map'][result[10]]
                elif state_dict['map'][result[8]] == "ON":
                    # DCS is set
                    t = "DCS"
                    tf = tone_frequency_dict[t]['map'][result[11]]
                else:
                    t = "No Tone"
                    tf = tone_frequency_dict[t]
                # Save tone to state dictionary
                self.state[side_dict['map'][s]]['tone'] = t
                self.state[side_dict['map'][s]]['tone_frequency'] = tf
                # Save shift to state dictionary
                self.state[side_dict['map'][s]]['shift'] = \
                    shift_dict['map'][result[4]]
                # Save reverse status to state dictionary
                self.state[side_dict['map'][s]]['reverse'] = \
                    '{}'.format(reverse_dict['map'][result[5]])
                # Save modulation to state dictionary
                self.state[side_dict['map'][s]]['modulation'] = \
                    '{}'.format(modulation_dict['map'][result[13]])
                # Save the mode to the state dictionary
                self.state[side_dict['map'][s]]['mode'] = _mode_str
                # Save the RX step to state dictionary
                self.state[side_dict['map'][s]]['step'] = \
                    step_dict['map'][result[3]]
                # Save the frequency to the state dictionary
                self.state[side_dict['map'][s]]['frequency'] = \
                    "{:.3f}".format(int(result[2]) / 1000000)
            except IndexError as _:
                raise

        result = None
        result = self.handle_query(f"BC")
        if result is None:
            return None
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
            if result is None:
                return None
            if mode_dict['map'][result[2]] == 'MR':
                # This side is in Memory mode
                # Retrieve memory channel
                result = self.handle_query(f"MR {s}")
                if result is None:
                    return None
                ch_num_raw = result[2]  # Unformatted channel number
                try:
                    # Save the channel number to the state dictionary
                    self.state[side_dict['map'][s]]['ch_number'] = \
                        int(result[2])
                except IndexError as _:
                    raise
                # Retrieve state information for this memory channel
                result = self.handle_query(f"FO {s}")
                if result is None:
                    return None
                # print(f"{stamp()}: {result}", file=sys.stderr)
                try:
                    common_elements('MR')
                except IndexError as _:
                    raise
                # Retrieve the channel name
                result = self.handle_query(f"MN {ch_num_raw}")
                if result is None:
                    return None
                try:
                    if result[0] != 'N':
                        self.state[side_dict['map'][s]]['ch_name'] = \
                            result[2]
                except IndexError as _:
                    raise
            # else:
                #     print(f"{stamp()}: ERROR: Nothing in memory",
                #           file=sys.stderr)
            elif mode_dict['map'][result[2]] == 'VFO':
                # This side is in VFO mode. Retrieve FO data
                result = self.handle_query(f"FO {s}")
                if result is None:
                    return None
                try:
                    common_elements('VFO')
                except IndexError as _:
                    raise
                try:
                    self.state[side_dict['map'][s]]['ch_number'] = '  '
                    self.state[side_dict['map'][s]]['ch_name'] = '      '
                except IndexError as _:
                    raise
            elif mode_dict['map'][result[2]] == 'CALL':
                # This side is in Call mode. Retrieve CC data
                # result = self.handle_query(f"CC {s}")
                result = self.handle_query(f"FO {s}")
                if result is None:
                    return None
                try:
                    common_elements('CALL')
                except IndexError as _:
                    raise
                try:
                    self.state[side_dict['map'][s]]['ch_number'] = '  '
                    self.state[side_dict['map'][s]]['ch_name'] = '      '
                except IndexError as _:
                    raise
            elif mode_dict['map'][result[2]] == 'WX':
                # This side is in Call mode. Retrieve CC data
                # result = self.handle_query(f"CC {s}")
                result = self.handle_query(f"FO {s}")
                if result is None:
                    return None
                try:
                    common_elements('WX')
                except IndexError as _:
                    raise
                try:
                    self.state[side_dict['map'][s]]['ch_number'] = '  '
                    self.state[side_dict['map'][s]]['ch_name'] = '      '
                except IndexError as _:
                    raise
            else:
                pass
            # Power
            result = self.handle_query(f"PC {s}")
            if result is None:
                return None
            try:
                self.state[side_dict['map'][s]]['power'] = power_dict['map'][result[2]]
            except IndexError as _:
                raise
        # Data side
        result = self.handle_query(f"MU")
        if result is None:
            return None
        try:
            if result[38] in ['0', '1']:
                self.state['data_side'] = side_dict['map'][result[38]]
            else:
                self.state['data_side'] = None
            self.state[side_dict['map']['0']]['data'] = \
                'D' if result[38] == '0' else \
                'D-TX' if result[38] == '2' else \
                'D-RX' if result[38] == '3' else \
                ' '
            self.state[side_dict['map']['1']]['data'] = \
                'D' if result[38] == '1' else \
                'D-RX' if result[38] == '2' else \
                'D-TX' if result[38] == '3' else \
                ' '
            self.state['speed'] = data_speed_dict['map'][result[39]]
            self.state['timeout'] = timeout_dict['map'][result[16]]
            self.state['vhf_aip'] = state_dict['map'][result[11]]
            self.state['uhf_aip'] = state_dict['map'][result[12]]
            self.state['backlight'] = backlight_dict['map'][result[28]]
        except IndexError as _:
            raise
        # Lock state
        result = self.handle_query(f"LK")
        if result is None:
            return None
        try:
            self.state['lock'] = lock_dict['map'][result[1]]
        except IndexError as _:
            raise
        return self.state

    def get_dictionary(self) -> dict:
        """
        Returns state of radio state as a dictionary
        :return: state dictionary
        """
        return self.state

    # def run_command(self, command: str) -> str:
    #     """
    #     Adds command to cmd_queue. Monitors ans_queue for the result
    #     :return: String containing command results
    #     """
    #     self.ans_queue.join()
    #     self.cmd_queue.put(['command', command])
    #     result = None
    #     while result is None:
    #         if self.ans_queue.not_empty:
    #             result = self.ans_queue.get()
    #             self.ans_queue.task_done()
    #     return result

    def run_job(self, job: list, msg_queue: Queue) -> list:
        """
        Accepts a job list and executes the corresponding Kenwood
        CAT commmands to fulfill the job task
        :param job: list containing job
        :param msg_queue: Queue to which to send status messages
        :return: The job that was sent as an argument, or if the job
        was a 'command', the result of the command will be the second
        list element. Returns None if the job could not be completed.
        """

        def get_arg_list() -> list:
            if len(job) > 1 and job[1] in ('A', 'B'):
                _arg = side_dict['inv'][job[1]]
                _answer = self.handle_query(f"VM {_arg}")
                if _answer is None:
                    return None
                _, _, _m = list(_answer)
                if _m == '0':  # vfo
                    cmd = 'FO'
                elif _m == '1':  # mr
                    cmd = 'ME'
                    _answer = self.handle_query(f"MR {_arg}")
                    if _answer is None:
                        return None
                    _arg = _answer[2]  # Get the channel number
                elif _m == '2':  # call
                    cmd = 'CC'
                else:  # wx
                    cmd = 'VM'
                    _arg = f"{_arg},3"
                _answer = self.handle_query(f"{cmd} {_arg}")
                if _answer is None:
                    return None
                else:
                    return list(_answer)
            else:
                return None
        if job[0] in ('mode',):  # 'VM' command - mode change requested
            arg = f"VM {side_dict['inv'][job[1]]},{job[2]}"
            if self.handle_query(arg) is None:
                return None
        elif job[0] in ('ptt', 'ctrl'):  # 'BC' command
            answer = self.handle_query("BC")
            if answer is None:
                return None
            ctrl = answer[1]
            ptt = answer[2]
            if job[0] == 'ptt':
                arg = f"BC {ctrl},{side_dict['inv'][job[1]]}"
            else:  # Setting ctrl
                arg = f"BC {side_dict['inv'][job[1]]},{ptt}"
            if self.handle_query(arg) is None:
                return None
        elif job[0] in ('power',):  # 'PC' command
            arg = f"PC {side_dict['inv'][job[1]]},{job[2]}"
            if self.handle_query(arg) is None:
                return None
        elif job[0] in ('lock',):
            answer = self.handle_query("LK")
            if answer is None:
                return None
            arg = "LK {}".format('1' if answer[1] == '0' else '0')
            if self.handle_query(arg) is None:
                return None
        elif job[0] in ('frequency', 'modulation', 'step',
                        'tone', 'tone_frequency', 'rev'):
            arg_list = get_arg_list()
            if arg_list is None or arg_list[0] == 'N':
                return None
            if arg_list[0] not in ['CC', 'FO', 'ME']:
                # WX or unknown mode. Skip this job.
                job[0] = None
            if job[0] in ('tone', 'tone_frequency'):
                same_type = False
                for key, value in tone_type_dict['map'].items():
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
                    _, t, c, d = list(tone_type_dict['map'].keys())
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
                        tone_frequency_dict[current_type]['inv'][job[2]]
            if job[0] == 'frequency':
                arg_list[2] = f"{int(job[2] * 1000000):010d}"
            if job[0] == 'modulation':
                arg_list[13] = job[2]
            if job[0] == 'step':
                arg_list[3] = job[2]
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
                # MR mode
                # Kenwood provides no CAT command for changing the
                # frequency band on a given side. To work around
                # this shortcoming, we must modify the memory channel.
                msg_queue.put(['WARNING',
                               f"{stamp()}: WARNING: Modifying "
                               f"memory {int(arg_list[1])}!"])
            if job[0] is not None:
                if self.handle_query(f"{arg_list[0]} {','.join(arg_list[1:])}") is None:
                    return None
        elif job[0] in ('beep', 'vhf_aip', 'uhf_aip', 'speed',
                        'backlight', 'apo', 'data', 'timeout'):
            # Get the current menu state
            mu = self.handle_query('MU')
            if mu is None:
                return None
            mu_list = list(mu)

            if job[0] == 'backlight':
                if self.state['backlight'] == 'green':
                    desired_color = 'amber'
                else:
                    desired_color = 'green'
                mu_list[menu_dict['backlight']['index']] = \
                    menu_dict['backlight']['values'][desired_color]
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
            if self.handle_query(arg) is None:
                return None
            # Workaround for screen refresh bug: Move CTRL to
            # opposite side and back to refresh screen so that
            # radio state updates correctly.
            if job[0] == 'data':
                bc = self.handle_query('BC')
                if bc is None:
                    return None
                _error = False
                for _ in range(2):
                    if bc[1] == '0':
                        ctrl_temp = '1'
                    else:
                        ctrl_temp = '0'
                    bc = self.handle_query(f"BC {ctrl_temp},{bc[2]}")
                    if bc is None:
                        _error = True
                        return None
                if _error:
                    return None
        elif job[0] in ('up', 'down'):
            arg_list = get_arg_list()  # Get the channel data for current mode
            if arg_list is None or arg_list[0] == 'N':
                return None
            channel = 0
            if arg_list[0] == 'FO':
                frequency = int(arg_list[2])
                step = int(step_dict['map'][arg_list[3]]) * 1000
                if job[0] == 'down':
                    step *= -1
                frequency += step
                _min = float(frequency_limits[job[1]]['min']) * 1000000
                _max = float(frequency_limits[job[1]]['max']) * 1000000
                # print(f"min = {_min}, max = {_min}")
                if _min <= frequency <= _max:
                    arg_list[2] = f"{frequency:010d}"
            elif arg_list[0] == 'ME':
                channel = int(arg_list[1])
                step = 1
                if job[0] == 'down':
                    step *= -1
                channel += step
                _min = memory_limits['min']
                _max = memory_limits['max']
                if _min <= channel <= _max:
                    arg_list.clear()
                    arg_list = ['MR', '0' if job[1] == 'A' else '1',
                                f"{channel:03d}"]
            else:
                pass
            arg = f"{arg_list[0]} {','.join(arg_list[1:])}"
            _ans = self.handle_query(arg)
            if _ans is None:
                return None
            elif arg_list[0] == 'MR' and _ans[0] == 'N':
                msg_queue.put(['ERROR',
                               f"{stamp()}: Memory "
                               f"{channel} is empty"])
        elif job[0] in ('ch_number',):
            arg_list = get_arg_list()  # Get the channel data for current mode
            if arg_list is None or arg_list[0] == 'N':
                return None
            if arg_list[0] == 'ME':
                arg = f"MR {'0' if job[1] == 'A' else '1'},{job[2]}"
                _ans = self.handle_query(arg)
                if _ans is None:
                    return None
                elif _ans[0] == 'N':
                    msg_queue.put(['ERROR',
                                   f"{stamp()}: Memory "
                                   f"{int(job[2])} is empty"])
        elif job[0] in ('micup', 'micdown',):
            if job[0] == 'micup':
                arg = "UP"
            else:
                arg = "DW"
            if self.handle_query(arg) is None:
                return None
        elif job[0] == 'command':
            # Wait for reply_queue to empty before accepting command.
            self.reply_queue.join()
            result = self.handle_query(job[1])
            if result is None:
                return None
            else:
                self.reply_queue.put(result)
        else:
            pass
        return job
