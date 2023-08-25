import datetime

__all__ = [
    'XMLRPC_PORT',
    'FREQUENCY_LIMITS',
    'FREQUENCY_BAND_LIMITS',
    'MEMORY_LIMITS',
    'DISP_MODE_DICT',
    'SIDE_DICT',
    'MODE_DICT',
    'MODULATION_DICT',
    'TONE_TYPE_DICT',
    'DCS_FREQUENCY_DICT',
    'TONE_FREQUENCY_DICT',
    'POWER_DICT',
    'STATE_DICT',
    'STEP_DICT',
    'SHIFT_DICT',
    'DATA_BAND_DICT',
    'DATA_SPEED_DICT',
    'TIMEOUT_DICT',
    'APO_DICT',
    'REVERSE_DICT',
    'BACKLIGHT_DICT',
    'TONE_STATUS_DICT',
    'CTCSS_STATUS_DICT',
    'DCS_STATUS_DICT',
    'LOCK_DICT',
    'LOCK_OUT_DICT',
    'PTT_DICT',
    'CTRL_DICT',
    'MENU_DICT',
    'DEFAULT_STEP_VHF',
    'DEFAULT_STEP_UHF',
    'stamp',
    'within_frequency_limits',
    'same_frequency_band',
    'QueryException',
    'UpdateDisplayException',
    'frequency_shifts',
    'VENDOR_ID',
    'PRODUCT_IDS',
    'NEXUS_PTT_GPIO_DICT'
]

XMLRPC_PORT = 12345


class QueryException(Exception):
    """
    Raise this exception when an error occurs while querying radio
    """


class UpdateDisplayException(Exception):
    """
    Raise this exception when an error occurs updating the GUI display
    """


def stamp() -> str:
    """
    Returns string formatted with current time
    :return: String
    """
    return datetime.datetime.now().strftime('%Y%m%dT%H%M%S')


def within_frequency_limits(side: str, freq: float) -> bool:
    """
    Checks to see if a supplied frequency is within Kenwood defined
    ranges for the supplied side (A or B) of the radio.
    :param: side: String containing A or B (the side of the radio)
    :param: freq: Float with frequency in Hz.
    :return: True if within defined range, False otherwise
    """
    _min = FREQUENCY_LIMITS[side]['min']
    _max = FREQUENCY_LIMITS[side]['max']
    if _min <= freq <= _max:
        return True
    else:
        return False


def same_frequency_band(freq1: int, freq2: int) -> bool:
    """
    Check if 2 frequencies in Hz are in the same amateur radio band.
    :param: freq1:  1st Frequency in Hz
    :param: freq2:  2nd Frequency in Hz
    :return: True if both freq1 and freq2 are in the same band,
    False otherwise
    """
    same_band = False
    for freq_range in FREQUENCY_BAND_LIMITS.values():
        if freq1 in range(freq_range['min'], freq_range['max']) \
                and freq2 in range(freq_range['min'],
                                   freq_range['max']):
            same_band = True
            break
    return same_band


def frequency_shifts(frequency: int) -> tuple:
    """
    Given a frequency, it returns a value that translates to whether
    the frequency is simplex (0), + (1) or - (2)
    :param frequency: Integer value of frequency in Hz
    :return: Tuple containing 0, 1 or 2 (simplex, up or down
    respectively) and shift frequency in Hz
    """
    if 145100000 <= frequency <= 145499900:
        return '2', '00600000'
    elif 146000000 <= frequency <= 146399000:
        return '1', '00600000'
    elif 146600000 <= frequency <= 146999000:
        return '2', '00600000'
    elif 147000000 <= frequency <= 147399000:
        return '1', '00600000'
    elif 147600000 <= frequency <= 147999000:
        return '2', '00600000'
    elif 442000000 <= frequency <= 444999000:
        return '1', '05000000'
    elif 447000000 <= frequency <= 449999000:
        return '2', '05000000'
    else:
        return '0', '00000000'


NEXUS_PTT_GPIO_DICT = {'left': '12', 'right': '23'}
GPIO_PTT = ['4', '5', '6', '12', '13', '16', '17', '18', '19', '20',
            '21', '22', '23', '24', '25', '26', '27']
OTHER_PTT = ['digirig', 'cm108']
# GPIO_PTT_DICT = {'none': None, 'cat': None, 'cm108[@index][:1-8]': None, 'cm108:1': None,
#                  'cm108:2': None, 'cm108:3': None, 'cm108:4': None,
#                  'cm108:5': None, 'cm108:6': None, 'cm108:7': None,
#                  'cm108:8': None, 'digirig': None, 'left': 12,
#                  'right': 23, '4': 4, '5': 5, '6': 6, '12': 12,
#                  '13': 13, '16': 16, '17': 17, '18': 18, '19': 19,
#                  '20': 20, '21': 21, '22': 22, '23': 23, '24': 24,
#                  '25': 25, '26': 26, '27': 27
#                  }
FREQUENCY_LIMITS = {'A': {'min': 118.0, 'max': 524.0},
                    'B': {'min': 136.0, 'max': 1300.0}}
MEMORY_LIMITS = {'min': 0, 'max': 999}
FREQUENCY_BAND_LIMITS = {'118': {'min': 118000000, 'max': 136000000},
                         '144': {'min': 136000000, 'max': 200000000},
                         '220': {'min': 200000000, 'max': 300000000},
                         '440': {'min': 400000000, 'max': 524000000},
                         '1200': {'min': 800000000, 'max': 1300000000}}

_disp_mode_dict = {'0': 'Dual', '1': 'Single'}
DISP_MODE_DICT = {'map': _disp_mode_dict,
                  'inv': {v: k for k, v in _disp_mode_dict.items()}}

_side_dict = {'0': 'A', '1': 'B'}
SIDE_DICT = {'map': _side_dict, 'inv': {v: k for k, v in _side_dict.items()}}

_mode_dict = {'0': 'VFO', '1': 'MR', '2': 'CALL', '3': 'WX'}
MODE_DICT = {'map': _mode_dict, 'inv': {v: k for k, v in _mode_dict.items()}}

_modulation_dict = {'0': "FM", '1': "NFM", '2': "AM"}
MODULATION_DICT = {'map': _modulation_dict,
                   'inv': {v: k for k, v in _modulation_dict.items()}}

_tone_type_dict = {'0': "No Tone", '6': 'Tone', '7': 'CTCSS', '8': 'DCS'}
TONE_TYPE_DICT = {'map': _tone_type_dict,
                  'inv': {v: k for k, v in _tone_type_dict.items()}}

_pll_frequency_dict = {'00': "67", '01': "69.3", '02': "71.9",
                       '03': "74.4",
                       '04': "77", '05': "79.7", '06': "82.5",
                       '07': "85.4",
                       '08': "88.5", '09': "91.5", '10': "94.8",
                       '11': "97.4", '12': "100", '13': "103.5",
                       '14': "107.2", '15': "110.9", '16': "114.8",
                       '17': "118.8", '18': "123", '19': "127.3",
                       '20': "131.8", '21': "136.5", '22': "141.3",
                       '23': "146.2", '24': "151.4", '25': "156.7",
                       '26': "162.2", '27': "167.9", '28': "173.8",
                       '29': "179.9", '30': "186.2", '31': "192.8",
                       '32': "203.5", '33': "240.7", '34': "210.7",
                       '35': "218.1", '36': "225.7", '37': "229.1",
                       '38': "233.6", '39': "241.8", '40': "250.3",
                       '41': "254.1"}

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
                       '080': "506", '081': "516", '082': "523", '083': "526",
                       '084': "532", '085': "546", '086': "565", '087': "606",
                       '088': "612", '089': "624", '090': "627", '091': "631",
                       '092': "632", '093': "654", '094': "662", '095': "664",
                       '096': "703", '097': "712", '098': "723", '099': "731",
                       '100': "732", '101': "734", '102': "743", '103': "754"}
DCS_FREQUENCY_DICT = {'map': _dcs_frequency_dict,
                      'inv': {v: k for k, v in _dcs_frequency_dict.items()}}

TONE_FREQUENCY_DICT = {'0': ' ',
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
POWER_DICT = {'map': _power_dict,
              'inv': {v: k for k, v in _power_dict.items()}}

_state_dict = {'0': "OFF", '1': "ON"}
STATE_DICT = {'map': _state_dict,
              'inv': {v: k for k, v in _state_dict.items()}}

_step_dict = {'0': '5', '1': '6.25', '2': '8.33', '3': '10',
              '4': '12.5', '5': '15', '6': '20', '7': '25', '8': '30',
              '9': '50', 'A': '100'}
STEP_DICT = {'map': _step_dict,
             'inv': {v: k for k, v in _step_dict.items()}}

_shift_dict = {'0': 'S', '1': '+', '2': '-'}
SHIFT_DICT = {'map': _shift_dict,
              'inv': {v: k for k, v in _shift_dict.items()}}

_data_band_dict = {'0': 'A', '1': 'B', '2': 'TX A,RX B', '3': 'TX B,RX A'}
DATA_BAND_DICT = {'map': _data_band_dict,
                  'inv': {v: k for k, v in _data_band_dict.items()}}

_data_speed_dict = {'0': '1200', '1': '9600'}
DATA_SPEED_DICT = {'map': _data_speed_dict,
                   'inv': {v: k for k, v in _data_speed_dict.items()}}

_timeout_dict = {'0': '3', '1': '5', '2': '10'}
TIMEOUT_DICT = {'map': _timeout_dict,
                'inv': {v: k for k, v in _timeout_dict.items()}}

_apo_dict = {'0': 'off', '1': '30', '2': '60', '3': '90',
             '4': '120', '5': '180'}
APO_DICT = {'map': _apo_dict,
            'inv': {v: k for k, v in _apo_dict.items()}}

_reverse_dict = {'0': ' ', '1': 'R'}
REVERSE_DICT = {'map': _reverse_dict,
                'inv': {v: k for k, v in _reverse_dict.items()}}

_backlight_dict = {'0': 'amber', '1': 'green'}
BACKLIGHT_DICT = {'map': _backlight_dict,
                  'inv': {v: k for k, v in _backlight_dict.items()}}
_tone_status_dict = _state_dict
TONE_STATUS_DICT = STATE_DICT
_ctcss_status_dict = _state_dict
CTCSS_STATUS_DICT = STATE_DICT
_dcs_status_dict = _state_dict
DCS_STATUS_DICT = STATE_DICT
_lock_dict = _state_dict
LOCK_DICT = STATE_DICT
_lock_out_dict = _state_dict
LOCK_OUT_DICT = STATE_DICT
PTT_DICT = SIDE_DICT
CTRL_DICT = SIDE_DICT
DEFAULT_STEP_VHF = 5
DEFAULT_STEP_UHF = 25

MENU_DICT = {'beep': {'index': 1, 'values': STATE_DICT['inv']},
             'vhf_aip': {'index': 11,
                         'values': STATE_DICT['inv']},
             'uhf_aip': {'index': 12,
                         'values': STATE_DICT['inv']},
             'backlight': {'index': 28, 'values': {'amber': '0',
                                                   'green': '1'}},
             'apo': {'index': 37, 'values': APO_DICT['inv']},
             'data': {'index': 38, 'values': DATA_BAND_DICT['inv']},
             'speed': {'index': 39, 'values': DATA_SPEED_DICT['inv']},
             }

# C-Media CM1xx sound card Vendor ID
VENDOR_ID = 0x0d8c
# C-Media CM1xx product IDs with known GPIO capability
PRODUCT_IDS = (0x8, 0x9, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf,
               0x139, 0x12, 0x13, 0x13a, 0x13c)
