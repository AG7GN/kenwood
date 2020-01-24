# Kenwood
Files related to Kenwood radios
## 710.sh  

VERSION 20200124

This script provides CAT control of a Kenwood TM-D710G or TM-V71A radio on a Raspberry Pi. It requires a serial/USB cable between the radio and the Pi.  An RT Systems programming cable will work, as will a Kenwood PG-5G or equivalent.  

## Install
Pick either Easy or Manual Installation.
### Easy Installation (for Hampi users)
- Make sure your Pi is connected to the Internet.
- Click __Raspberry > Hamradio > Update Pi and Ham Apps__.
- Check __710.sh__, click __OK__.

### Manual Installation
- Make sure your Pi is connected to the Internet.
- Open a Terminal and run these commands:

		cd ~
		rm -rf kenwood/
		git clone https://github.com/AG7GN/kenwood
		sudo cp kenwood/710.sh /usr/local/bin/

## Run
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
	

## Notes

You can optionally supply the serial port used to connect to your radio using the `-p PORT` argument.  For example:

	tnc.sh -p /dev/ttyUSB0 set timeout 3

Alternatively, you optionally supply a string to grep (search) for in `/dev/serial/by-id` to determine the serial port used to connect to your radio using the `-s PORTSTRING` argument.  For example:

	tnc.sh -s RT_Systems get info

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