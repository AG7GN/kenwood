import io
import re
import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk
import datetime


# noinspection PyTypeChecker
class KenwoodTMCat(object):
    """
    Kenwood TM-D710G and TM-V71A CAT implementation

    This class implements the CAT interface, enabling a computer to
    control the radio via a serial interface. The Kenwood CAT commands
    are documented at https://github.com/LA3QMA/TM-V71_TM-D710-Kenwood
    """

    _disp_mode_dict = {'0': 'Dual', '1': 'Single'}
    disp_mode_dict = {'map': _disp_mode_dict,
                      'inv': {v: k for k, v in _disp_mode_dict.items()}}

    _side_dict = {'0': 'A', '1': 'B'}
    side_dict = {'map': _side_dict, 'inv': {v: k for k, v in _side_dict.items()}}

    _mode_dict = {'0': 'VFO', '1': 'MR', '2': 'CALL', '3': 'WX'}
    mode_dict = {'map': _mode_dict, 'inv': {v: k for k, v in _mode_dict.items()}}

    _modulation_dict = {'0': "FM", '1': "NFM", '2': "AM"}
    modulation_dict = {'map': _modulation_dict,
                       'inv': {v: k for k, v in _modulation_dict.items()}}

    _tone_type_dict = {'0': "No Tone", '6': 'Tone', '7': 'CTCSS', '8': 'DCS'}
    tone_type_dict = {'map': _tone_type_dict,
                      'inv': {v: k for k, v in _tone_type_dict.items()}}

    _pll_frequency_dict = {'01': "67", '02': "69.3", '03': "71.9",
                           '04': "74.4",
                           '05': "77", '06': "79.7", '07': "82.5",
                           '08': "85.4",
                           '09': "88.5", '10': "91.5", '11': "94.8",
                           '12': "97.4", '13': "100", '14': "103.5",
                           '15': "107.2", '16': "110.9", '17': "114.8",
                           '18': "118.8", '19': "123", '20': "127.3",
                           '21': "131.8", '22': "136.5", '23': "141.3",
                           '24': "146.2", '25': "151.4", '26': "156.7",
                           '27': "162.2", '28': "167.9", '29': "173.8",
                           '30': "179.9", '31': "186.2", '32': "192.8",
                           '33': "203.5", '34': "240.7", '35': "210.7",
                           '36': "218.1", '37': "225.7", '38': "229.1",
                           '39': "233.6", '40': "241.6", '41': "250.3",
                           '42': "254.1"}

    _dcs_frequency_dict = {'000': "23", '001': "25", '002': "26", '003': "31",
                           '004': "32", '005': "36", '006': "43", '007': "47",
                           '008': "51", '009': "53", '010': "54", '011': "65",
                           '012': "71", '013': "72", '014': "73", '015': "74",
                           '016': "114", '017': "115", '018': "116", '019': "122",
                           '020': "125", '021': "131", '022': "132", '023': "134",
                           '024': "143", '025': "145", '026': "152", '027': "155",
                           '028': "156", '029': "162", '030': "165", '031': "172",
                           '032': "174", '033': "205", '034': "212", '035': "223",
                           '036': "225", '037': "226", '038': "243", '039': "244",
                           '040': "245", '041': "246", '042': "251", '043': "252",
                           '044': "255", '045': "261", '046': "263", '047': "265",
                           '048': "266", '049': "271", '050': "274", '051': "306",
                           '052': "311", '053': "315", '054': "325", '055': "331",
                           '056': "332", '057': "343", '058': "346", '059': "351",
                           '060': "356", '061': "364", '062': "365", '063': "371",
                           '064': "411", '065': "412", '066': "413", '067': "423",
                           '068': "431", '069': "432", '070': "445", '071': "446",
                           '072': "452", '073': "454", '074': "455", '075': "462",
                           '076': "464", '077': "465", '078': "466", '079': "503",
                           '080': "506", '081': "516", '082': "523", '083': "565",
                           '084': "532", '085': "546", '086': "565", '087': "606",
                           '088': "612", '089': "624", '090': "627", '091': "631",
                           '092': "632", '093': "654", '094': "662", '095': "664",
                           '096': "703", '097': "712", '098': "723", '099': "731",
                           '100': "732", '101': "734", '102': "743", '103': "754"}
    dcs_frequency_dict = {'map': _dcs_frequency_dict,
                          'inv': {v: k for k, v in _dcs_frequency_dict.items()}}

    tone_frequency_dict = {'0': ' ',
                           'No Tone': ' ',
                           '6': {'map': _pll_frequency_dict,
                                 'inv': {v: k for k, v in _pll_frequency_dict.items()}},
                           'Tone': {'map': _pll_frequency_dict,
                                    'inv': {v: k for k, v in _pll_frequency_dict.items()}},
                           '7': {'map': _pll_frequency_dict,
                                 'inv': {v: k for k, v in _pll_frequency_dict.items()}},
                           'CTCSS': {'map': _pll_frequency_dict,
                                     'inv': {v: k for k, v in _pll_frequency_dict.items()}},
                           '8': {'map': _dcs_frequency_dict,
                                 'inv': {v: k for k, v in _dcs_frequency_dict.items()}},
                           'DCS': {'map': _dcs_frequency_dict,
                                   'inv': {v: k for k, v in _dcs_frequency_dict.items()}},
                           }

    _power_dict = {'0': 'H', '1': 'M', '2': 'L'}
    power_dict = {'map': _power_dict,
                  'inv': {v: k for k, v in _power_dict.items()}}

    _state_dict = {'0': "OFF", '1': "ON"}
    state_dict = {'map': _state_dict,
                  'inv': {v: k for k, v in _state_dict.items()}}

    _step_dict = {'0': '5', '1': '6.25', '2': '28.33', '3': '10',
                  '4': '12.5', '5': '15', '6': '20', '7': '25', '8': '30',
                  '9': '50', 'A': '100'}
    step_dict = {'map': _step_dict,
                 'inv': {v: k for k, v in _step_dict.items()}}

    _shift_dict = {'0': 'S', '1': '+', '2': '-'}
    shift_dict = {'map': _shift_dict,
                  'inv': {v: k for k, v in _shift_dict.items()}}

    _data_band_dict = {'0': 'A', '1': 'B', '2': 'TX A,RX B', '3': 'TX B,RX A'}
    data_band_dict = {'map': _data_band_dict,
                      'inv': {v: k for k, v in _data_band_dict.items()}}

    _data_speed_dict = {'0': '1200', '1': '9600'}
    data_speed_dict = {'map': _data_speed_dict,
                       'inv': {v: k for k, v in _data_speed_dict.items()}}

    _timeout_dict = {'0': '3', '1': '5', '2': '10'}
    timeout_dict = {'map': _timeout_dict,
                    'inv': {v: k for k, v in _timeout_dict.items()}}

    _apo_dict = {'0': 'off', '1': '30', '2': '60', '3': '90',
                 '4': '120', '5': '180'}
    apo_dict = {'map': _apo_dict,
                'inv': {v: k for k, v in _apo_dict.items()}}

    _reverse_dict = {'0': ' ', '1': 'R'}
    reverse_dict = {'map': _reverse_dict,
                    'inv': {v: k for k, v in _reverse_dict.items()}}

    _backlight_dict = {'0': 'amber', '1': 'green'}
    backlight_dict = {'map': _backlight_dict,
                      'inv': {v: k for k, v in _backlight_dict.items()}}
    _tone_status_dict = _state_dict
    tone_status_dict = state_dict
    _ctcss_status_dict = _state_dict
    ctcss_status_dict = state_dict
    _dcs_status_dict = _state_dict
    dcs_status_dict = state_dict
    _lock_dict = _state_dict
    lock_dict = state_dict
    _lock_out_dict = _state_dict
    lock_out_dict = state_dict
    ptt_dict = side_dict
    ctrl_dict = side_dict

    menu_dict = {'beep': {'index': 1, 'values': state_dict['inv']},
                 'vhf_aip': {'index': 11,
                             'values': state_dict['inv']},
                 'uhf_aip': {'index': 12,
                             'values': state_dict['inv']},
                 'backlight': {'index': 28, 'values': {'amber': '0',
                                                       'green': '1'}},
                 'apo': {'index': 37, 'values': apo_dict['inv']},
                 'data': {'index': 38, 'values': data_band_dict['inv']},
                 'speed': {'index': 39, 'values': data_speed_dict['inv']},
                 }

    def __init__(self, _ser: object):
        """
        Initializes a BufferedRWPair object that wraps a serial object.
        Wrapping the serial port allows customization of the end-of-line
        character used by the radio
        :param _ser: Serial object
        """
        self.ser = _ser
        sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser),
                               newline='\r')
        self.sio = sio
        self.display = {'A': {'mode': None, 'ch_name': None,
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
                        }
        self.serial_port_error = False

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
        except Exception as e:
            print(f"{stamp()}: Serial Port ERROR: {e}")
            self.serial_port_error = True
            return ()
        if answer and answer != '?':
            # Remove trailing \r and convert string to tuple
            return tuple(answer[:-1].split(','))
        else:
            return ()

    def get_radio_status(self) -> dict:
        """
        Queries the radio for several parameters that are used to
        populate the GUI representation of the radio's screen. Several
        commands are needed to obtain all of the required information.

        :return: dictionary with the screen parameters. The dictionary
        is defined and initialized in __init__()
        """

        def common_elements(_mode_str: str):
            if self._state_dict[result[6]] == "ON":
                # Tone is set
                t = "Tone"
                tf = self.tone_frequency_dict[t]['map'][result[9]]
            elif self._state_dict[result[7]] == "ON":
                # CTCSS is set
                t = "CTCSS"
                tf = self.tone_frequency_dict[t]['map'][result[10]]
            elif self._state_dict[result[8]] == "ON":
                # DCS is set
                t = "DCS"
                tf = self.tone_frequency_dict[t]['map'][result[11]]
            else:
                t = "No Tone"
                tf = self.tone_frequency_dict[t]
            # Save tone to display dictionary
            self.display[self._side_dict[s]]['tone'] = t
            self.display[self._side_dict[s]]['tone_frequency'] = tf
            # Save shift to display dictionary
            self.display[self._side_dict[s]]['shift'] = \
                self._shift_dict[result[4]]
            # Save reverse status to display dictionary
            # self.display[self._side_dict[s]]['reverse'] = \
            #     '{}'.format(self._reverse_dict[result[5]])
            # Save modulation to display dictionary
            self.display[self._side_dict[s]]['modulation'] = \
                '{}'.format(self.modulation_dict['map'][result[13]])
            # Save the mode to the display dictionary
            self.display[self._side_dict[s]]['mode'] = _mode_str
            # Save the frequency to the display dictionary
            self.display[self._side_dict[s]]['frequency'] = \
                "{:.3f}".format(int(result[2]) / 1000000)
            # Save the RX step to display dictionary
            self.display[self._side_dict[s]]['step'] = \
                self._step_dict[result[3]]

        # result = self.query(f"DL")
        # if not result:
        #     print(f"{stamp()}: ERROR: No response from radio")
        #     return {}
        # if result[1] == '0':
        #     sides = ('0', '1')
        # else:
        #     sides = ('0',)
        sides = ('0', '1')
        result = self.query(f"BC")
        if not result:
            print(f"{stamp()}: ERROR: No response from radio")
            return {}
        self.display['A']['ctrl'] = 'CTRL' if result[1] == '0' else '   '
        self.display['B']['ctrl'] = 'CTRL' if result[1] == '1' else '   '
        self.display['A']['ptt'] = 'PTT' if result[2] == '0' else '   '
        self.display['B']['ptt'] = 'PTT' if result[2] == '1' else '   '
        for s in sides:  # '0' = A side, '1' = B side
            # Determine current mode (VFO, Memory, Call)
            result = self.query(f"VM {s}")
            if not result:
                print(f"{stamp()}: ERROR: No response from radio")
                return {}
            if self._mode_dict[result[2]] == 'MR':
                # This side is in Memory mode
                # Retrieve memory channel
                result = self.query(f"MR {s}")
                if not result:
                    print(f"{stamp()}: ERROR: No response from radio")
                    return {}
                ch_num_raw = result[2]  # Unformatted channel number
                # Save the channel number to the display dictionary
                self.display[self._side_dict[s]]['ch_number'] = \
                    int(result[2])
                # Retrieve display information for this memory channel
                result = self.query(f"FO {s}")
                if not result:
                    print(f"{stamp()}: ERROR: No response from radio")
                    return {}
                common_elements('MR')
                # Retrieve the channel name
                result = self.query(f"MN {ch_num_raw}")
                if not result:
                    print(f"{stamp()}: ERROR: No response from radio")
                    return {}
                self.display[self._side_dict[s]]['ch_name'] = \
                    result[2]
            elif self._mode_dict[result[2]] == 'VFO':
                # This side is in VFO mode. Retrieve FO data
                result = self.query(f"FO {s}")
                if not result:
                    print(f"{stamp()}: ERROR: No response from radio")
                    return {}
                common_elements('VFO')
                self.display[self._side_dict[s]]['ch_number'] = '  '
                self.display[self._side_dict[s]]['ch_name'] = '      '
            elif self._mode_dict[result[2]] == 'CALL':
                # This side is in Call mode. Retrieve CC data
                # result = self.query(f"CC {s}")
                result = self.query(f"FO {s}")
                if not result:
                    print(f"{stamp()}: ERROR: No response from radio")
                    return {}
                common_elements('CALL')
                self.display[self._side_dict[s]]['ch_number'] = '  '
                self.display[self._side_dict[s]]['ch_name'] = '      '
            elif self._mode_dict[result[2]] == 'WX':
                # This side is in Call mode. Retrieve CC data
                # result = self.query(f"CC {s}")
                result = self.query(f"FO {s}")
                if not result:
                    print(f"{stamp()}: ERROR: No response from radio")
                    return {}
                common_elements('WX')
                self.display[self._side_dict[s]]['ch_number'] = '  '
                self.display[self._side_dict[s]]['ch_name'] = '      '
            else:
                pass
            # Power
            result = self.query(f"PC {s}")
            if not result:
                print(f"{stamp()}: ERROR: No response from radio")
                return {}
            self.display[self._side_dict[s]]['power'] = self._power_dict[result[2]]
            result = self.query(f"AS {s}")
            if not result:
                print(f"{stamp()}: ERROR: No response from radio")
                return {}
            self.display[self._side_dict[s]]['reverse'] = self._reverse_dict[result[2]]
        # Data side
        result = self.query(f"MU")
        if not result:
            print(f"{stamp()}: ERROR: No response from radio")
            return {}
        self.display[self._side_dict['0']]['data'] = \
            'D' if result[38] == '0' else \
            'D-TX' if result[38] == '2' else \
            'D-RX' if result[38] == '3' else \
            ' '
        self.display[self._side_dict['1']]['data'] = \
            'D' if result[38] == '1' else \
            'D-RX' if result[38] == '2' else \
            'D-TX' if result[38] == '3' else \
            ' '
        self.display['speed'] = self._data_speed_dict[result[39]]
        self.display['timeout'] = self._timeout_dict[result[16]]
        self.display['vhf_aip'] = self._state_dict[result[11]]
        self.display['uhf_aip'] = self._state_dict[result[12]]
        self.display['backlight'] = self._backlight_dict[result[28]]
        # Lock state
        result = self.query(f"LK")
        if not result:
            print(f"{stamp()}: ERROR: No response from radio")
            return {}
        self.display['lock'] = self._lock_dict[result[1]]
        return self.display


def close(self):
    # self.sio.flush()
    self.sio.close()


class KenwoodTMScreen:
    """
    GUI that simulates a Kenwood TM-D710G screen. Will also work with a
    TM-V71A.
    """
    _green = "#CCFF33"
    _amber = "#FF9933"
    _screen_bg_color = _green

    _default_font = ("Tahoma", 18)
    _frequency_font = ("Tahoma", 40)
    _button_font = ("Tahoma", 16)
    _scr = {'row': 0, 'col': 0}  # screen starts at row 0, column 0

    frequency_limits = {'A': {'min': 118.0, 'max': 524.0},
                        'B': {'min': 136.0, 'max': 1300.0}}
    memory_limits = {'min': 0, 'max': 999}

    # labels dictionary tuples: (row, column, columnspan,
    # rowspan, sticky, font, tooltip)
    labels_dict = {'A': {'ptt': (_scr['row'], _scr['col'], 1, 1,
                                 'w', _default_font, "Push-to-talk"),
                         'ctrl': (_scr['row'], _scr['col'] + 1, 1, 1,
                                  'w', _default_font, "Control"),
                         'tone': (_scr['row'], _scr['col'] + 2, 1, 1,
                                  'e', _default_font, "Tone Type: Tone, DCS, or CTCSS\nClick to change"),
                         'tone_frequency': (_scr['row'], _scr['col'] + 3, 1, 1,
                                            'w', _default_font, "Tone, DCS, or CTCSS frequency\nClick to change"),
                         'shift': (_scr['row'], _scr['col'] + 4, 1, 1,
                                   'w', _default_font, "TX shift direction\n'S' is simplex"),
                         'reverse': (_scr['row'], _scr['col'] + 5, 1,
                                     1, 'e', _default_font, "'R': TX and RX frequencies reversed"),
                         'modulation': (_scr['row'], _scr['col'] + 6,
                                        1, 1, 'e', _default_font, "Modulation: FM, NFM or AM\nClick to change"),
                         'power': (_scr['row'] + 1, _scr['col'], 1, 1,
                                   'w', _default_font, "Power: High, Medium, Low"),
                         'data': (_scr['row'] + 1, _scr['col'] + 6, 1,
                                  1, 'e', _default_font, "'D' means data on this side.\nClick to move to other side"),
                         'ch_name': (_scr['row'] + 1, _scr['col'] + 1,
                                     2, 1, 'e', _default_font, "Memory Channel Name"),
                         'ch_number': (_scr['row'] + 1,
                                       _scr['col'] + 4, 1, 1,
                                       'w', _default_font, "Memory Channel Number\nClick to change"),
                         'mode': (_scr['row'] + 4, _scr['col'],
                                  1, 1, 'sw', _default_font, "Mode: VFO, MR, CALL or WX\nClick to change"),
                         'frequency': (_scr['row'] + 2, _scr['col'] + 1,
                                       5, 3, 'nsw', _frequency_font, "Frequency in MHz\nClick to change"),
                         'step': (_scr['row'] + 4, _scr['col'] + 6,
                                  1, 1, 'se', _default_font, "Step size in KHz\nClick to change"),
                         },
                   'B': {'ptt': (_scr['row'], _scr['col'] + 8, 1,
                                 1, 'w', _default_font, "Push-to-talk"),
                         'ctrl': (_scr['row'], _scr['col'] + 9, 1,
                                  1, 'w', _default_font, "Control"),
                         'tone': (_scr['row'], _scr['col'] + 10, 1,
                                  1, 'e', _default_font, "Tone Type: Tone, DCS, or CTCSS\nClick to change"),
                         'tone_frequency': (_scr['row'], _scr['col'] + 11, 1,
                                            1, 'w', _default_font, "Tone, DCS, or CTCSS frequency\nClick to change"),
                         'shift': (_scr['row'], _scr['col'] + 12, 1,
                                   1, 'w', _default_font, "TX shift direction\n'S' is simplex"),
                         'reverse': (_scr['row'], _scr['col'] + 13, 1,
                                     1, 'e', _default_font, "'R': TX and RX frequencies reversed"),
                         'modulation': (_scr['row'], _scr['col'] + 14,
                                        1, 1, 'e', _default_font, "Modulation: FM, NFM or AM\nClick to change"),
                         'power': (_scr['row'] + 1, _scr['col'] + 8, 1,
                                   1, 'w', _default_font, "Power: High, Medium, Low\nClick to change"),
                         'data': (_scr['row'] + 1, _scr['col'] + 14, 1,
                                  1, 'e', _default_font, "'D' means data on this side.\nClick to move to other side"),
                         'ch_name': (_scr['row'] + 1, _scr['col'] + 9,
                                     2, 1, 'e', _default_font, "Memory Channel Name"),
                         'ch_number': (_scr['row'] + 1,
                                       _scr['col'] + 12, 1, 1,
                                       'w', _default_font, "Memory Channel Number\nClick to change"),
                         'mode': (_scr['row'] + 4, _scr['col'] + 8, 1,
                                  1, 'sw', _default_font, "Mode: VFO, MR, CALL, or WX\nClick to change"),
                         'frequency': (_scr['row'] + 2,
                                       _scr['col'] + 9, 5, 3,
                                       'nsw', _frequency_font, "Frequency in MHz\nClick to change"),
                         'step': (_scr['row'] + 4, _scr['col'] + 14,
                                  1, 1, 'se', _default_font, "Step size in KHz\nClick to change"),
                         }
                   }

    def __init__(self, master, version, shared_queue):
        self.version = version
        self.master = master
        self._q = shared_queue
        # Make the root window
        w = 785
        h = 320
        ws = master.winfo_screenwidth()
        hs = master.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        master.geometry(f"{w}x{h}+{x}+{y}")
        master.title(f"Kenwood TM-D710G/TM-V71A Controller {version}")
        master['padx'] = 5
        master['pady'] = 5
        # Make the master frame
        content_frame = tk.Frame(master)
        content_frame.grid(column=0, row=0)
        bottom_btns_frames = {'A': {'row': 5, 'col': 0, 'cspan': 7},
                              'B': {'row': 5, 'col': 8, 'cspan': 7}
                              }
        self.bottom_btn_frame = {'A': {}, 'B': {}}
        bottom_btns = {'ptt': "Click to move PTT to this side",
                       'ctrl': "Click to move control to this side",
                       'rev': "Click to toggle Reverse TX",
                       'down': "Click to decrease channel # or frequency",
                       'up': "Click to increase channel # or frequency",
                       }
        screen_field = {'A': {}, 'B': {}}
        self.screen_label = {'A': {}, 'B': {}}
        self.side_btn = {'A': {}, 'B': {}}
        self.bottom_btn = {'A': {}, 'B': {}}

        # Make the screen frame
        self.screen_frame = tk.Frame(master=content_frame,
                                     relief=tk.SUNKEN, borderwidth=5,
                                     bg=self._screen_bg_color,
                                     width=650)
        self.screen_frame.grid(column=0, row=0, rowspan=6,
                               columnspan=15)

        # Make a vertical line separating the A and B sides of screen
        self.side_separator_frame = tk.Frame(master=self.screen_frame,
                                             padx=5, pady=3,
                                             bg=self._screen_bg_color)
        self.side_separator_frame.grid(column=7, row=0, rowspan=6,
                                       sticky='ns')
        separator = tk.Canvas(master=self.side_separator_frame,
                              width=2, height=2, borderwidth=0,
                              highlightthickness=0, bg='grey')
        separator.pack(fill=tk.BOTH, expand=True)

        for side in bottom_btns_frames.keys():
            self.bottom_btn_frame[side] = tk.Frame(master=self.screen_frame,
                                                   borderwidth=0,
                                                   bg=self._screen_bg_color)
            self.bottom_btn_frame[side].grid(column=bottom_btns_frames[side]['col'],
                                             row=bottom_btns_frames[side]['row'],
                                             columnspan=bottom_btns_frames[side]['cspan'],
                                             sticky='ew')
            for key, value in self.labels_dict[side].items():
                screen_field[side][key] = \
                    tk.Frame(master=self.screen_frame)
                screen_field[side][key].grid(row=value[0],
                                             column=value[1],
                                             columnspan=value[2],
                                             rowspan=value[3],
                                             sticky=value[4])
                self.screen_label[side][key] = tk.Label(
                    master=screen_field[side][key],
                    text=key[0:2], fg="black",
                    bg=self._screen_bg_color, font=value[5])
                if key in ('frequency', 'tone', 'tone_frequency',
                           'ch_name', 'mode', 'ch_number',
                           'power', 'data', 'modulation', 'step'):
                    self.screen_label[side][key]. \
                        bind("<Button-1>",
                             lambda _, s=side,
                             k=key: self.widget_clicked(side=s, key=k))
                ToolTip(widget=self.screen_label[side][key],
                        text=value[6],
                        x_offset=5, y_offset=40)
                self.screen_label[side][key]. \
                    pack(fill=tk.BOTH, expand=True)

            bottom_btn_start_col = bottom_btns_frames[side]['col']
            for b, val in bottom_btns.items():
                # print(b, side)
                self.bottom_btn[side][b] = \
                    tk.Button(master=self.bottom_btn_frame[side],
                              text=b.upper(),
                              font=self._button_font,
                              command=lambda _b=b, _s=side:
                              self._q.put([_b, _s]))
                self.bottom_btn[side][b]. \
                    grid(row=bottom_btns_frames[side]['row'],
                         column=bottom_btn_start_col)
                bottom_btn_start_col += 1
                ToolTip(widget=self.bottom_btn[side][b],
                        text=bottom_btns[b],
                        x_offset=5, y_offset=35)

            bg_button = tk.Button(master=content_frame,
                                  text="Backlight Color",
                                  font=self._button_font,
                                  command=lambda:
                                  self._q.put(['backlight', ]))
            bg_button.grid(row=6, column=0, sticky='nsew')
            ToolTip(widget=bg_button,
                    text="Click to toggle screen background color",
                    x_offset=5, y_offset=35)

            self.timeout_button = \
                tk.Button(master=content_frame,
                          text="TX Timeout",
                          font=self._button_font,
                          command=lambda:
                          self.widget_clicked(key='timeout'))
            self.timeout_button.grid(row=6, column=1, sticky='nsew')
            ToolTip(widget=self.timeout_button,
                    text="Click to set TX timeout (minutes)",
                    x_offset=5, y_offset=35)

            micdown_button = tk.Button(master=content_frame,
                                       text="Mic Down",
                                       font=self._button_font,
                                       command=lambda:
                                       self._q.put(['micdown', ]))
            micdown_button.grid(row=6, column=2, sticky='nsew')
            ToolTip(widget=micdown_button,
                    text="Click to emulate 'Down' button on mic",
                    x_offset=5, y_offset=35)
            micup_button = tk.Button(master=content_frame,
                                     text="Mic Up",
                                     font=self._button_font,
                                     command=lambda:
                                     self._q.put(['micup', ]))
            micup_button.grid(row=6, column=3, sticky='nsew')
            ToolTip(widget=micup_button,
                    text="Click to emulate 'Up' button on mic",
                    x_offset=5, y_offset=35)

            self.lock_button = tk.Button(master=content_frame,
                                         text="Lock is",
                                         font=self._button_font,
                                         command=lambda:
                                         self._q.put(['lock', ]))
            self.lock_button.grid(row=7, column=0, sticky='nsew')
            ToolTip(widget=self.lock_button,
                    text="Click to toggle radio controls lock",
                    x_offset=5, y_offset=35)

            self.vhf_aip_button = tk.Button(master=content_frame,
                                            text="VHF AIP is",
                                            font=self._button_font,
                                            command=lambda:
                                            self._q.put(['vhf_aip', ]))
            self.vhf_aip_button.grid(row=7, column=1, sticky='nsew')
            ToolTip(widget=self.vhf_aip_button,
                    text="Click to toggle VHF Advanced Intercept Point",
                    x_offset=5, y_offset=35)

            self.uhf_aip_button = tk.Button(master=content_frame,
                                            text="VHF AIP is",
                                            font=self._button_font,
                                            command=lambda:
                                            self._q.put(['uhf_aip', ]))
            self.uhf_aip_button.grid(row=7, column=2, sticky='nsew')
            ToolTip(widget=self.uhf_aip_button,
                    text="Click to toggle UHF Advanced Intercept Point",
                    x_offset=5, y_offset=35)

            self.speed_button = tk.Button(master=content_frame,
                                          text="Tap",
                                          font=self._button_font,
                                          command=lambda:
                                          self.widget_clicked(key='speed'))
            self.speed_button.grid(row=7, column=3, sticky='nsew')
            ToolTip(widget=self.speed_button,
                    text="Click to toggle data audio tap (1200 or 9600)",
                    x_offset=5, y_offset=35)

            quit_button = tk.Button(master=content_frame,
                                    text='Quit',
                                    font=self._button_font,
                                    command=lambda:
                                    self._q.put(['quit', ]))
            quit_button.grid(row=8, column=0, columnspan=14, sticky='nsew')

    def widget_clicked(self, **kwargs):

        if 'side' in kwargs.keys():
            s = kwargs['side']
        else:
            s = None
        if 'key' in kwargs.keys():
            k = kwargs['key']
        else:
            k = None
        if s is None:
            print(f"{stamp()}: Widget '{k}' clicked.")
        else:
            print(f"{stamp()}: Widget '{k}' on side {s} clicked. Value is "
                  f"'{self.screen_label[s][k].cget('text')}'")
        if k == 'frequency':
            user_input = \
                simpledialog.askfloat(
                    prompt=f"Enter desired frequency in MHz for "
                           f"side {s}",
                    title=f"{s} side frequency",
                    initialvalue=float(self.screen_label[s][k].cget('text')),
                    minvalue=self.frequency_limits[s]['min'],
                    maxvalue=self.frequency_limits[s]['max'])
            if user_input:
                self._q.put([k, s, user_input])
        elif k == 'ch_number':
            user_input = \
                simpledialog.askinteger(
                    prompt=f"Enter desired channel number for "
                           f"side {s}",
                    title=f"{s} side Frequency",
                    initialvalue=int(self.screen_label[s][k].cget('text')),
                    minvalue=self.memory_limits['min'],
                    maxvalue=self.memory_limits['max'])
            if user_input:
                self._q.put([k, s, f"{int(user_input):03d}"])
        elif k == 'tone':
            RadioPopup(widget=self.screen_label[s][k],
                       title=f"  Side {s} Tone Type  ",
                       label=k, side=s,
                       initial_value=KenwoodTMCat.tone_type_dict['inv'][self.screen_label[s][k].cget('text')],
                       content=KenwoodTMCat.tone_type_dict['inv'],
                       job_q=self._q)
        elif k == 'tone_frequency':
            # We need to know which tone frequencies to present to user
            tone_type = self.screen_label[s]['tone'].cget('text')
            if tone_type in ('Tone', 'CTCSS'):
                content = list(KenwoodTMCat.tone_frequency_dict[tone_type]['map'].values())
            elif tone_type == 'DCS':
                content = list(KenwoodTMCat.dcs_frequency_dict['map'].values())
            else:  # No tones in use
                content = None
            if content is not None:
                ComboPopup(widget=self.screen_label[s][k],
                           title=f"  Side {s} Tone (Hz)  ",
                           label=k, side=s,
                           content=list(KenwoodTMCat.tone_frequency_dict[tone_type]['map'].values()),
                           job_q=self._q)
        elif k == 'mode':
            RadioPopup(widget=self.screen_label[s][k],
                       title=f"    Side {s} Mode     ",
                       label=k, side=s,
                       initial_value=KenwoodTMCat.mode_dict['inv'][self.screen_label[s][k].cget('text')],
                       content=KenwoodTMCat.mode_dict['inv'],
                       job_q=self._q)
        elif k == 'power':
            RadioPopup(widget=self.screen_label[s][k],
                       title=f"   Side {s} TX Power  ",
                       label=k, side=s,
                       initial_value=KenwoodTMCat.power_dict['inv'][self.screen_label[s][k].cget('text')],
                       content=KenwoodTMCat.power_dict['inv'],
                       job_q=self._q)
        elif k == 'modulation':
            RadioPopup(widget=self.screen_label[s][k],
                       title=f"  Side {s} Modulation  ",
                       label=k, side=s,
                       initial_value=KenwoodTMCat.modulation_dict['inv'][self.screen_label[s][k].cget('text')],
                       content=KenwoodTMCat.modulation_dict['inv'],
                       job_q=self._q)
        elif k == 'step':
            RadioPopup(widget=self.screen_label[s][k],
                       title=f"Side {s} Step Size (KHz)",
                       label=k, side=s,
                       initial_value=KenwoodTMCat.step_dict['inv'][self.screen_label[s][k].cget('text')],
                       content=KenwoodTMCat.step_dict['inv'],
                       job_q=self._q)
        elif k == 'speed':
            initial_value = KenwoodTMCat.data_speed_dict['inv'][self.speed_button.cget('text')]
            RadioPopup(widget=self.speed_button,
                       title=f"   Set data audio tap   ",
                       label=k,
                       initial_value=initial_value,
                       content=KenwoodTMCat.data_speed_dict['inv'],
                       job_q=self._q)
        elif k == 'timeout':
            current_timeout = re.sub("[^0-9]", "", self.timeout_button.cget('text'))
            RadioPopup(widget=self.timeout_button,
                       title=f"  TX Timeout (minutes)  ",
                       label=k,
                       initial_value=KenwoodTMCat.timeout_dict['inv'][current_timeout],
                       content=KenwoodTMCat.timeout_dict['inv'],
                       job_q=self._q)
        elif k == 'data':
            if s == 'A':
                self._q.put([k, '1'])
            else:
                self._q.put([k, '0'])
        else:
            pass

    def change_bg(self, **kwargs):
        if 'color' in kwargs.keys():
            if kwargs['color'] == 'amber':
                self._screen_bg_color = self._amber
            else:
                self._screen_bg_color = self._green
        else:  # No color specified - just make it the other color
            if self._screen_bg_color == self._green:
                self._screen_bg_color = self._amber
            else:
                self._screen_bg_color = self._green
        self.screen_frame. \
            config(background=self._screen_bg_color)
        self.side_separator_frame. \
            config(background=self._screen_bg_color)
        for side in ('A', 'B'):
            for key in self.labels_dict[side]:
                self.screen_label[side][key]. \
                    config(background=self._screen_bg_color)
            self.bottom_btn_frame[side].config(background=self._screen_bg_color)


class Popup(object):
    """
    Class that creates a popup window for entering data
    """

    def __init__(self, **kwargs):
        self.widget = kwargs['widget']
        self.title = kwargs['title']
        self.label = kwargs['label']
        self.side = kwargs.get('side', None)
        self.content = kwargs['content']
        self.job_q = kwargs['job_q']
        self.initial_value = kwargs.get('initial_value', self.widget.cget('text'))
        self.selected = tk.StringVar(None, self.initial_value)
        # self.selected = tk.StringVar(None, kwargs['initial_value'])
        self.pop = tk.Toplevel(self.widget)
        self.pop.bind('<Escape>', lambda e: self.pop.destroy())
        self.pop.title(self.title)
        self.pop.geometry("+{}+{}".format(self.widget.winfo_rootx(),
                                          self.widget.winfo_rooty()))
        self.font = kwargs.get('font', ("Tahoma", 16))
        # self.pop.after(2000, lambda: self.pop.focus_force())
        self.pop.wm_attributes("-topmost", True)

    def selection(self, data):
        if self.side is None:
            self.job_q.put([self.label, data])
        else:
            self.job_q.put([self.label, self.side, data])
        try:
            self.pop.destroy()
        except AttributeError:
            print(f"{stamp()}: Popup already closed")


class ComboPopup(Popup):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        combo = ttk.Combobox(self.pop,
                             text=self.title,
                             values=self.content,
                             textvariable=self.selected,
                             width=len(self.title),
                             font=self.font)
        combo.pack(anchor='w', padx=5, pady=5)
        combo.bind("<<ComboboxSelected>>", lambda _: self.selection(combo.get()))


class RadioPopup(Popup):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for descr, index in self.content.items():
            tk.Radiobutton(self.pop,
                           text=descr, variable=self.selected,
                           value=index, indicatoron=False,
                           font=self.font,
                           width=len(self.title),
                           command=lambda:
                           self.selection(self.selected.get())). \
                pack(anchor='w', padx=5)


class ToolTip(object):
    """
    Class that creates tool tips on Kenwood simulated screen
    """

    def __init__(self, widget, text, x_offset, y_offset):
        self.widget = widget
        self.text = text
        self.x = x_offset
        self.y = y_offset
        self.tooltipwindow = None
        widget.bind('<Enter>', lambda _: self.show_tool_tip())
        widget.bind('<Leave>', lambda _: self.hide_tool_tip())

    def show_tool_tip(self):
        self.tooltipwindow = tw = tk.Toplevel(self.widget)
        # window without border and no normal means of closing
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+{}+{}".format(
            self.widget.winfo_rootx() + self.x,
            self.widget.winfo_rooty() + self.y))
        tk.Label(tw, text=self.text, background="#ffffe0",
                 relief='solid', borderwidth=1).pack()
        tw.update_idletasks()  # Needed for MacOS
        tw.lift()  # Needed for MacOS

    def hide_tool_tip(self):
        tw = self.tooltipwindow
        if tw:
            tw.destroy()
        self.tooltipwindow = None


def stamp():
    return datetime.datetime.now().strftime('%Y%m%dT%H%M%S')


if __name__ == "__main__":
    import serial
    import sys
    import argparse
    from serial.tools import list_ports

    device = '/dev/cu.usbserial-RT1RVT5Y'
    baud = 57600

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port",
                        choices=[comport.device for comport
                                 in serial.tools.list_ports.comports()],
                        type=str, default=device,
                        help="Serial port connected to radio")
    parser.add_argument("-b", "--baudrate",
                        choices=[300, 1200, 2400, 4800, 9600, 19200,
                                 38400, 57600],
                        type=int, default=baud,
                        help="Serial port speed (must match radio)")
    port_info = parser.parse_args()
    print(f"{stamp()}: Using {port_info.__dict__['port']} @ "
          f"{port_info.__dict__['baudrate']} bps")

    try:
        ser = serial.Serial(**port_info.__dict__, timeout=0.1,
                            writeTimeout=0.1)
    except serial.serialutil.SerialException:
        print(f"{stamp()}: ERROR: Could not open serial port")
        sys.exit(1)

    radio = KenwoodTMCat(ser)
