# Kenwood
Files related to Kenwood radios
## 710.sh  

VERSION 20191209

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

By default, the script will look for USB-serial cables (represented as files) in `/dev/serial/by-id`.  If any of the devices listed have filenames that contain any of these strings, then the script should automatically select and use that cable to communicate with the radio:

		USB-Serial

		RT_Systems

		usb-FTDI

## Notes

You can optionally supply the serial port used to connect to your radio using the `-p PORT` argument.  For example:

	tnc.sh -p /dev/ttyUSB0 set timeout 3

Alternatively, you optionally supply a string to grep for in `/dev/serial/by-id` to determine the serial port used to connect to your radio using the `-s PORTSTRING` argument.  For example:

	tnc.sh -s RT_Systems get info

If a port is supplied using `-p PORT`, it will take precedence over a string supplied by `-s PORTSTRING`."

