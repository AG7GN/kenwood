import re
import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import ttk
from tkinter import scrolledtext
from common710 import stamp
from common710 import FREQUENCY_LIMITS
from common710 import MEMORY_LIMITS
from common710 import TONE_TYPE_DICT
from common710 import TONE_FREQUENCY_DICT
from common710 import DCS_FREQUENCY_DICT
from common710 import SHIFT_DICT
from common710 import MODE_DICT
from common710 import POWER_DICT
from common710 import MODULATION_DICT
from common710 import STEP_DICT
from common710 import DATA_SPEED_DICT
from common710 import TIMEOUT_DICT
from common710 import UpdateDisplayException

__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2023, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "2.0.4"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"


class Display(object):
    """
    GUI that simulates a Kenwood TM-D710G screen. Will also work with a
    TM-V71A.
    """
    _green = "#CCFF33"
    _amber = "#FF9933"
    _screen_bg_color = _green
    scale = {'normal': {'w': 790, 'h': 420, 'frame_w': 650,
                        'default_font_size': 18,
                        'frequency_font_size': 40,
                        'button_font_size': 16,
                        'message_font_size': 12,
                        'console_w': 70, 'console_h': 5,
                        'x_offset': 5, 'y_offset': 35},
             'small': {'w': 545, 'h': 285, 'frame_w': 200,
                       'default_font_size': 10,
                       'frequency_font_size': 20,
                       'button_font_size': 8,
                       'message_font_size': 8,
                       'console_w': 60, 'console_h': 5,
                       'x_offset': 5, 'y_offset': 25},
             }
    # screen starts at row 0, column 0
    _scr = {'row': 0, 'col': 0, 'columns': 16, 'B_side_col': 8}

    def __init__(self, **kwargs):
        default_kwargs = {'title': 'Kenwood TM-D710G/TM-V71A Controller'}
        kwargs = {**default_kwargs, **kwargs}
        self.master = kwargs['root']
        self.title = kwargs['title']
        self.version = kwargs['version']
        self.cmd_q = kwargs['cmd_queue']
        self.info = kwargs['info']
        size = kwargs.get('size', 'normal')
        self.current_color = None
        self._default_font = ("Tahoma",
                              Display.scale[size]['default_font_size'])
        self._frequency_font = ("Tahoma",
                                Display.scale[size]['frequency_font_size'])
        self._button_font = ("Tahoma",
                             Display.scale[size]['button_font_size'])
        # labels dictionary tuples: (row, column, columnspan,
        # rowspan, sticky, font, tooltip)

        self.labels_dict = {'ptt': {'row': Display._scr['row'],
                                    'column': Display._scr['col'],
                                    'columnspan': 1,
                                    'rowspan': 1,
                                    'sticky': 'w',
                                    'font': self._default_font,
                                    'tooltip': "Push-to-talk",
                                    'relief': 'flat'},
                            'ctrl': {'row': Display._scr['row'],
                                     'column': Display._scr['col'] + 1,
                                     'columnspan': 1,
                                     'rowspan': 1,
                                     'sticky': 'w',
                                     'font': self._default_font,
                                     'tooltip': "Control",
                                     'relief': 'flat'},
                            'tone': {'row': Display._scr['row'],
                                     'column': Display._scr['col'] + 2,
                                     'columnspan': 1,
                                     'rowspan': 1,
                                     'sticky': 'e',
                                     'font': self._default_font,
                                     'tooltip': "Tone Type: Tone, DCS, or CTCSS.\nClick to change",
                                     'relief': 'flat'},
                            'tone_frequency': {'row': Display._scr['row'],
                                               'column': Display._scr['col'] + 3,
                                               'columnspan': 1,
                                               'rowspan': 1,
                                               'sticky': 'w',
                                               'font': self._default_font,
                                               'tooltip': "Tone, DCS, or CTCSS frequency.\nClick to change",
                                               'relief': 'flat'},
                            'shift': {'row': Display._scr['row'],
                                      'column': Display._scr['col'] + 4,
                                      'columnspan': 1,
                                      'rowspan': 1,
                                      'sticky': 'w',
                                      'font': self._default_font,
                                      'tooltip': "TX shift direction.\n'S' is simplex",
                                      'relief': 'flat'},
                            'reverse': {'row': Display._scr['row'],
                                        'column': Display._scr['col'] + 5,
                                        'columnspan': 1,
                                        'rowspan': 1,
                                        'sticky': 'e',
                                        'font': self._default_font,
                                        'tooltip': "'R': TX and RX frequencies reversed",
                                        'relief': 'flat'},
                            'modulation': {'row': Display._scr['row'],
                                           'column': Display._scr['col'] + 6,
                                           'columnspan': 1,
                                           'rowspan': 1,
                                           'sticky': 'e',
                                           'font': self._default_font,
                                           'tooltip': "Modulation: FM, NFM or AM.\nClick to change",
                                           'relief': 'flat'},
                            'power': {'row': Display._scr['row'] + 1,
                                      'column': Display._scr['col'],
                                      'columnspan': 1,
                                      'rowspan': 1,
                                      'sticky': 'w',
                                      'font': self._default_font,
                                      'tooltip': "Power: High, Medium, Low.\nClick to change",
                                      'relief': 'flat'},
                            'data': {'row': Display._scr['row'] + 1,
                                     'column': Display._scr['col'] + 6,
                                     'columnspan': 1,
                                     'rowspan': 1,
                                     'sticky': 'e',
                                     'font': self._default_font,
                                     'tooltip': "'D' means data on this side.\nClick to change",
                                     'relief': 'flat'},
                            'ch_name': {'row': Display._scr['row'] + 1,
                                        'column': Display._scr['col'] + 1,
                                        'columnspan': 2,
                                        'rowspan': 1,
                                        'sticky': 'e',
                                        'font': self._default_font,
                                        'tooltip': "Memory Channel Name",
                                        'relief': 'flat'},
                            'ch_number': {'row': Display._scr['row'] + 1,
                                          'column': Display._scr['col'] + 4,
                                          'columnspan': 1,
                                          'rowspan': 1,
                                          'sticky': 'w',
                                          'font': self._default_font,
                                          'tooltip': "Memory Channel Number.\nClick to go to different memory",
                                          'relief': 'flat'},
                            'mode': {'row': Display._scr['row'] + 4,
                                     'column': Display._scr['col'],
                                     'columnspan': 1,
                                     'rowspan': 1,
                                     'sticky': 'sw',
                                     'font': self._default_font,
                                     'tooltip': "Mode: VFO, MR, CALL or WX.\nClick to change",
                                     'relief': 'flat'},
                            'frequency': {'row': Display._scr['row'] + 2,
                                          'column': Display._scr['col'] + 1,
                                          'columnspan': 5,
                                          'rowspan': 3,
                                          'sticky': 'nsw',
                                          'font': self._frequency_font,
                                          'tooltip': "Frequency in MHz.\nClick to change",
                                          'relief': 'flat'},
                            'step': {'row': Display._scr['row'] + 4,
                                     'column': Display._scr['col'] + 6,
                                     'columnspan': 1,
                                     'rowspan': 1,
                                     'sticky': 'se',
                                     'font': self._default_font,
                                     'tooltip': "Step size in KHz.\nClick to change",
                                     'relief': 'flat'},
                            }

        # Make the root window
        w = Display.scale[size]['w']
        h = Display.scale[size]['h']
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        if kwargs['initial_location'] is None:
            x = (ws // 2) - (w // 2)
            y = (hs // 2) - (h // 2)
        else:
            x = kwargs['initial_location'][0]
            y = kwargs['initial_location'][1]
        # self.master.geometry(f"{w}x{h}+{x}+{y}")
        self.master.geometry(f"+{x}+{y}")
        self.master.title(f"{self.title} {self.version}")
        self.master['padx'] = 5
        self.master['pady'] = 5
        self.master.resizable(False, False)

        # Make the master frame
        content_frame = tk.Frame(self.master)
        content_frame.grid(column=0, row=0)
        sides = ('A', 'B')
        screen_btn_frames_dict = {'A': {'row': 5, 'col': 0, 'cspan': 7},
                                  'B': {'row': 5, 'col': 8, 'cspan': 7}
                                  }
        self.screen_btn_frame = {'A': {}, 'B': {}}
        self.screen_btns_dict = {'PTT': {'tooltip': "Click to move PTT to this side"},
                                 'CTRL':
                                     {'tooltip': "Click to move CTRL to this side"},
                                 'REV':
                                     {'tooltip': "Click to toggle Reverse TX"},
                                 'DOWN': {'tooltip':
                                          "Click to decrease channel # or frequency"},
                                 'UP': {'tooltip':
                                        "Click to increase channel # or frequency"},
                                 }
        screen_field = {'A': {}, 'B': {}}
        self.screen_label = {'A': {}, 'B': {}}
        self.side_btn = {'A': {}, 'B': {}}
        screen_btn = {'A': {}, 'B': {}}

        screen_btn_style = ttk.Style()
        screen_btn_style.configure('button.TLabel', font=self._button_font)

        self.screen_frame = tk.Frame(master=content_frame,
                                     relief=tk.SUNKEN, borderwidth=5,
                                     bg=Display._screen_bg_color)
        self.screen_frame.grid(column=0, row=0, rowspan=6,
                               columnspan=14)

        self.msg_frame = ttk.Frame(master=content_frame,
                                   borderwidth=5)
        self.msg_frame.grid(column=0, row=8, columnspan=14)
        self.msg = MessageConsole(frame=self.msg_frame,
                                  scale=Display.scale[size],
                                  queue=kwargs['msg_queue'])

        # Make a vertical line separating the A and B sides of screen
        self.side_separator_frame_style = ttk.Style()
        self.side_separator_frame_style.configure('side_separator.TFrame',
                                                  background=Display._screen_bg_color)
        self.side_separator_frame = tk.Frame(master=self.screen_frame,
                                             padx=5, pady=3,
                                             bg=Display._screen_bg_color)

        self.side_separator_frame.grid(column=7, row=0, rowspan=6,
                                       sticky='ns')
        separator = tk.Canvas(master=self.side_separator_frame,
                              width=2, height=2, borderwidth=0,
                              highlightthickness=0, bg='grey')
        separator.pack(fill=tk.BOTH, expand=True)

        column_offset = 0
        for side in sides:
            self.screen_btn_frame[side] = \
                ttk.Frame(master=self.screen_frame)
            self.screen_btn_frame[side].\
                grid(row=screen_btn_frames_dict[side]['row'],
                     column=screen_btn_frames_dict[side]['col'],
                     columnspan=screen_btn_frames_dict[side]['cspan'])
            for key, value in self.labels_dict.items():
                screen_field[side][key] = \
                    ttk.Frame(master=self.screen_frame)
                screen_field[side][key].grid(row=value['row'],
                                             column=value['column'] + column_offset,
                                             columnspan=value['columnspan'],
                                             rowspan=value['rowspan'],
                                             sticky=value['sticky'],
                                             ipadx=2)
                self.screen_label[side][key] = tk.Label(
                    master=screen_field[side][key],
                    text=key[0:2], fg="black",
                    bg=Display._screen_bg_color, font=value['font'])
                if key in ('frequency', 'tone', 'tone_frequency',
                           'ch_name', 'shift', 'mode', 'ch_number',
                           'power', 'data', 'modulation', 'step'):
                    self.screen_label[side][key]. \
                        bind("<Button-1>",
                             lambda _, s=side,
                             k=key: self.widget_clicked(side=s,
                                                        key=k))
                ToolTip(widget=self.screen_label[side][key],
                        text=value['tooltip'],
                        x_offset=Display.scale[size]['x_offset'],
                        y_offset=Display.scale[size]['y_offset'] + 10)
                self.screen_label[side][key]. \
                    pack(fill=tk.BOTH, expand=True)
            column_offset += Display._scr['B_side_col']

            # Buttons (actually labels for maximum compatibility
            # across operating systems) PTT, CTRL, REV, DOWN, UP.
            btn_column = 0
            for key in self.screen_btns_dict.keys():
                screen_btn[side][key] = \
                    tk.Label(master=self.screen_btn_frame[side],
                             text=key, relief="raised",
                             font=self._button_font
                             )
                screen_btn[side][key].grid(column=btn_column, row=0,
                                           ipadx=2, padx=1)
                btn_column += 1
                screen_btn[side][key]. \
                    bind("<Button-1>",
                         lambda _, s=side, k=key:
                         self.widget_clicked(side=s, key=k))
                ToolTip(widget=screen_btn[side][key],
                        text=self.screen_btns_dict[key]['tooltip'],
                        x_offset=Display.scale[size]['x_offset'],
                        y_offset=Display.scale[size]['y_offset'])

            button_frame = ttk.Frame(master=content_frame)
            button_frame.grid(row=6,
                              column=0,
                              columnspan=14,
                              rowspan=2, pady=2)

            bg_button = ttk.Label(master=button_frame,
                                  text="Backlight Color",
                                  anchor="center",
                                  style='button.TLabel', relief="raised",
                                  padding=1)
            bg_button.grid(row=0, column=0, sticky='nsew', padx=1, ipadx=1)
            bg_button.bind("<Button-1>",
                           lambda _: self.cmd_q.put(['backlight', ]))
            ToolTip(widget=bg_button,
                    text="Click to toggle screen background color",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.timeout_button = \
                ttk.Label(master=button_frame,
                          text="TX TO", relief="raised",
                          anchor="center",
                          style='button.TLabel')

            self.timeout_button.grid(row=0, column=1, sticky='nsew',
                                     padx=1, ipadx=1)
            self.timeout_button.bind("<Button-1>", lambda _:
                                     self.widget_clicked(key='timeout'))
            ToolTip(widget=self.timeout_button,
                    text="Click to set TX timeout (minutes)",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            micdown_button = ttk.Label(master=button_frame,
                                       text="Mic Down", relief="raised",
                                       anchor="center",
                                       style='button.TLabel')

            micdown_button.grid(row=0, column=2, sticky='nsew',
                                padx=1, ipadx=1)
            micdown_button.bind("<Button-1>", lambda _:
                                self.cmd_q.put(['micdown', ]))
            ToolTip(widget=micdown_button,
                    text="Click to emulate 'Down' button on mic",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            micup_button = ttk.Label(master=button_frame,
                                     text="Mic Up", relief="raised",
                                     anchor="center",
                                     style='button.TLabel')

            micup_button.grid(row=0, column=3, sticky='nsew', padx=1,
                              ipadx=1)
            micup_button.bind("<Button-1>", lambda _:
                              self.cmd_q.put(['micup', ]))
            ToolTip(widget=micup_button,
                    text="Click to emulate 'Up' button on mic",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.lock_button = ttk.Label(master=button_frame,
                                         text="Lock is", relief="raised",
                                         anchor="center",
                                         style='button.TLabel')

            self.lock_button.grid(row=1, column=0, sticky='nsew', padx=1,
                                  ipadx=1)
            self.lock_button.bind("<Button-1>", lambda _:
                                  self.cmd_q.put(['lock', ]))
            ToolTip(widget=self.lock_button,
                    text="Click to toggle radio controls lock",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.vhf_aip_button = ttk.Label(master=button_frame,
                                            text="VHF AIP is",
                                            relief="raised",
                                            anchor="center",
                                            style='button.TLabel')
            self.vhf_aip_button.grid(row=1, column=1, sticky='nsew', padx=1,
                                     ipadx=1)
            self.vhf_aip_button.bind("<Button-1>", lambda _:
                                     self.cmd_q.put(['vhf_aip', ]))
            ToolTip(widget=self.vhf_aip_button,
                    text="Click to toggle VHF Advanced Intercept Point",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.uhf_aip_button = ttk.Label(master=button_frame,
                                            text="VHF AIP is",
                                            relief="raised",
                                            anchor="center",
                                            style='button.TLabel')
            self.uhf_aip_button.grid(row=1, column=2, sticky='nsew', padx=1,
                                     ipadx=1)
            self.uhf_aip_button.bind("<Button-1>", lambda _:
                                     self.cmd_q.put(['uhf_aip', ]))
            ToolTip(widget=self.uhf_aip_button,
                    text="Click to toggle UHF Advanced Intercept Point",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.speed_button = ttk.Label(master=button_frame,
                                          text="Tap",
                                          relief="raised",
                                          anchor="center",
                                          style='button.TLabel')
            self.speed_button.grid(row=1, column=3, sticky='nsew', padx=1,
                                   ipadx=1)
            self.speed_button.bind("<Button-1>", lambda _:
                                   self.widget_clicked(key='speed'))
            ToolTip(widget=self.speed_button,
                    text="Click to toggle data audio tap (1200 or 9600)",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            info_quit_frame = ttk.Frame(master=content_frame)
            info_quit_frame.grid(row=13,
                                 column=0,
                                 columnspan=14,
                                 pady=2)

            info_button = tk.Button(master=info_quit_frame,
                                    text='Rig Information',
                                    font=self._button_font,
                                    command=lambda:
                                    self.showinfo())
            info_button.grid(row=0, column=0)

            quit_button = tk.Button(master=info_quit_frame,
                                    text='Quit',
                                    font=self._button_font,
                                    command=lambda:
                                    self.cmd_q.put(['quit', ]))
            quit_button.grid(row=0, column=1)

    def showinfo(self):
        """
        Message box with radio information
        """
        info = f"Model:\t{self.info['model']}\n" \
               f"Serial:\t{self.info['serial']}\n" \
               f"Body FW:\t{self.info['firmware']['main']}\n" \
               f"Head FW: {self.info['firmware']['panel']}"
        messagebox.showinfo(title="Rig Info",
                            message=info,
                            parent=self.master)

    def widget_clicked(self, **kwargs):
        """
        Manage user input when certain labels are clicked
        :param kwargs: 'side': side of the radio (A or B)
        'key': Label that was clicked
        """
        _label = None
        s = kwargs.get('side', None)
        k = kwargs.get('key', None)
        if s is None:
            self.msg.queue.put(['INFO', f"{stamp()}: '{k}' clicked."])
        else:
            if k in self.screen_btns_dict.keys():
                self.cmd_q.put([k.lower(), s])
                self.msg.queue.put(['INFO', f"{stamp()}: '{k}' on side "
                                            f"{s} clicked."])
                return
            else:
                _label = str(self.screen_label[s][k].cget('text'))
                self.msg.queue.put(['INFO', f"{stamp()}: '{k}' on side "
                                    f"{s} clicked. Value is '{_label}'"])
        if k == 'frequency':
            user_input = \
                simpledialog.askfloat(
                    prompt=f"Enter desired frequency in MHz for "
                           f"side {s}",
                    title=f"Side {s} frequency",
                    initialvalue=float(self.screen_label[s][k].cget('text')),
                    minvalue=FREQUENCY_LIMITS[s]['min'],
                    maxvalue=FREQUENCY_LIMITS[s]['max'])
            if user_input is not None:
                self.cmd_q.put([k, s, user_input])
        elif k == 'ch_number':
            if _label and _label.strip():
                user_input = \
                    simpledialog.askinteger(
                        prompt=f"Enter desired channel number for "
                               f"side {s}",
                        title=f"Side {s} channel",
                        initialvalue=int(self.screen_label[s][k].cget('text')),
                        minvalue=MEMORY_LIMITS['min'],
                        maxvalue=MEMORY_LIMITS['max'])
                if user_input is not None:
                    self.cmd_q.put([k, s, f"{int(user_input):03d}"])
            else:
                self.msg.queue.put(['ERROR', f"{stamp()}: Side {s} is not "
                                             "in memory mode. Cannot set memory location."])
        elif k == 'tone':
            RadioPopup(widget=self.screen_label[s][k],
                       # title=f"  Side {s} Tone Type  ",
                       pop_label=f"Side {s} Tone Type",
                       label=k,
                       side=s,
                       font=self._default_font,
                       initial_value=TONE_TYPE_DICT['inv'][self.screen_label[s][k].cget('text')],
                       content=TONE_TYPE_DICT['inv'],
                       job_q=self.cmd_q)
        elif k == 'tone_frequency':
            # We need to know which tone frequencies to present to user
            tone_type = self.screen_label[s]['tone'].cget('text')
            if tone_type in ('Tone', 'CTCSS'):
                content = list(TONE_FREQUENCY_DICT[tone_type]['map'].values())
            elif tone_type == 'DCS':
                content = list(DCS_FREQUENCY_DICT['map'].values())
            else:  # No tones in use
                content = None
            if content is not None:
                ComboPopup(widget=self.screen_label[s][k],
                           # title=f"  Side {s} Tone (Hz)  ",
                           pop_label=f"Side {s} Tone (Hz)",
                           label=k,
                           side=s,
                           font=self._default_font,
                           content=list(TONE_FREQUENCY_DICT[tone_type]['map'].values()),
                           job_q=self.cmd_q)
        elif k == 'shift':
            RadioPopup(widget=self.screen_label[s][k],
                       # title=f"    Side {s} Shift     ",
                       pop_label=f"Side {s} Shift",
                       label=k,
                       side=s,
                       font=self._default_font,
                       initial_value=SHIFT_DICT['inv'][self.screen_label[s][k].cget('text')],
                       content=SHIFT_DICT['inv'],
                       job_q=self.cmd_q)
        elif k == 'mode':
            RadioPopup(widget=self.screen_label[s][k],
                       # title=f"    Side {s} Mode     ",
                       pop_label=f"Side {s} Mode",
                       label=k,
                       side=s,
                       font=self._default_font,
                       initial_value=MODE_DICT['inv'][self.screen_label[s][k].cget('text')],
                       content=MODE_DICT['inv'],
                       job_q=self.cmd_q)
        elif k == 'power':
            RadioPopup(widget=self.screen_label[s][k],
                       # title=f"   Side {s} TX Power  ",
                       pop_label=f"Side {s} TX Power",
                       label=k,
                       side=s,
                       font=self._default_font,
                       initial_value=POWER_DICT['inv'][self.screen_label[s][k].cget('text')],
                       content=POWER_DICT['inv'],
                       job_q=self.cmd_q)
        elif k == 'modulation':
            RadioPopup(widget=self.screen_label[s][k],
                       # title=f"  Side {s} Modulation  ",
                       pop_label=f"Side {s} Modulation",
                       label=k,
                       side=s,
                       font=self._default_font,
                       initial_value=MODULATION_DICT['inv'][self.screen_label[s][k].cget('text')],
                       content=MODULATION_DICT['inv'],
                       job_q=self.cmd_q)
        elif k == 'step':
            RadioPopup(widget=self.screen_label[s][k],
                       pop_label=f"Side {s} Step Size (KHz)",
                       label=k,
                       side=s,
                       font=self._default_font,
                       initial_value=STEP_DICT['inv'][self.screen_label[s][k].cget('text')],
                       content=STEP_DICT['inv'],
                       job_q=self.cmd_q)
        elif k == 'speed':
            initial_value = DATA_SPEED_DICT['inv'][re.sub("[^0-9]",
                                                          "",
                                                          self.speed_button.cget('text'))]
            RadioPopup(widget=self.speed_button,
                       # title=f"   Set data audio tap   ",
                       pop_label=f"Set data audio tap",
                       label=k,
                       initial_value=initial_value,
                       font=self._default_font,
                       content=DATA_SPEED_DICT['inv'],
                       job_q=self.cmd_q)
        elif k == 'timeout':
            current_timeout = re.sub("[^0-9]", "", self.timeout_button.cget('text'))
            RadioPopup(widget=self.timeout_button,
                       # title=f"  TX Timeout (minutes)  ",
                       pop_label=f"TX Timeout (minutes)",
                       label=k,
                       font=self._default_font,
                       initial_value=TIMEOUT_DICT['inv'][current_timeout],
                       content=TIMEOUT_DICT['inv'],
                       job_q=self.cmd_q)
        elif k == 'data':
            if s == 'A':
                self.cmd_q.put([k, '1'])
            else:
                self.cmd_q.put([k, '0'])
        else:
            pass

    def change_bg(self, **kwargs):
        """
        Toggle radio's background color and update onscreen display
        to match
        :param kwargs: 'color': green or amber
        """
        if 'color' in kwargs.keys():
            if kwargs['color'] == 'amber':
                Display._screen_bg_color = self._amber
            else:
                Display._screen_bg_color = self._green
        else:  # No color specified - just make it the other color
            if Display._screen_bg_color == self._green:
                Display._screen_bg_color = self._amber
            else:
                Display._screen_bg_color = self._green
        self.screen_frame. \
            config(background=Display._screen_bg_color)
        self.side_separator_frame. \
            config(background=Display._screen_bg_color)
        for side in ('A', 'B'):
            for key in self.labels_dict.keys():
                self.screen_label[side][key]. \
                    config(background=Display._screen_bg_color)

    def update_display(self, data: dict):
        """
        Refresh the onscreen display
        :param data:
        :return:
        """
        try:
            for s in ('A', 'B'):
                for key in data[s]:
                    self.screen_label[s][key]. \
                        config(text=data[s][key])
                    self.screen_label[s][key]. \
                        pack(fill=tk.BOTH, expand=True)
                    self.screen_label[s][key].update()
            if self.current_color != data['backlight']:
                # Update state to current background color
                self.change_bg(color=data['backlight'])
                self.current_color = data['backlight']
            self.timeout_button.config(text=f"TX TO is {data['timeout']}")
            self.timeout_button.update()
            self.lock_button.config(text=f"Lock is {data['lock']}")
            self.lock_button.update()
            self.vhf_aip_button.config(text=f"VHF AIP is {data['vhf_aip']}")
            self.vhf_aip_button.update()
            self.uhf_aip_button.config(text=f"UHF AIP is {data['uhf_aip']}")
            self.uhf_aip_button.update()
            self.speed_button.config(text=f"Audio tap is {data['speed']}")
            self.speed_button.update()
        except KeyError as _:
            raise UpdateDisplayException("Error updating display")


class MessageConsole(object):
    """
    Object to create a scrolling console pane in the onscreen display
    to which messages are printed.
    """
    def __init__(self, **kwargs):
        self.frame = kwargs['frame']
        scale = kwargs['scale']
        _msg_console_font = ("TkFixedFont", scale['message_font_size'])
        self.msg_text = scrolledtext.ScrolledText(master=self.frame,
                                                  state='disabled',
                                                  wrap=tk.WORD,
                                                  width=scale['console_w'],
                                                  height=scale['console_h'],
                                                  font=_msg_console_font)
        self.msg_text.grid(row=0, column=0, columnspan=14, rowspan=5, pady=0)
        self.msg_text.tag_configure('INFO', foreground='blue')
        self.msg_text.tag_configure('WARNING', foreground='black',
                                    background='orange')
        self.msg_text.tag_configure('ERROR', foreground='white',
                                    background='red')
        self.queue = kwargs['queue']
        self.frame.after(100, self.msg_q_reader)

    def display_message(self, msg):
        """
        Print messages to the console pane
        :param msg: String containing text to print
        """
        _level, _m = msg
        self.msg_text.configure(state='normal')
        self.msg_text.insert(tk.END, _m + '\n', _level)
        self.msg_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.msg_text.yview(tk.END)

    def msg_q_reader(self):
        """
        Manage message queue
        """
        while not self.queue.empty():
            message = self.queue.get(block=False)
            self.display_message(message)
            self.queue.task_done()
        self.frame.after(100, self.msg_q_reader)


class Popup(object):
    """
    Creates a popup window for entering data
    """

    def __init__(self, **kwargs):
        self.widget = kwargs['widget']
        self.title = kwargs.get('title', '.')
        self.label = kwargs['label']
        self.side = kwargs.get('side', None)
        self.content = kwargs['content']
        self.job_q = kwargs['job_q']
        self.initial_value = kwargs.get('initial_value', self.widget.cget('text'))
        self.selected = tk.StringVar(None, self.initial_value)
        self.pop = tk.Toplevel(self.widget)
        self.pop.bind('<Escape>', lambda e: self.pop.destroy())
        self.pop.title(self.title)
        self.pop.geometry("+{}+{}".format(self.widget.winfo_rootx(),
                                          self.widget.winfo_rooty()))
        self.font = kwargs['font']
        self.width = len(kwargs['pop_label'])
        self.pop.wm_attributes("-topmost", True)
        self.pop_label = ttk.Label(self.pop, font=self.font,
                                   text=f"{kwargs['pop_label']}:")
        self.pop_label.pack(anchor='w', padx=5, pady=5)

    def selection(self, data):
        if self.side is None:
            self.job_q.put([self.label, data])
        else:
            self.job_q.put([self.label, self.side, data])
        try:
            self.pop.destroy()
        except AttributeError:
            # popup already closed
            pass


class ComboPopup(Popup):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        combo = ttk.Combobox(self.pop,
                             name=self.title,
                             values=self.content,
                             textvariable=self.selected,
                             width=self.width,
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
                           width=self.width,
                           command=lambda:
                           self.selection(self.selected.get())). \
                pack(anchor='w', padx=5)


class ToolTip(object):
    """
    Implements tool tips on onscreen display
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
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+{}+{}".format(
            self.widget.winfo_rootx() + self.x,
            self.widget.winfo_rooty() + self.y))
        tk.Label(tw, text=self.text, background="#ffffe0",
                 relief='solid', borderwidth=1).pack()
        tw.update_idletasks()  # Needed for macOS
        # tw.lift()  # Needed for macOS

    def hide_tool_tip(self):
        tw = self.tooltipwindow
        if tw:
            tw.destroy()
        self.tooltipwindow = None
