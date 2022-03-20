import re
import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk
from tkinter import scrolledtext
from common710 import stamp
from common710 import FREQUENCY_LIMITS
from common710 import MEMORY_LIMITS
from common710 import TONE_TYPE_DICT
from common710 import TONE_FREQUENCY_DICT
from common710 import DCS_FREQUENCY_DICT
from common710 import MODE_DICT
from common710 import POWER_DICT
from common710 import MODULATION_DICT
from common710 import STEP_DICT
from common710 import DATA_SPEED_DICT
from common710 import TIMEOUT_DICT
from common710 import UpdateDisplayException

__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2022, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "2.0.3"
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
                        'console_w': 75, 'console_h': 5,
                        'x_offset': 5, 'y_offset': 35},
             'small': {'w': 545, 'h': 285, 'frame_w': 200,
                       'default_font_size': 10,
                       'frequency_font_size': 20,
                       'button_font_size': 8,
                       'message_font_size': 8,
                       'console_w': 72, 'console_h': 5,
                       'x_offset': 5, 'y_offset': 25},
             }
    _scr = {'row': 0, 'col': 0}  # screen starts at row 0, column 0

    def __init__(self, **kwargs):
        default_kwargs = {'title': 'Kenwood TM-D710G/TM-V71A Controller'}
        kwargs = {**default_kwargs, **kwargs}
        self.master = kwargs['root']
        self.title = kwargs['title']
        self.version = kwargs['version']
        self.cmd_q = kwargs['cmd_queue']
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
        self.labels_dict = {'A': {'ptt': (Display._scr['row'],
                                          Display._scr['col'], 1, 1,
                                          'w', self._default_font,
                                          "Push-to-talk"),
                                  'ctrl': (Display._scr['row'],
                                           Display._scr['col'] + 1, 1, 1,
                                           'w', self._default_font,
                                           "Control"),
                                  'tone': (Display._scr['row'],
                                           Display._scr['col'] + 2, 1, 1,
                                           'e', self._default_font,
                                           "Tone Type: Tone, DCS, or CTCSS.\nClick to change"),
                                  'tone_frequency': (Display._scr['row'],
                                                     Display._scr['col'] + 3, 1, 1,
                                                     'w', self._default_font,
                                                     "Tone, DCS, or CTCSS frequency.\nClick to change"),
                                  'shift': (Display._scr['row'],
                                            Display._scr['col'] + 4, 1, 1,
                                            'w', self._default_font,
                                            "TX shift direction.\n'S' is simplex"),
                                  'reverse': (Display._scr['row'],
                                              Display._scr['col'] + 5, 1,
                                              1, 'e', self._default_font,
                                              "'R': TX and RX frequencies reversed"),
                                  'modulation': (Display._scr['row'],
                                                 Display._scr['col'] + 6,
                                                 1, 1, 'e', self._default_font,
                                                 "Modulation: FM, NFM or AM.\nClick to change"),
                                  'power': (Display._scr['row'] + 1,
                                            Display._scr['col'], 1, 1,
                                            'w', self._default_font,
                                            "Power: High, Medium, Low.\nClick to change"),
                                  'data': (Display._scr['row'] + 1,
                                           Display._scr['col'] + 6, 1,
                                           1, 'e', self._default_font,
                                           "'D' means data on this side.\nClick to change"),
                                  'ch_name': (Display._scr['row'] + 1,
                                              Display._scr['col'] + 1,
                                              2, 1, 'e', self._default_font,
                                              "Memory Channel Name"),
                                  'ch_number': (Display._scr['row'] + 1,
                                                Display._scr['col'] + 4, 1, 1,
                                                'w', self._default_font,
                                                "Memory Channel Number.\nClick to go to different memory"),
                                  'mode': (Display._scr['row'] + 4,
                                           Display._scr['col'],
                                           1, 1, 'sw', self._default_font,
                                           "Mode: VFO, MR, CALL or WX.\nClick to change"),
                                  'frequency': (Display._scr['row'] + 2,
                                                Display._scr['col'] + 1,
                                                5, 3, 'nsw', self._frequency_font,
                                                "Frequency in MHz.\nClick to change"),
                                  'step': (Display._scr['row'] + 4,
                                           Display._scr['col'] + 6,
                                           1, 1, 'se', self._default_font,
                                           "Step size in KHz.\nClick to change"),
                                  },
                            'B': {'ptt': (Display._scr['row'],
                                          Display._scr['col'] + 8, 1,
                                          1, 'w', self._default_font, "Push-to-talk"),
                                  'ctrl': (Display._scr['row'],
                                           Display._scr['col'] + 9, 1,
                                           1, 'w', self._default_font, "Control"),
                                  'tone': (Display._scr['row'],
                                           Display._scr['col'] + 10, 1,
                                           1, 'e', self._default_font,
                                           "Tone Type: Tone, DCS, or CTCSS.\nClick to change"),
                                  'tone_frequency': (Display._scr['row'],
                                                     Display._scr['col'] + 11, 1,
                                                     1, 'w', self._default_font,
                                                     "Tone, DCS, or CTCSS frequency.\nClick to change"),
                                  'shift': (Display._scr['row'],
                                            Display._scr['col'] + 12, 1,
                                            1, 'w', self._default_font,
                                            "TX shift direction.\n'S' is simplex"),
                                  'reverse': (Display._scr['row'],
                                              Display._scr['col'] + 13, 1,
                                              1, 'e', self._default_font,
                                              "'R': TX and RX frequencies reversed"),
                                  'modulation': (Display._scr['row'],
                                                 Display._scr['col'] + 14,
                                                 1, 1, 'e', self._default_font,
                                                 "Modulation: FM, NFM or AM.\nClick to change"),
                                  'power': (Display._scr['row'] + 1,
                                            Display._scr['col'] + 8, 1,
                                            1, 'w', self._default_font,
                                            "Power: High, Medium, Low.\nClick to change"),
                                  'data': (Display._scr['row'] + 1,
                                           Display._scr['col'] + 14, 1,
                                           1, 'e', self._default_font,
                                           "'D' means data on this side.\nClick to change"),
                                  'ch_name': (Display._scr['row'] + 1,
                                              Display._scr['col'] + 9,
                                              2, 1, 'e', self._default_font,
                                              "Memory Channel Name"),
                                  'ch_number': (Display._scr['row'] + 1,
                                                Display._scr['col'] + 12, 1, 1,
                                                'w', self._default_font,
                                                "Memory Channel Number.\nClick to go to different memory"),
                                  'mode': (Display._scr['row'] + 4,
                                           Display._scr['col'] + 8, 1,
                                           1, 'sw', self._default_font,
                                           "Mode: VFO, MR, CALL, or WX.\nClick to change"),
                                  'frequency': (Display._scr['row'] + 2,
                                                Display._scr['col'] + 9, 5, 3,
                                                'nsw', self._frequency_font,
                                                "Frequency in MHz.\nClick to change"),
                                  'step': (Display._scr['row'] + 4,
                                           Display._scr['col'] + 14,
                                           1, 1, 'se', self._default_font,
                                           "Step size in KHz.\nClick to change"),
                                  }
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
        self.master.geometry(f"{w}x{h}+{x}+{y}")
        self.master.title(f"{self.title} {self.version}")
        self.master['padx'] = 5
        self.master['pady'] = 5
        self.master.resizable(0, 0)
        # Make the master frame
        content_frame = tk.Frame(self.master)
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
                                     bg=Display._screen_bg_color,
                                     width=Display.scale[size]['frame_w'])
        self.screen_frame.grid(column=0, row=0, rowspan=6,
                               columnspan=14, sticky='nsew')

        self.msg_frame = tk.Frame(master=content_frame,
                                  borderwidth=5,
                                  width=Display.scale[size]['frame_w'])
        self.msg_frame.grid(column=0, row=8, columnspan=14, sticky='nsew')
        self.msg = MessageConsole(frame=self.msg_frame,
                                  scale=Display.scale[size],
                                  queue=kwargs['msg_queue'])

        # Make a vertical line separating the A and B sides of screen
        self.side_separator_frame = tk.Frame(master=self.screen_frame,
                                             padx=5, pady=3,
                                             bg=Display._screen_bg_color)
        self.side_separator_frame.grid(column=7, row=0, rowspan=6,
                                       sticky='ns')
        separator = tk.Canvas(master=self.side_separator_frame,
                              width=2, height=2, borderwidth=0,
                              highlightthickness=0, bg='grey')
        separator.pack(fill=tk.BOTH, expand=True)

        for side in bottom_btns_frames.keys():
            self.bottom_btn_frame[side] = tk.Frame(master=self.screen_frame,
                                                   borderwidth=0,
                                                   bg=Display._screen_bg_color)
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
                    bg=Display._screen_bg_color, font=value[5])
                if key in ('frequency', 'tone', 'tone_frequency',
                           'ch_name', 'mode', 'ch_number',
                           'power', 'data', 'modulation', 'step'):
                    self.screen_label[side][key]. \
                        bind("<Button-1>",
                             lambda _, s=side,
                             k=key: self.widget_clicked(side=s,
                                                        key=k))
                ToolTip(widget=self.screen_label[side][key],
                        text=value[6],
                        x_offset=Display.scale[size]['x_offset'],
                        y_offset=Display.scale[size]['y_offset'] + 10)
                self.screen_label[side][key]. \
                    pack(fill=tk.BOTH, expand=True)

            # PTT, CTRL, REV, DOWN, UP buttons
            bottom_btn_start_col = bottom_btns_frames[side]['col']
            for b, val in bottom_btns.items():
                self.bottom_btn[side][b] = \
                    tk.Button(master=self.bottom_btn_frame[side],
                              text=b.upper(),
                              font=self._button_font,
                              command=lambda _b=b, _s=side:
                              self.cmd_q.put([_b, _s]))
                self.bottom_btn[side][b]. \
                    grid(row=bottom_btns_frames[side]['row'],
                         column=bottom_btn_start_col)
                bottom_btn_start_col += 1
                ToolTip(widget=self.bottom_btn[side][b],
                        text=bottom_btns[b],
                        x_offset=Display.scale[size]['x_offset'],
                        y_offset=Display.scale[size]['y_offset'])

            bg_button = tk.Button(master=content_frame,
                                  text="Backlight Color",
                                  font=self._button_font,
                                  command=lambda:
                                  self.cmd_q.put(['backlight', ]))
            bg_button.grid(row=6, column=0, sticky='nsew')
            ToolTip(widget=bg_button,
                    text="Click to toggle screen background color",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.timeout_button = \
                tk.Button(master=content_frame,
                          text="TX TO",
                          font=self._button_font,
                          command=lambda:
                          self.widget_clicked(key='timeout'))
            self.timeout_button.grid(row=6, column=1, sticky='nsew')
            ToolTip(widget=self.timeout_button,
                    text="Click to set TX timeout (minutes)",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            micdown_button = tk.Button(master=content_frame,
                                       text="Mic Down",
                                       font=self._button_font,
                                       command=lambda:
                                       self.cmd_q.put(['micdown', ]))
            micdown_button.grid(row=6, column=2, sticky='nsew')
            ToolTip(widget=micdown_button,
                    text="Click to emulate 'Down' button on mic",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])
            micup_button = tk.Button(master=content_frame,
                                     text="Mic Up",
                                     font=self._button_font,
                                     command=lambda:
                                     self.cmd_q.put(['micup', ]))
            micup_button.grid(row=6, column=3, sticky='nsew')
            ToolTip(widget=micup_button,
                    text="Click to emulate 'Up' button on mic",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.lock_button = tk.Button(master=content_frame,
                                         text="Lock is",
                                         font=self._button_font,
                                         command=lambda:
                                         self.cmd_q.put(['lock', ]))
            self.lock_button.grid(row=7, column=0, sticky='nsew')
            ToolTip(widget=self.lock_button,
                    text="Click to toggle radio controls lock",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.vhf_aip_button = tk.Button(master=content_frame,
                                            text="VHF AIP is",
                                            font=self._button_font,
                                            command=lambda:
                                            self.cmd_q.put(['vhf_aip', ]))
            self.vhf_aip_button.grid(row=7, column=1, sticky='nsew')
            ToolTip(widget=self.vhf_aip_button,
                    text="Click to toggle VHF Advanced Intercept Point",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.uhf_aip_button = tk.Button(master=content_frame,
                                            text="VHF AIP is",
                                            font=self._button_font,
                                            command=lambda:
                                            self.cmd_q.put(['uhf_aip', ]))
            self.uhf_aip_button.grid(row=7, column=2, sticky='nsew')
            ToolTip(widget=self.uhf_aip_button,
                    text="Click to toggle UHF Advanced Intercept Point",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            self.speed_button = tk.Button(master=content_frame,
                                          text="Tap",
                                          font=self._button_font,
                                          command=lambda:
                                          self.widget_clicked(key='speed'))
            self.speed_button.grid(row=7, column=3, sticky='nsew')
            ToolTip(widget=self.speed_button,
                    text="Click to toggle data audio tap (1200 or 9600)",
                    x_offset=Display.scale[size]['x_offset'],
                    y_offset=Display.scale[size]['y_offset'])

            quit_button = tk.Button(master=content_frame,
                                    text='Quit',
                                    font=self._button_font,
                                    command=lambda:
                                    self.cmd_q.put(['quit', ]))
            quit_button.grid(row=13, column=0, columnspan=14,
                             sticky='nsew')

    def widget_clicked(self, **kwargs):

        _label = None
        s = kwargs.get('side', None)
        k = kwargs.get('key', None)
        if s is None:
            self.msg.queue.put(['INFO', f"{stamp()}: Widget '{k}' clicked."])
        else:
            _label = str(self.screen_label[s][k].cget('text'))
            self.msg.queue.put(['INFO', f"{stamp()}: Widget '{k}' on side "
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
            for key in self.labels_dict[side]:
                self.screen_label[side][key]. \
                    config(background=Display._screen_bg_color)
            self.bottom_btn_frame[side].config(background=Display._screen_bg_color)

    def update_display(self, data: dict):
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
        self.msg_text.grid(row=0, column=0, sticky='nsew')
        self.msg_text.tag_configure('INFO', foreground='blue')
        self.msg_text.tag_configure('WARNING', foreground='black',
                                    background='orange')
        self.msg_text.tag_configure('ERROR', foreground='white',
                                    background='red')
        self.queue = kwargs['queue']
        self.frame.after(100, self.msg_q_reader)

    def display_message(self, msg):
        _level, _m = msg
        self.msg_text.configure(state='normal')
        self.msg_text.insert(tk.END, _m + '\n', _level)
        self.msg_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.msg_text.yview(tk.END)

    def msg_q_reader(self):
        while not self.queue.empty():
            message = self.queue.get(block=False)
            self.display_message(message)
            self.queue.task_done()
        self.frame.after(100, self.msg_q_reader)


class Popup(object):
    """
    Class that creates a popup window for entering data
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
        # self.selected = tk.StringVar(None, kwargs['initial_value'])
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
                             text=self.title,
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
        tw.wm_overrideredirect(True)
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
