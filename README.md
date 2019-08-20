# Kenwood
Files related to Kenwood radios
## 710.sh  
This script provides CAT control of a Kenwood TM-D710G or TM-V71A radio on a Raspberry Pi.  
It requires a serial/USB cable between the radio and the Pi.  An RT Systems programming cable will work, as will a Kenwood PG-5G or equivalent.  

### Installation  
- Make sure your Pi is connected to the Internet.
- Connect your radio's serial cable to your Pi.
- Open a Terminal and run these commands:

		ls -l /dev/serial/by-id
	For example:
	
		pi@gokitpi:/dev/serial/by-id $ ls -l  
		total 0
		lrwxrwxrwx 1 root root 13 May 21 20:31 usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0 -> ../../ttyUSB0  
- Locate a part of that string that uniquely identifies the serial port.  In this example, __USB-Serial__ would work.
- Run these commands in the Terminal:

		cd ~
		rm -rf kenwood/
		git clone https://github.com/AG7GN/kenwood
		cd kenwood
		chmod +x 710.sh  
	
- Open `710.sh` in a text editor and locate this line:  

		PORT="$(ls -l $DIR 2>/dev/null | grep USB-Serial)"
    
  If necessary, change the __USB-Serial__ string to look for to match your cable's ID.  
- Save the file and exit the editor.
  
- Copy the script to `/usr/local/bin`:
  
		sudo cp 710.sh /usr/local/bin  

### Run
- Open a terminal and run:
  
		710.sh  
	and follow the instructions.  
