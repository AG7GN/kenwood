# Kenwood
Files related to Kenwood radios
## 710.sh  

VERSION 20210422

Two scripts that provide CAT control for Kenwood TM-D710G or TM-V71A radios on a Raspberry Pi. It requires a serial/USB cable between the radio and the Pi.  An RT Systems programming cable will work, as will a Kenwood PG-5G or equivalent. 

- `710.sh` is a shell script that you use in the Terminal.
- `710.py` is a Python application that allows you to control the radio through a GUI that emulates the TM-D710G's screen, although it works with the TM-V71A as well.

The `710.sh` script calls `710.py` to talk to the radio. It does not start the `710.py` GUI in this case. `710.py` uses the Python serial library to communicate with the radio. 

## Install
Pick either Easy or Manual Installation.

### Easy Installation (for Nexus users)
- Make sure your Pi is connected to the Internet.
- Click __Raspberry > Hamradio > Update Pi and Ham Apps__.
- Check __710__, click __OK__.

### Manual Installation
- Make sure your Pi is connected to the Internet.
- Open a Terminal and run these commands:

		cd ~
		rm -rf kenwood/
		git clone https://github.com/AG7GN/kenwood
		sudo cp kenwood/710.sh /usr/local/bin/
		sudo cp kenwood/*.py /usr/local/bin/
		sudo cp kenwood/*.png /usr/share/pixmaps/

## Running `710.py`

- Open a terminal and run:

		710.py 
		
	By default, `710.py` will attempt to use `/dev/ttyUSB0` at 57600 baud to communicate with the radio. You can specify a different serial port or speed on the command line. Run `710.py -h` for instructions.  Running it with `-h` will display the available serial ports.
	
	For example, to use port `/dev/ttyUSB1` @ 19200 baud, run it like this:
	
		710.py -p /dev/tty/USB1 -b 19200

	The baud rate must match the radio's __PC Port Baudrate__ (menu __920__) in the 710 and the equivalent in the 71A.
	
	The GUI features tool tips, which describe the different elements on the screen as you move your mouse over them.
	
	If you want the GUI to use a smaller desktop footprint, add the `--small` argument to `710.py`.

## Make a __Hamradio__ menu selection for `710.py`

In the example below, the serial port connected to the Kenwood is `/dev/ttyUSB1`. Yours may be different. Note also that this example desktop file will launch `710.py` in "small" mode so it doesn't occupy so much screen real estate.

- Using your favorite text editor, create a file called `$HOME/.local/share/applications/kenwoodtm.desktop`

- Enter this text in the file:

		[Desktop Entry]
		Name=TM-D710G Controller
		Comment=Kenwood TM-D710G/TM-V71A Controller
		Exec=sh -c "710.py -p /dev/ttyUSB1 --small >/dev/null 2>&1"
		Icon=hamradio.png
		StartupNotify=true
		Terminal=false
		Type=Application
		Categories=HamRadio
		Keywords=Ham Radio;Rig Control

- Change the `Exec=` line to add/remove/modify arguments for your particular serial port/speed. Omit the `--small` if you want to run the GUI in regular size.

- Change the `Name=` line to suit. This is the menu item name.

- Save the file and close your editor. The new menu item should appear at the bottom of your Hamradio menu.


## Running `710.sh`
- Open a terminal and run:
  
		710.sh  
	and follow the instructions.  

By default, the script will look for USB-serial cables (represented as files) in `/dev/serial/by-id`.  If any of the devices listed have filenames that contain any of these strings, then the script will automatically select and use that cable to communicate with the radio:

		USB-Serial

		RT_Systems

		usb-FTDI

If more than one cable matches, it'll use the last matching file name alphabetically.

To view the list of files that represent the USB-serial cables, open a terminal and run this command:

	ls -al /dev/serial/by-id
	

### Notes

You can optionally supply the serial port used to connect to your radio using the `-p PORT` argument.  For example:

	710.sh -p /dev/ttyUSB0 set timeout 3

Alternatively, you optionally supply a string to grep (search) for in `/dev/serial/by-id` to determine the serial port used to connect to your radio using the `-s PORTSTRING` argument.  For example:

	710.sh -s RT_Systems get info

If a port is supplied using `-p PORT`, it will take precedence over a string supplied by `-s PORTSTRING`."

If you connect more than one serial cable and the string description for those cables contain a match of any of the strings listed above you __MUST__ use either the `-p` or `-s` options to tell the cables apart apart.

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