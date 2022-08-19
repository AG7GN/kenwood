# Kenwood
Files related to Kenwood radios

VERSION 20220819

## 710.py and 710.sh

Two scripts that provide CAT control for Kenwood TM-D710G or TM-V71A radios on a Raspberry Pi. It requires a serial/USB cable between the radio and the Pi.  An RT Systems programming cable will work, as will a Kenwood PG-5G cable or equivalent. 

- `710.sh` is a shell script that you use in the Terminal.
- `710.py` is a Python application that allows you to control the radio through a GUI that emulates the TM-D710G's screen. It also works with the TM-V71A.

The `710.sh` script requires `710.py` to talk to the radio. It does not start the `710.py` GUI in this case. `710.py` uses the Python serial library to communicate with the radio. 

## Recent significant changes

1. Ability to set shift (simplex, negative or positive).
1. Changing the frequency, modulation, step, tone, tone frequency, reverse or shift in the GUI while in memory mode will now prompt the user to modify the memory or copy the memory contents to VFO and then make the modifications. If the user attempts to change the frequency to one that is not in the band currently set to that side of the radio, the user will be prompted to either modify the memory or abort the change.
1. User can select any Raspberry Pi GPIO pin for PTT, not just the 'left' and 'right' radios for the Nexus DR-X. 'left' and 'right' are still available and will map to GPIO 12 and GPIO23 respectively.
1. Clicking 'Up' or 'Down' when in VFO mode now more closely mimics turning the tuning knob on the radio in terms of what parameters are kept from frequency to frequency. For example, the shift setting will automatically change as frequencies traverse the ranges described in the TM-D710GA manual:

	- VHF
		
		Under 145.100 MHz:		No offset (Simplex operation)
	
		145.100 ~ 145.499 MHz: 	– 600 kHz offset
	
		145.500 ~ 145.999 MHz: 	No offset (Simplex operation)
	
		146.000 ~ 146.399 MHz: 	+ 600 kHz offset
	
		146.400 ~ 146.599 MHz:	No offset (Simplex operation)
	
		146.600 ~ 146.999 MHz:	– 600 kHz offset
	
		147.000 ~ 147.399 MHz:	+ 600 kHz offset
	
		147.400 ~ 147.599 MHz:	No offset (Simplex operation)
	
		147.600 ~ 147.999 MHz:	– 600 kHz offset
	 
		148.000 MHz and higher:	No offset (Simplex operation)

	- UHF
	
		Under 442.000 MHz:		No offset (Simplex operation)
		
		442.000 ~ 444.999 MHz:	+ 5 MHz offset
		
		445.000 ~ 446.999 MHz:	No offset (Simplex operation)
		
		447.000 ~ 449.999 MHz:	– 5 MHz offset
		
		450.000 MHz and higher:	No offset (Simplex operation)

1. `710.py` now has a multithreaded XML-RPC server. This allows Fldigi to communicate with `710.py` as if `710.py` were Flrig. Apps using Hamlib can also use `710.py` via hamlib's 'FLRig' setting. Details below.

1. `710.sh` can interact with `710.py` as it always has, by calling it and passing commands via `710.py -c COMMAND`. Now, it can also interact via XML-RPC. This means that `710.sh` can be used while `710.py` is running.

1. PTT works via XML-RPC calls. When Fldigi makes an RPC call to `710.py` to activate PTT, for example, `710.py` will use the Pi's GPIO pins in the Nexus DR-X to control PTT. Details below

## CAVEATS

- Kenwood does not provide a CAT command to change the frequency band on a given side of the radio. You can only change the frequency band on the radio itself. This omission causes the following behaviors:

	1. When in VFO mode, you cannot select a frequency outside the frequency band set for that side. 

	1. Changing the frequency, modulation, step, tone, tone frequency, reverse or shift in the GUI while in memory mode will prompt the user to modify the memory or copy the memory contents to VFO and then make the modifications. If the user attempts to change the frequency to one that is not in the band currently set to that side of the radio, the user will be prompted to either modify the memory or abort the change.
	
	1. If you use the shell script (`710.sh`) to change the frequency, the script will first change the mode to VFO (if it's not already in that mode) and attempt to set the desired frequency. If the desired frequency is not in the currently set frequency band for that side, the frequency will not be changed. 

	The workaround for the inability to use CAT to change the frequency band is to set your commonly used frequencies in memory locations and use the scripts to put the radio in MR mode and set a certain memory channel. One easy way to program the radio's memories is to use `chirp`, which is available via the the Nexus Updater. `chirp` uses the same serial/USB cable as the `710` scripts. 
	
	Here are some tips for using `chirp`:
	
	1. Close the `710` script while running `chirp`. Only one program can access the serial port at a time.
	1. For the TM-D710G: Select __TM-D710G__ and not TM-D710G_CloneMode. Select __TM-V71__ for that radio.
	1. On the TM-D710G, all changes you make in `chirp` are immediately sent to the radio. There is no "update" or "send to radio" action to take.

- Unlike the radio's display, the GUI display will not display the TX frequency while PTT is active.

## Installation
Pick either Easy or Manual Installation.

### Easy Installation (for Nexus DR-X users)
- Make sure your Pi is connected to the Internet.
- Click __Raspberry > Hamradio > Update Pi and Ham Apps__.
- Check __710__ and __hamlib__, click __OK__.

### Manual Installation
- Make sure your Pi is connected to the Internet.
- Open a Terminal and run these commands:

		cd ~
		rm -rf kenwood/
		git clone https://github.com/AG7GN/kenwood
		sudo cp kenwood/710.sh /usr/local/bin/
		sudo cp kenwood/*.py /usr/local/bin/
		sudo cp kenwood/*.png /usr/share/pixmaps/

## OPTIONAL: Add a `udev` rule for your USB-serial cable

This is optional but recommended and will ensure that your radio's cable always is identified as the same serial port name on your Pi.

1. With your USB-serial cable for your radio __unplugged__ from the Pi, run this command in the Terminal:

		lsusb
	
	For example:
	
		pi@nexuspi4b-ag7gn:~ $ lsusb
		Bus 002 Device 002: ID 0bda:0316 Realtek Semiconductor Corp. Card Reader
		Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
		Bus 001 Device 010: ID 067b:2303 Prolific Technology, Inc. PL2303 Serial Port / Mobile Action MA-8910P
		Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
		Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

1. Connect your USB-serial cable to a USB port on your Pi. Your radio does not have to be powered on.

1. Run `lsusb` again. 

	For example:

		pi@nexuspi4b-ag7gn:~ $ lsusb
		Bus 002 Device 002: ID 0bda:0316 Realtek Semiconductor Corp. Card Reader
		Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
		Bus 001 Device 010: ID 067b:2303 Prolific Technology, Inc. PL2303 Serial Port / Mobile Action MA-8910P
		Bus 001 Device 011: ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC
		Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
		Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

1. Note the differences between the outputs of the two runs. In this example, the second run of `lsusb` has one additional line:

		Bus 001 Device 011: ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC

	That's the cable you just plugged in. We'll create a `udev` rule so that this serial port has a consistent name, which we'll call `kenwoodTM-V71A`. You can use whatever name you like. Don't use any spaces in your name and keep it simple and memorable.
	
1. The rule will use the ID information to identify that particular cable. In this example, the ID is `0403:6001`. Your cable will likely have a different ID. The ID consists of 2 parts: The part before the `:` is the `idVendor` and the part after the `:` is the `idProduct`.

1. The rule is defined in a file in `/etc/udev/rules.d`. To make the rule file, enter these commands in the Terminal using the ATTR values for your cable and whatever name you've decided to use (Note that after the 1st 2 commands, you'll get a `>` prompt):

		cat >99-kenwood.rules <<EOF
		SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="kenwoodTM-V71A"
		EOF
		sudo mv 99-kenwood.rules /etc/udev/rules.d/
		sudo udevadm control --reload
		
	For example:
	
		pi@nexuspi4b-ag7gn:~ $ cat >99-kenwood.rules <<EOF
		> SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="kenwoodTM-V71A"
		> EOF
		
		pi@nexuspi4b-ag7gn:~ $ sudo mv 99-kenwood.rules /etc/udev/rules.d/

		pi@nexuspi4b-ag7gn:~ $ sudo udevadm control --reload

1. Unplug your USB-serial cable from your Pi and plug it back in.

1. Now you'll see your serial port in `/dev/`. Run `ls -al /dev/ken*` to see it. 

	For example:

		pi@nexuspi4b-ag7gn:~ $ ls -al /dev/ken*
		lrwxrwxrwx 1 root root 7 Jan 30 16:15 /dev/kenwoodTM-V71A -> ttyUSB1

1. From now on, your serial port will be called `/dev/kenwoodTM-V71A` even if you disconnect/reconnect the cable or reboot the Pi.

### Distinguishing between cables with the same make/model

__IMPORTANT:__ If you have 2 USB-Serial cables of the same make and model attached to your Pi, they'll both have the same idVendor and idProduct value. In that case you'll need to use additional or alternate criteria to tell them apart. These devices have a lot of attribute (ATTRS) values, so you might find that one of the ATTRS is a serial number of some sort. Here's how:

1. Make sure your cable is plugged in to your Pi
1. Identify the port you want to query (ex. `/dev/ttyUSB0`, `/dev/ttyUSB1`). In this example, we'll use the one we just set up: `/dev/KenwoodTM-V71A`:

		pi@nexuspi4b-ag7gn:~ $ udevadm info -q property -n /dev/kenwoodTM-V71A
		
		DEVPATH=/devices/platform/scb/fd500000.pcie/pci0000:00/0000:00:00.0/0000:01:00.0/usb1/1-1/1-1.1/1-1.1:1.0/ttyUSB1/tty/ttyUSB1
		DEVNAME=/dev/ttyUSB1
		MAJOR=188
		MINOR=1
		SUBSYSTEM=tty
		USEC_INITIALIZED=270367968798
		ID_BUS=usb
		ID_VENDOR_ID=0403
		ID_MODEL_ID=6001
		ID_PCI_CLASS_FROM_DATABASE=Serial bus controller
		ID_PCI_SUBCLASS_FROM_DATABASE=USB controller
		ID_PCI_INTERFACE_FROM_DATABASE=XHCI
		ID_VENDOR_FROM_DATABASE=VIA Technologies, Inc.
		ID_MODEL_FROM_DATABASE=VL805 USB 3.0 Host Controller
		ID_PATH=platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0
		ID_PATH_TAG=platform-fd500000_pcie-pci-0000_01_00_0-usb-0_1_1_1_0
		ID_VENDOR=FTDI
		ID_VENDOR_ENC=FTDI
		ID_MODEL=FT232R_USB_UART
		ID_MODEL_ENC=FT232R\x20USB\x20UART
		ID_REVISION=0600
		ID_SERIAL=FTDI_FT232R_USB_UART_AI05SMCB
		ID_SERIAL_SHORT=AI05SMCB
		ID_TYPE=generic
		ID_USB_INTERFACES=:ffffff:
		ID_USB_INTERFACE_NUM=00
		ID_USB_DRIVER=ftdi_sio
		DEVLINKS=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AI05SMCB-if00-port0 /dev/kenwoodTM-V71A /dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0-port0
		TAGS=:systemd:
		CURRENT_TAGS=:systemd:

1. Note that there are 2 serial number items in the property list:

		ID_SERIAL=FTDI_FT232R_USB_UART_AI05SMCB
		ID_SERIAL_SHORT=AI05SMCB

	__NOTE:__ Not all USB-serial cables have serial numbers or another way to distinguish one cable from another of the same make/model. In that case, you'll have to use a cable from a different vendor so you can tell them apart.

1. Now, find out the actual ATTRS name for the serial number. We'll use the `ID_SERIAL_SHORT` item, which is `AI05SMCB` in this example. Run `udevadm info -q property -n /dev/kenwoodTM-V71A --attribute-walk | grep AI05SMCB`:

		pi@nexuspi4b-ag7gn:~ $ udevadm info -q property -n /dev/kenwoodTM-V71A --attribute-walk | grep AI05SMCB
		
		ATTRS{serial}=="AI05SMCB"
			 
1. Now we can use that ATTR to distinguish between cables with the same make/model. Our current `/etc/udev/rules.d/99-kenwood.rules` looks like this:

		SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="kenwoodTM-V71A"

	Modify that file (open it in a text editor as `sudo`) and add our new serial attribute so it looks like this:
	
		SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="AI05SMCB", SYMLINK+="kenwoodTM-V71A"
	
1. Save the file, exit your editor and run:

		sudo udevadm control --reload
		
1. Unplug and re-plug in your cable.


## Operating `710.py`

If you did the optional `udev` rule setup in the previous step, then you already know the serial port for your radio (`/dev/kenwoodTM-V71A` in the example). If you didn't, you'll have to figure out the port now. 

- Open a terminal and run:

		710.py 
		
	- By default, `710.py` will attempt to use `/dev/ttyUSB0` at 57600 baud to communicate with the radio. 
	- You can specify a different serial port or speed on the command line. Run `710.py -h` for instructions.  Running it with `-h` will display ports that it has identified as serial ports.
	
- For example, to use the port we created in the optional `udev` step earlier `/dev/kenwoodTM-V71A` @ 19200 baud, run it like this:
	
		710.py -p /dev/kenwoodTM-V71A -b 19200

	The baud rate must match the radio's __PC Port Baudrate__ (menu __920__) in the 710 and the equivalent in the 71A. By default, `710.py` uses `57600` unless you specify otherwise. Again, make sure your radio is set to the same value.
	
	The GUI features tool tips, which describe the different elements on the screen as you move your mouse over them.
	
	If you want the GUI to use a smaller desktop footprint, add the `--small` argument to `710.py`.

- Running `710.py -h` my Pi for example shows:

		pi@nexuspi4b-ag7gn:/usr/local/bin $ 710.py -h
		usage: 710.py [-h] [-v]
				[-p {/dev/kenwoodTM-D710G,/dev/gps2,/dev/ttyUSB2,/dev/gps0,/dev/gps1,/dev/serial1,/dev/serial0,/dev/ttyUSB1,/dev/ttyUSB0,/dev/ttyS0,/dev/ttyAMA0,/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0,/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_IC-7100_02007519_A-if00-port0,/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_IC-7100_02007519_B-if00-port0}]
				[-b {300,1200,2400,4800,9600,19200,38400,57600}] [-s] [-l x:y] [-x [1024-65535]]
				[-r {none,left,right,17,18,27,22,23,24,25,4,5,6,13,19,26,12,16,20,21}] [-c COMMAND]

		CAT control for Kenwood TM-D710G/TM-V71A

		optional arguments:
		  -h, --help            show this help message and exit
		  -v, --version         show program's version number and exit
		  -p {/dev/kenwoodTM-D710G,/dev/gps2,/dev/ttyUSB2,/dev/gps0,/dev/gps1,/dev/serial1,/dev/serial0,/dev/ttyUSB1,/dev/ttyUSB0,/dev/ttyS0,/dev/ttyAMA0,/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0,/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_IC-7100_02007519_A-if00-port0,/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_IC-7100_02007519_B-if00-port0}, --port {/dev/kenwoodTM-D710G,/dev/gps2,/dev/ttyUSB2,/dev/gps0,/dev/gps1,/dev/serial1,/dev/serial0,/dev/ttyUSB1,/dev/ttyUSB0,/dev/ttyS0,/dev/ttyAMA0,/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0,/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_IC-7100_02007519_A-if00-port0,/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_IC-7100_02007519_B-if00-port0}
										Serial port connected to radio (default: /dev/ttyUSB0)
		  -b {300,1200,2400,4800,9600,19200,38400,57600}, --baudrate {300,1200,2400,4800,9600,19200,38400,57600}
										Serial port speed (must match radio) (default: 57600)
		  -s, --small           Smaller GUI window (default: False)
		  -l x:y, --location x:y
										x:y: Initial x and y position (in pixels) of upper left corner of GUI. (default: None)
		  -x [1024-65535], --xmlport [1024-65535]
										TCP port on which to listen for XML-RPC rig control calls from clients such as Fldigi or Hamlib (default:
										12345)
		  -r {none,left,right,17,18,27,22,23,24,25,4,5,6,13,19,26,12,16,20,21}, --rig {none,left,right,17,18,27,22,23,24,25,4,5,6,13,19,26,12,16,20,21}
										BCM GPIO pin number for PTT control. Nexus DR-X Users: Select left or right radio if you want to control GPIO
										PTT via an XML-RPC 'rig.set_ptt' call. This will map to GPIO pin 12 for the left radio and pin 23 for the
										right. 'none' means that 'rig.set_ptt' calls will be ignored. In any case, PTT activation via CAT command is
										never used. (default: none)
		  -c COMMAND, --command COMMAND
										CAT command to send to radio (no GUI) (default: None)


### Make a Hamradio menu selection for `710.py`

Installing these scripts as per the directions above does not automatically create a Hamradio menu item because it is not possible to know in advance your system's serial port that will be used to communicate with the radio. You can make your own Hamradio menu item as described here. Some sleuthing might be needed to identify your radio's serial port if you haven't already done so.

1.	If you haven't already determined the serial port name for your radio's cable, here's one way to do it:

	- Unplug your USB-serial cable from your Pi.
	- Open a Terminal on your Pi and run this command:

			dmesg -w -H 
		
		You'll see lots of output and then it'll pause and wait for some event to happen (like plugging in a USB device).
	- Plug your USB-serial cable into your Pi (the radio does not have to be on).
	- You should see some `dmesg` output appear in your Terminal. It'll look something like this:

			[Jan28 15:00] usb 1-1.4: new full-speed USB device number 4 using xhci_hcd
			[  +0.134526] usb 1-1.4: New USB device found, idVendor=067b, idProduct=2303, bcdDevice= 4.00
			[  +0.000009] usb 1-1.4: New USB device strings: Mfr=1, Product=2, SerialNumber=0
			[  +0.000006] usb 1-1.4: Product: USB-Serial Controller D
			[  +0.000006] usb 1-1.4: Manufacturer: Prolific Technology Inc. 
			[  +0.002693] pl2303 1-1.4:1.0: pl2303 converter detected
			[  +0.009797] usb 1-1.4: pl2303 converter now attached to ttyUSB1

	- In this example, that last line tells you that the USB-Serial cable you plugged in is "`...now attached to ttyUSB1`". So, the serial port in this example is `/dev/ttyUSB1`. Yours may be different. With that information, you can now make a `desktop` file. Note that this example desktop file will launch `710.py` in "small" mode so it doesn't occupy so much screen real estate.

1. Create your `desktop` file
	- Using your favorite text editor, create a file called `$HOME/.local/share/applications/kenwoodtm.desktop`. Here's one way to do that:
	
		- Click __Raspberry > Run__
		- In the __Run__ window, enter:
		
				mousepad $HOME/.local/share/applications/kenwoodtm.desktop
			
			That will open a text editor similar to Notepad on Windows.

	- Enter this text in the file:

			[Desktop Entry]
			Name=TM-D710G/TM-V71A Controller
			Comment=Kenwood TM-D710G/TM-V71A Controller
			Exec=sh -c "710.py -p /dev/kenwoodTM-V71A -r right --small >/dev/null 2>&1"
			Icon=hamradio.png
			StartupNotify=true
			Terminal=false
			Type=Application
			Categories=HamRadio
			Keywords=Ham Radio;Rig Control

	- Change the `Exec=` line to add/remove/modify arguments for your particular serial port/speed. Omit the `--small` if you want to run the GUI in regular size. 
	
		If you want GPIO PTT control via XML-RPC, also specify `-r left` or `-r right` for the left or right radios respectively. This is only needed if you want to control PTT via XML-RPC.

	- Change the `Name=` line to suit. This is the menu item name.

	- Save the file and close your editor. The new menu item should appear at the bottom of your __Raspberry > Hamradio__ menu.

### Using `710.py` with Fldigi

`710.py` runs an XML-RPC server on port `12345` by default. You can change the port using the `-x <port-number>` argument when you launch `710.py`. Port `12345` is the default XML-RPC port for Fldigi (Left Radio).

1. Launch `710.py` either from the command line or via your new menu item.

1. In Fldigi, select __Configure > Rig Control > flrig__. Assuming you're using the default port of `12345`, configure these settings:

	![Flrig Settings](img/fldigi_flrig.png)
	
	If you used the `-x <port-number>` option to change the port, you must use that same port in the configuration above.
	
	Most Nexus DR-X uses will want to leave the __Flrig PTT keys modem__ unchecked because Fldigi GPIO PTT is already configured (under __Rig Control > GPIO__).
	
1. Click the __Reconnect__ button to tell Fldigi to set up a new XML-RPC connection to `710.py`.

1.	Click __Save__, then __Close__.

1. You should now be able to change the frequency from Fldigi's frequency field, from `710.py` by clicking on the frequency or by adjusting the frequency on the radio itself.

	__NOTE:__ Setting the frequency in Fldigi will only change the frequency on the side of the radio set for Digital.

### Using `710.py` with Hamlib

Hamlib can send commands and receive state information from Flrig. `710.py` can be used as a substitute for Flrig.

Nexus DR-X users can use the __Hamlib Rig Control GUI__ to manage Hamlib.

- Start the `710.py` script. 
	- Be sure to use the default port of `12345` (in other words, don't specify a different port with the `-x` option). Hamlib will only work over port `12345`. 
	- If you want Hamlib to control PTT, then run `710.py` with `-r left` or `-r right` to control the left or right radio. This is needed for apps that cannot control GPIO PTT directly and so must rely on Hamlib for PTT. Fldigi and Direwolf can control GPIO PTT directly.
- Run __Raspberry > Hamradio > Hamlib Rig Control GUI__ 
- Enter `flrig` in the __Rig search string__ field, then click __Find__. 
- Check __Flrig__ in the list.
- Set the __Serial Port__ and __Speed__ fields to __Not Applicable__.
- Click __Save Changes & [Re]start rigctld__.
- You should now see that rigctld is running as shown in green:

	![hamlib flrig](img/hamlib_flrig.png)

- Applications that use Hamlib for rig control (and PTT if you launched `710.py` with `-r left|right`) should now work with the Kenwood radio.

__IMPORTANT:__ If you close `710.py` while `rigctld` is running, you'll have to restart `rigctld` again once `710.py` is running.

## Operating `710.sh`
- Open a terminal and run:
  
		710.sh -h
	and follow the instructions.  

- `710.sh` will attempt to communicate with the radio via `710.py` in one of 2 ways:

	1.	__If `710.py` IS ALREADY running:__ `710.sh` will use XML-RPC to send the command to `710.py`, which will in turn send the command to the radio. This is the slower of the 2 ways to communicate with the radio, but has the advantage that `710.py` can be running when you send your commands.

	2. __If `710.py` IS NOT running:__ `710.sh` will attempt to start `710.py` in non-GUI "one shot" mode. No GUI will open, but `710.py` will send the command passed to it by `710.sh`, return the results to `710.sh`, and then exit. This is the way that `710.sh` operated in previous versions and returns data faster than the first method.

		If you use the second method, the script will look for USB-serial cables (represented as files) in `/dev/serial/by-id` unless you specify the serial port with `-p`.  If any of the devices listed have filenames that contain any of these strings, then the script will automatically select and use that cable to communicate with the radio:

		- USB-Serial
		- RT_Systems
		- usb-FTDI

		If more than one cable matches, it'll use the last matching file name alphabetically.

		To view the list of files that represent the USB-serial cables, open a terminal and run this command:

			ls -al /dev/serial/by-id
	

### Notes

You can optionally supply the serial port used to connect to your radio using the `-p PORT` argument.  __This is used ONLY if `710.sh` cannot contact `710.py` via XML-RPC__. 

For example:

	710.sh -p /dev/ttyUSB0 set timeout 3

Alternatively, you can supply a string to grep (search) for in `/dev/serial/by-id` to determine the serial port used to connect to your radio using the `-s PORTSTRING` argument.  

For example:

	710.sh -s RT_Systems get info

If a port is supplied using `-p PORT`, it will take precedence over a string supplied by `-s PORTSTRING`."

If you connect more than one serial cable and the string description for those cables contain a match of any of the strings listed above you __MUST__ use either the `-p` or `-s` options to tell the cables apart apart. See the optional `udev` instructions above for a better way to identify your serial cable(s).

In the following example, 2 USB-serial cables are attached to the Pi:

	pi@hampi-ag7gn:~ $ ls -l /dev/serial/by-id
	total 0
	lrwxrwxrwx 1 root root 13 Jan 24 09:13 usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0 -> ../../ttyUSB0
	lrwxrwxrwx 1 root root 13 Jan 24 10:52 usb-RT_Systems_K5G_Radio_Ca͢le_RT1RVT5Y-if00-port0 -> ../../ttyUSB1

In this example, both cables will match the default search string.  So, you must specify either the `-p` or `-s` options:

Continuing with this example, to use the cable with `RT_Systems` in the name, run:

	710.sh -s RT_Systems get info
	
To use the cable with `USB-Serial` in the name:

	710.sh -s USB-serial get info
	
When you use the `-s` option, make sure you use a search string that's unique to the cable you want to use.

