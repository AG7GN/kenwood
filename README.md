# Kenwood
Files related to Kenwood radios
## 710.sh  
This script provides CAT control of a Kenwood TM-D710G or TM-V71A radio on a Raspberry Pi.  
It requires a serial/USB cable between the radio and the Pi.  An RT Systems programming cable will work, as will a Kenwood PG-5G or equivalent.  

### Installation  
- Open https://github.com/AG7GN/kenwood in your Pi's browser.
- Click __710.sh__, then click the __Download__ button.  
- Open Terminal and go to the __Downloads__ folder:  
        <code>cd Downloads</code>
- Run the following commands:  
        <code>chmod +x 710.sh</code>  
- Edit this line  
    <code>PORT="$(ls -l $DIR 2>/dev/null | grep USB-Serial)"</code>  
  in __710.sh__ if necessary to change the __USB-Serial__ substring to look for in /dev/serial/by-id to match your cable's ID.  
  
  For example:  
  <code>pi@gokitpi:/dev/serial/by-id $ ls -l  
total 0
lrwxrwxrwx 1 root root 13 May 21 20:31 usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0 -> ../../ttyUSB0</code>  

In this example, grep for 'USB-Serial' would find the right device.  

- Move the script to /usr/local/bin:  
    <code>sudo mv 710.sh /usr/local/bin</code>  

### Run
- Open a terminal and run:  
    <code>710.sh</code>  
    and follow the instructions.  
