import re
from common710 import stamp
from queue import Queue
from common710 import VENDOR_ID, PRODUCT_IDS, NEXUS_PTT_GPIO_DICT

__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2023, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL v3.0"
__version__ = "1.0.0"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"


class Ptt(object):
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
        def __init__(self, digirig: str, **kwargs):
            self.msg_queue = kwargs['msg_queue']
            self.digirig = digirig
            digirig_parts = self.digirig.split('@')
            try:
                digirig_device_port = digirig_parts[1]
            except (ValueError, IndexError):
                # No '@<device>' so digirig uses same serial
                # port as controller
                self.port = kwargs['default_port']
                self.digirig_ready = True
            else:
                # User supplied a digirig serial port device name,
                # and it is different from the controller port device.
                # Set up the digirig serial port
                import serial
                digirig_device = serial.Serial(port=None)
                digirig_device.rts = False
                digirig_device.port = digirig_device_port
                try:
                    digirig_device.open()
                except serial.serialutil.SerialException:
                    # Supplied digirig device port exists, but can't open it
                    self.digirig_ready = False
                else:
                    self.port = digirig_device
                    self.digirig_ready = True

        def on(self):
            self.port.rts = True

        def off(self):
            self.port.rts = False

        @property
        def value(self) -> int:
            return int(self.port.rts)

        @property
        def ready(self) -> bool:
            return self.digirig_ready

    class CM108Ptt(object):
        """
        Implements PTT via GPIO on CM108/CM119 sound interfaces such as
        the DRA series. The most common GPIO pin for PTT on these
        devices is 3, but the user can specify any GPIO pin between 1
        and 8. 3 is the default. User can also specify an index representing
        the CM108/CM119 device if more than one is present
        """
        def __init__(self, cm1xx: str, **kwargs):
            self.msg_queue = kwargs['msg_queue']
            try:
                import hid
            except ModuleNotFoundError:
                self.msg_queue.put(['ERROR', f"{stamp()}: Python3 hidapi "
                                   "module not found. Ignoring CAT PTT commands."])
                self.cm108_ready = False
                return

            # Check for GPIO pin parameter
            cm108 = cm1xx.split(':')
            try:
                # User specified a GPIO pin
                cm108_gpio = int(cm108[1])
            except (ValueError, IndexError):
                # No GPIO pin specified. Use 3, the most common
                # for PTT on CM1xx
                cm108_gpio = 3

            # Check for CMedia device selection
            cm108 = cm108[0].split('@')
            try:
                device_index = int(cm108[1])
            except (ValueError, IndexError):
                # User did not specify a particular CM108 device
                device_index = 0

            self.ptt_active = 0
            # CM108 info: https://github.com/nwdigitalradio/direwolf/blob/master/cm108.c)
            mask = 1 << (cm108_gpio - 1)
            self.PTT_on = bytearray([0, 0, mask, mask, 0])
            self.PTT_off = bytearray([0, 0, mask, 0, 0])
            self.path = None
            index = 0
            for device_dict in hid.enumerate(vendor_id=VENDOR_ID):
                if device_dict['product_id'] in PRODUCT_IDS:
                    if device_index == 0:
                        # No CM1xx device requested so use the first one found.
                        # (There is no way to identify individual CM1xx
                        # USB sound cards because there is no serial number.)
                        self.path = device_dict['path']
                        break
                    else:
                        # Specific CM1xx device requested
                        index += 1
                        self.path = device_dict['path']
                        if device_index == index:
                            break

            if self.path is None:
                self.msg_queue.put(['ERROR', f"{stamp()}: No C-Media device with "
                                   "GPIO found. Ignoring CAT PTT commands."])
                self.CM108_ready = False
            else:
                self.device = hid.device()
                # Verify that we can open the HID device before
                # claiming victory
                if self._open():
                    self._close()
                    self.CM108_ready = True
                else:
                    self.CM108_ready = False

        def _open(self) -> bool:
            try:
                self.device.open_path(self.path)
            except (OSError, IOError) as e:
                self.msg_queue.put(['ERROR', f"{stamp()}: Unable to open"
                                   f"CM1xx sound device at path {self.path}: {e}"])
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
                    self.msg_queue.put(['ERROR', f"{stamp()}: Unable to write "
                                       "to CM1xx GPIO"])
                self._close()

        def off(self):
            if self._open():
                previous_ptt_state = self.ptt_active
                wrote = self.device.write(self.PTT_off)
                if wrote == len(self.PTT_off):
                    self.ptt_active = 0
                else:
                    self.msg_queue.put(['ERROR', f"{stamp()}: Unable to write "
                                       "to CM1xx GPIO"])
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

    class GPIOPtt(object):
        """
        Implements PTT via GPIO on Raspberry Pi computers.
        """
        def __init__(self, gpio: str, **kwargs):
            self.msg_queue = kwargs['msg_queue']
            try:
                from gpiozero import OutputDevice
            except (ModuleNotFoundError, Exception):
                self.msg_queue.put(['ERROR', f"{stamp()}: Python3 gpiozero "
                                   "module not found. Ignoring CAT PTT commands."])
                self.gpio_ready = False
            else:
                from gpiozero import BadPinFactory
                if gpio in NEXUS_PTT_GPIO_DICT.keys():
                    gpio = NEXUS_PTT_GPIO_DICT[gpio]
                try:
                    self.gpio_ptt = OutputDevice(int(gpio),
                                                 active_high=True,
                                                 initial_value=False)
                except BadPinFactory:
                    self.gpio_ready = False
                else:
                    self.gpio_ready = True

        def on(self):
            self.gpio_ptt.on()

        def off(self):
            self.gpio_ptt.off()

        @property
        def value(self) -> int:
            return self.gpio_ptt.value

        @property
        def ready(self) -> bool:
            return self.gpio_ready

    def __init__(self, ptt_method: str, **kwargs):
        """
        Initializes a BufferedRWPair object that wraps a serial object.
        Wrapping the serial port object allows customization of the
        end-of-line character used by the radio
        :param ptt_method: str
        """
        self.ptt_method = ptt_method
        self.msg_queue = kwargs['msg_queue']
        if self.ptt_method == 'cat':
            self.ptt = self.CatPtt(kwargs['job_queue'])
            self.msg_queue.put(['INFO', f"{stamp()}: XML-RPC PTT will be "
                               f"sent to radio serial port as CAT command"])
        elif self.ptt_method.startswith('digirig'):
            self.ptt = self.DigirigPtt(self.ptt_method,
                                       default_port=kwargs['default_port'],
                                       msg_queue=self.msg_queue)
            if not self.ptt.ready:
                self.msg_queue.put(['WARNING', f"{stamp()}: Unable to access "
                                   f"{self.ptt_method}. Ignoring XML-RPC PTT."])
                self.ptt = None
            else:
                self.msg_queue.put(['INFO', f"{stamp()}: XML-RPC PTT "
                                   f"will handled via {self.ptt_method} audio port"])
        elif self.ptt_method.startswith('cm108'):
            self.ptt = self.CM108Ptt(self.ptt_method,
                                     msg_queue=self.msg_queue)
            if not self.ptt.ready:
                self.msg_queue.put(['WARNING', f"{stamp()}: Unable to access "
                                   f"{self.ptt_method} GPIO. Ignoring XML-RPC PTT."])
                self.ptt = None
            else:
                self.msg_queue.put(['INFO', f"{stamp()}: XML-RPC PTT will "
                                            f"be handled via {self.ptt_method} GPIO"])
        elif re.match("^(left|right|[1-9])", str(self.ptt_method)):
            self.ptt = self.GPIOPtt(self.ptt_method,
                                    msg_queue=self.msg_queue)
            if not self.ptt.ready:
                self.msg_queue.put(['WARNING', f"{stamp()}: Unable to initialize GPIO "
                                   f"{self.ptt_method}. Ignoring XML-RPC PTT."])
                self.ptt = None
            else:
                self.msg_queue.put(['INFO', f"{stamp()}: XML-RPC PTT "
                                   f"will be handled via GPIO '{self.ptt_method}'"])
        else:
            self.ptt = None
            self.msg_queue.put(['INFO', f"{stamp()}: XML-RPC PTT will "
                               f"be ignored"])

    @property
    def state(self) -> int:
        """
        Returns state of PTT.
        :return: 1 if PTT is active, 0 if not active or if self.ptt is None
        """
        if self.ptt is None:
            return 0
        else:
            return self.ptt.value

    @state.setter
    def state(self, turn_on: bool):
        """
        Sets the state of PTT.
        :param turn_on: Desired state of PTT
        """
        if self.ptt is not None:
            if turn_on:
                self.ptt.on()
            else:
                self.ptt.off()
