#!/bin/bash

# Script to control Kenwood TM-V71A and TM-D710G radios via CAT commands.
# Author: Steve Magnuson, AG7GN

VERSION=4.7.5
DEV=234
SPEED=57600
DIR="/dev/serial/by-id"
# The following PORTSTRING will be used if the '-s PORTSTRING' argument is not supplied
DEFAULT_PORTSTRING="USB-Serial|RT_Systems|usb-FTDI"
PORTSTRING="$DEFAULT_PORTSTRING"

Usage () {
	echo
   [[ "$1" == "" ]] || echo "ERROR: $1"
   echo
	echo "Version $VERSION"
	echo
   echo "CAT control script for Kenwood TM-D710G/TM-V71A."
	echo "Set radio's PC port speed to $SPEED or change SPEED setting in"
	echo "this script to match radio's setting."
   echo
   echo "Usage:"
   echo
   echo "${0##*/} get apo						Prints Auto Power Off setting"
   echo "${0##*/} get data                Prints the side configured for external data"
   echo "${0##*/} get info                Prints some radio settings"
   echo "${0##*/} get memory <channel>    Prints memory channel configuration"
	echo "${0##*/} get menu                Prints raw menu contents output (diagnostic command)"
   echo "${0##*/} get mode                Prints mode (modulation) settings"
   echo "${0##*/} get power               Prints power settings"
   echo "${0##*/} get pttctrl             Prints PTT and CTRL settings"
	echo "${0##*/} get speed               Prints external data speed (1200|9600)"
	echo "${0##*/} get sqc                 Prints SQC source"
   echo "${0##*/} get a|b squelch         Prints squelch settings for side A or B"
   echo "${0##*/} get timeout             Prints TX timeout setting"
	echo
	echo "${0##*/} set apo off|30|60|90|120|180     Sets Automatic Power Off (minutes)"
   echo "${0##*/} set a|b ctrl            Sets CTRL to side A or B"
   echo "${0##*/} set a|b data            Sets external data to side A or B"
   echo "${0##*/} set a|b freq <MHz>      Sets side A or B to VFO and sets frequency to <MHz>"
   echo "${0##*/} set a|b memory <memory>"
   echo "                               Sets side A or B to memory mode and assigns"
   echo "                               <memory> location to it"
   echo "${0##*/} set a|b mode vfo|memory|call|wx"
   echo "                               Sets side A or B mode"
   echo "${0##*/} set a|b power l|m|h     Sets side A or B to Low, Medium or High power"
   echo "${0##*/} set a|b ptt             Sets PTT to side A or B"
   echo "${0##*/} set a|b pttctrl         Sets PTT and CTRL to side A or B"
   echo "${0##*/} set speed 1200|9600     Sets external data speed to 1200 or 9600"
   echo "${0##*/} set a|b squelch <0-31>  Sets squelch level for side A or B"
	echo "${0##*/} set timeout 3|5|10      Sets transmit timeout (minutes)"
   echo
	echo "${0##*/} help                    Prints this help screen"
	echo
	echo "You can optionally supply the serial port used to connect to your radio.  For example:"
	echo
	echo "${0##*/} -p /dev/ttyUSB0 set timeout 3"
	echo
	echo "Alternatively, you can optionally supply a string to grep for in $DIR to determine the"
	echo "serial port used to connect to your radio.  For example:"
	echo
	echo "${0##*/} -s RT_Systems get info"
	echo
	echo "If you do not supply a serial port with the -p option, or specify a string via '-s PORTSTRING'"
	echo "to search for in order to determine the port, the script will search for a serial port in $DIR"
	echo "using this grep string: $DEFAULT_PORTSTRING."
	echo
	echo "If a port is supplied using '-p PORT', it will take precedence over the search string."
	echo
   [[ "$1" == "" ]] && exit 0 || exit 1
}

command -v bc >/dev/null || Usage "Cannot find bc application.  To install it, run: sudo apt update && sudo apt install -y bc"
command -v rigctl >/dev/null || Usage "Cannot find rigctl application.  Install hamlib."

# Check if user supplied serial port
declare -a ARGS
PORT=""
while [ $# -gt 0 ]
do
   unset OPTIND
   unset OPTARG
   #while getopts as:c:  OPTIONS
   while getopts p:s:  OPTIONS
   do
      case $OPTIONS in
         p)
            PORT="$OPTARG"
         	;;
         s)
         	PORTSTRING="$OPTARG"
         	;;
      esac
   done
   shift $((OPTIND-1))
   ARGS+=($1)
   shift
done

P1="${ARGS[0]^^}"
P2="${ARGS[1]^^}"
P3="${ARGS[2]^^}"
P4="${ARGS[3]^^}"

[[ $P1 == "HELP" ]] && Usage

# If '-p PORT' is supplied, ignore PORTSTRING.
if [[ $PORT == "" ]]
then # User did not supply serial port.  Search for it using $PORTSTRING
	PORT="$(ls -l $DIR 2>/dev/null | egrep -i "$PORTSTRING")"
	PORT="$(echo "$PORT" | cut -d '>' -f2 | tr -d ' ./')"
	[[ $PORT == "" ]] && Usage "Unable to find serial port connection to radio using search string '$PORTSTRING'"
	PORT="/dev/${PORT}"
fi

RIGCTL="$(command -v rigctl) -m $DEV -r $PORT -s $SPEED"
$RIGCTL get_info >/dev/null || { echo "Unable to communicate with radio via $PORT @ $SPEED bps.  Check serial port and speed."; exit 1; }

declare -A MINFREQ
declare -A MAXFREQ
MINFREQ[A]="118000000"
MINFREQ[B]="136000000"
MAXFREQ[A]="524000000"
MAXFREQ[B]="1300000000"

declare -A SIDE
SIDE[A]=0
SIDE[B]=1

GetSet () {
   RESULT="$($RIGCTL w "$1")"
   [ $? -eq 0 ] || { echo "ERROR: $RESULT  Is the radio's PC port set to $SPEED?"; exit 1; }
   RESULT="$(echo $RESULT | cut -d' ' -f2- | tr -cd '\40-\176')"
   echo "$RESULT"
}

PrintMHz () {
   echo "$(printf "%0.4f" $(bc -l <<< "$1/1000000")) MHz"
}

PrintMenu () {
	MU=($(echo $1 | tr -s ',' ' '))
	echo $MU
}

SetMenu () {
	# $1 is the menu input, comma separated
	# $2 is the parameter to change (1-42)
	# $3 is the value to set that parameter to

	MU=($(echo $1 | tr -s ',' ' '))
	MU[$2]="$3"
	# Convert back to comma separated string
   UM="${MU[@]}"
	echo ${UM// /,}
}

PrintDataSide () {
   local S=( "A" "B" "TX A, RX B" "TX B, RX A" )
   local MU=($(echo $1 | tr -s ',' ' '))
   echo ${S[${MU[37]}]} 
}

PrintTimeout () {
	local T=( "3" "5" "10" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${T[${MU[15]}]}
}

PrintAPO () {
	local T=( "off" "30 minutes" "60 minutes" "90 minutes" "120 minutes" "180 minutes" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${T[${MU[36]}]}
}

PrintSQCsource () {
	local T=( "off" "busy" "SQL" "TX" "BUSY or TX" "SQL or TX" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${T[${MU[39]}]}
}

PrintSpeed () {
	local T=( "1200" "9600" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${T[${MU[38]}]}
}

PrintFreq () {
   F=($(echo $1 | tr -s ',' ' '))
   declare -a FF
   if [[ "$2" == "ME" ]]
   then
      FF[0]="Memory Channel"
   else
      FF[0]="Side"
   fi
   FF[1]="Frequency"
   FF[2]="Step Size"
   FF[3]="Shift Direction"
   FF[4]="Reverse"
   FF[5]="Tone Status"
   FF[6]="CTCSS Status"
   FF[7]="DCS Status"
   FF[8]="Tone frequency"
   FF[9]="CTCSS frequency"
   FF[10]="DCS frequency"
   FF[11]="Offset frequency in Hz"
   FF[12]="Mode"
   if [[ "$2" == "ME" ]]
   then
      FF[13]="Frequency"
      FF[14]="Unknown"
      FF[15]="Lock out"
   fi

   SS=( "5" "6.25" "28.33" "10" "12.5" "15" "20" "25" "30" "50" "100" )
   SD=( "Simplex" "Up" "Down" "Split" )
   TF=( "67" "69.3" "71.9" "74.4" "77" "79.7" "82.5" "85.4" "88.5" "91.5" "94.8" \
         "97.4" "100" "103.5" "107.2" "110.9" "114.8" "118.8" "123" "127.3" "131.8" \
         "136.5" "141.3" "146.2" "151.4" "156.7" "162.2" "167.9" "173.8" "179.9" \
         "186.2" "192.8" "203.5" "240.7" "210.7" "218.1" "225.7" "229.1" "233.6" \
         "241.6" "250.3" "254.1" )
   DCS=( "23" "25" "26" "31" "32" "36" "43" "47" "51" "53" "54" "65" "71" "72" \
         "73" "74" "114" "115" "116" "122" "125" "131" "132" "134" "143" "145" \
         "152" "155" "156" "162" "165" "172" "174" "205" "212" "223" "225" "226" \
         "243" "244" "245" "246" "251" "252" "255" "261" "263" "265" "266" "271" \
         "274" "306" "311" "315" "325" "331" "332" "343" "346" "351" "356" "364" \
         "365" "371" "411" "412" "413" "423" "431" "432" "445" "446" "452" "454" \
         "455" "462" "464" "465" "466" "503" "506" "516" "523" "565" "532" "546" \
         "565" "606" "612" "624" "627" "631" "632" "654" "662" "664" "703" "712" \
         "723" "731" "732" "734" "743" "754" )
   M=( "FM" "AM" "NFM" )
   L=( "Off" "On" )
   S=( "A" "B" )
   if [[ $2 == "ME" ]]
   then
      echo "Memory Channel: ${F[0]}" 
   else
      echo "Side: ${S[${F[0]}]}" 
   fi
   echo "Frequency: $(PrintMHz ${F[1]})"
   echo "Step Size: ${SS[$((10#${F[2]}))]} KHz"
   echo "Shift Direction: ${SD[$((10#${F[3]}))]}"
   echo "Reverse: ${L[${F[4]}]}"
   echo "Tone Status: ${L[${F[5]}]}"
   echo "CTCSS Status: ${L[${F[6]}]}"
   echo "DCS Status: ${L[${F[7]}]}"
   echo "Tone Frequency: ${TF[$((10#${F[8]}))]} Hz"
   echo "CTCSS Frequency: ${TF[$((10#${F[9]}))]} Hz"
   echo "DCS Frequency: ${DCS[$((10#${F[10]}))]} Hz" 
   echo "Offset Frequency: $(PrintMHz ${F[11]})"
   echo "Modulation: ${M[${F[12]}]}" 
   if [[ $2 == "ME" ]]
   then
      #echo "Frequency?: $(PrintMHz ${F[13]})"
      #echo "Unknown Parameter: ${F[14]}"
      echo "Lockout: ${L[${F[15]}]}"
   fi
}

case "$P1" in
   GET)
      case "$P2" in
         INFO)
            echo "Model: $(GetSet "ID")"
            echo "Serial: $(GetSet "AE")"
            $0 -p $PORT GET APO
            $0 -p $PORT GET TIMEOUT
            $0 -p $PORT GET PTTCTRL
            $0 -p $PORT GET DATA
            $0 -p $PORT GET SPEED
            echo "------------------------------------"
            $0 -p $PORT GET A FREQ
            $0 -p $PORT GET A POWER
            echo "------------------------------------"
            $0 -p $PORT GET B FREQ
            $0 -p $PORT GET B POWER
            exit 0
            ;;
         A|B)
            ;;
			DATA)
				echo "External Data is on Side $(PrintDataSide $(GetSet "MU"))"
				exit 0
				;;
			TIME*)
				echo "TX Timeout is $(PrintTimeout $(GetSet "MU")) minutes"
				exit 0
				;;
			APO)
				echo "APO is $(PrintAPO $(GetSet "MU"))"
				exit 0
				;;
			SQC)
				echo "SQC source is $(PrintSQCsource $(GetSet "MU"))"
				exit 0
				;;
			SPEED)
				echo "External data speed is $(PrintSpeed $(GetSet "MU"))"
				exit 0
				;;
         PTTCTRL)
   			ANS="$(GetSet "BC")"
   			CTRL=${ANS%,*}           
   			PTT=${ANS#*,}
   			case "$PTT" in
      			0)
         			echo "PTT is on Side A"
         			;;   
      			1)
         			echo "PTT is on Side B"
         			;;   
      			*)
         			echo "ERROR: Unable to determine PTT state $PTT"
         			exit 1
						;;
   			esac
   			case "$CTRL" in
      			0)
         			echo "CTRL is on Side A"
         			;;   
      			1)
         			echo "CTRL is on Side B"
         			;;   
      			*)
         			echo "ERROR: Unable to determine CTRL state $CTRL."
         			exit 1
						;;
   			esac
            exit 0
            ;;
         PO*)
            $0 -p $PORT GET A POWER
            $0 -p $PORT GET B POWER
            exit 0
            ;;
         MO*)
            $0 -p $PORT GET A MODE
            $0 -p $PORT GET B MODE
            exit 0
            ;;
         MEM*)
            if ((P3>=0 && P3<=999))
            then
               ANS="$(GetSet "ME $(printf "%03d" $((10#$P3)))")"
               if [[ "$ANS" == "N" ]]
               then
                  echo "Memory $(printf "%03d" $((10#$P3))) is empty."
               else
                  PrintFreq "$ANS" "ME"
                  ANS="$(GetSet "MN $(printf "%03d" $((10#$P3)))")"
                  echo "Name: ${ANS#*,}"
               fi
               exit 0
            else
               Usage "Memory location must be between 0 and 999"
               exit 1
            fi
            ;;
			MEN*)
				GetSet "MU"
				exit 0
				;;
         *)
            Usage "Invalid GET command"
            ;;
      esac
      ;;
   SET)
      case $P2 in
         A|B) # Handled in case $P3 section below 
				;;
			SP*) # External Data Speed
				ANS="$(GetSet "MU")"
      		case $P3 in
					1200)
						ANS="$(GetSet "MU $(SetMenu $ANS 38 0)")"
						;;
 					9600)
						ANS="$(GetSet "MU $(SetMenu $ANS 38 1)")"
						;;
					*)
      				Usage "Valid speed options are 1200 and 9600"
			   		;;	
				esac
				$0 -p $PORT GET SPEED
				exit 0
				;;
			APO) # Auto power off
				ANS="$(GetSet "MU")"
      		case $P3 in
					OFF)
						ANS="$(GetSet "MU $(SetMenu $ANS 36 0)")"
						;;
					30)
						ANS="$(GetSet "MU $(SetMenu $ANS 36 1)")"
						;;
					60)
						ANS="$(GetSet "MU $(SetMenu $ANS 36 2)")"
						;;
					90)
						ANS="$(GetSet "MU $(SetMenu $ANS 36 3)")"
						;;
					120)
						ANS="$(GetSet "MU $(SetMenu $ANS 36 4)")"
						;;
					180)
						ANS="$(GetSet "MU $(SetMenu $ANS 36 5)")"
						;;
					*)
      				Usage "Valid APO options are off, 30, 60, 90, 120, 180"
			   		;;	
				esac
				$0 -p $PORT GET APO
				exit 0
				;;
			SQC) # SQC source
				ANS="$(GetSet "MU")"
      		case $P3 in
					OFF)
						ANS="$(GetSet "MU $(SetMenu $ANS 39 0)")"
						;;
					BUSY)
						ANS="$(GetSet "MU $(SetMenu $ANS 39 1)")"
						;;
					SQL)
						ANS="$(GetSet "MU $(SetMenu $ANS 39 2)")"
						;;
					TX)
						ANS="$(GetSet "MU $(SetMenu $ANS 39 3)")"
						;;
					BUSYTX)
						ANS="$(GetSet "MU $(SetMenu $ANS 39 4)")"
						;;
					SQLTX)
						ANS="$(GetSet "MU $(SetMenu $ANS 39 5)")"
						;;
					*)
      				Usage "Valid SQC options are off, busy, sql, tx, busytx, sqltx"
			   		;;	
				esac
				$0 -p $PORT GET SQC
				exit 0
				;;
			TIME*) # TX Timeout
				ANS="$(GetSet "MU")"
      		case $P3 in
					3)
						ANS="$(GetSet "MU $(SetMenu $ANS 15 0)")"
						;;
					5)
						ANS="$(GetSet "MU $(SetMenu $ANS 15 1)")"
						;;
					10)
						ANS="$(GetSet "MU $(SetMenu $ANS 15 2)")"
						;;
					*)
      				Usage "Valid timeout options are 3, 5, 10"
			   		;;	
				esac
				$0 -p $PORT GET TIMEOUT
				exit 0
				;;
         *)
            Usage "Invalid SET command"
            ;;
      esac
      ;;
   CO*) # Command
      ANS="$(GetSet "$P2")"
      echo "$ANS"
      exit 0
      ;;
   HELP)
      Usage
      ;;
   *)
      Usage "Valid commands are GET, SET and HELP" 
		;;
esac

declare -a MODE1
MODE1[0]="VFO"; MODE1[1]="Memory"; MODE1[2]="Call"; MODE1[3]="WX";

case "$P3" in
   F*) # Frequency
      case "$P1" in
         GET)
            ANS="$(GetSet "FO ${SIDE[$P2]}")" 
            PrintFreq "$ANS" "FO"
            ANS="$(GetSet "VM ${SIDE[$P2]}")" 
            echo -n "Side $P2 is in ${MODE1[$ANS]} mode.  "
				if [[ ${MODE1[$ANS]} == "Memory" ]]
				then
					ANS="$(GetSet "MR ${SIDE[$P2]}")"
					ANS="$(GetSet "MN ${ANS#*,}")"
					echo "Memory location: $ANS"
				else
					echo
				fi
            ;;
         SET)
            FR=$(printf "%0.f" $(bc -l <<< "$P4*1000000"))
            if (( $FR <= ${MAXFREQ[$P2]} )) && (( $FR >= ${MINFREQ[$P2]} ))
            then
               ANS="$(GetSet "VM ${SIDE[$P2]},0")" # Set side to VFO before setting frequency
               ANS="$(GetSet "FO ${SIDE[$P2]},$(printf "%010d" $((10#$FR))),0,0,0,0,0,0,00,00,000,00000000,0")"
               $0 -p $PORT GET $P2 FREQ
            else
               Usage "Frequency must be between $(PrintMHz ${MINFREQ[$P2]}) and $(PrintMHz ${MAXFREQ[$P2]})"
            fi
            ;; 
      esac # $P1
      ;;
   MO*) # Mode
      case "$P1" in
         GET)
            ANS="$(GetSet "VM ${SIDE[$P2]}")" 
            echo -n "Side $P2 is in ${MODE1[$ANS]} mode"
				if [[ ${MODE1[$ANS]} == "Memory" ]]
				then
					ANS="$(GetSet "MR ${SIDE[$P2]}")"
					echo ": Memory location ${ANS#*,}"
				else
					echo
				fi
            ;;
         SET)
            case "$P4" in
               VFO)
                  M=0
                  ;;
               MEMORY)
                  M=1
                  ;;
               CALL)
                  M=2
                  ;;
               WX)
                  M=3
                  ;;
               *)
                  Usage "Valid modes are VFO, MEMORY, CALL, and WX"
                  ;;
            esac 
            ANS="$(GetSet "VM ${SIDE[$P2]},$M")"
            $0 -p $PORT GET $P2 MODE
            ;; 
      esac # $P1
      ;;
   PO*) # Power
      case "$P1" in
         GET)
            ANS="$(GetSet "PC ${SIDE[$P2]}")" 
            declare -A POWER
            POWER[0]="high"; POWER[1]="medium"; POWER[2]="low"
            echo "Side $P2 is at ${POWER[${ANS#*,}]} power"
            ;;
         SET)
            declare -A POWER
            POWER[H]=0; POWER[M]=1; POWER[L]=2
            case "$P4" in
               H|M|L)
                  ANS="$(GetSet "PC ${SIDE[$P2]},${POWER[$P4]}")"
                  $0 -p $PORT GET $P2 POWER
                  ;; 
               *)
                  Usage "Valid power settings are H, M, and L"
						;;
            esac
            ;;
      esac
      ;;
   SQ*) # Squelch
      case "$P1" in
         GET)
            ANS="$(GetSet "SQ ${SIDE[$P2]}")" 
            echo "Side $P2 squelch is at $((16#${ANS#*,})) out of 31"
            ;;
         SET)
            if ((P4>=0 && P4<=31))
            then
               P4="$(printf "%02X" $P4)"
               ANS="$(GetSet "SQ ${SIDE[$P2]},$P4")" 
               echo "Side $P2 squelch is at $((16#${ANS#*,})) out of 31"
            else
               Usage "Valid squelch settings are between 0 and 31 inclusive"
            fi
            ;;
      esac
      ;;
   PTTCTRL) # PTT/CTRL
      ANS="$(GetSet "BC ${SIDE[$P2]},${SIDE[$P2]}")" 
      $0 -p $PORT GET PTTCTRL
      ;;
   PTT) # PTT
      ANS="$(GetSet "BC")"
      CTRL=${ANS%,*}           
      PTT=${ANS#*,}
      if [[ "$P2" == "A" ]]
      then
         ANS="$(GetSet "BC $CTRL,0")" 
         $0 -p $PORT GET PTTCTRL
      else
         ANS="$(GetSet "BC $CTRL,1")" 
         $0 -p $PORT GET PTTCTRL
      fi      
      ;;
   CTRL) # CTRL
      ANS="$(GetSet "BC")"
      CTRL=${ANS%,*}           
      PTT=${ANS#*,}
      if [[ "$P2" == "A" ]]
      then
         ANS="$(GetSet "BC 0,$PTT")" 
         $0 -p $PORT GET PTTCTRL
      else
         ANS="$(GetSet "BC 1,$PTT")" 
         $0 -p $PORT GET PTTCTRL
      fi      
      ;;
	DA*) # External Data Side
		ANS="$(GetSet "MU")"
      if [[ "$P2" == "A" ]]
      then
			ANS="$(GetSet "MU $(SetMenu $ANS 37 0)")"
		else
			ANS="$(GetSet "MU $(SetMenu $ANS 37 1)")"
		fi
		$0 -p $PORT GET DATA
		;;
   MEM*)
      if ((P4>=0 && P4<=999))
      then
         ANS="$(GetSet "ME $(printf "%03d" $((10#$P4)))")"
         if [[ "$ANS" == "N" ]]
         then
            echo "Memory $(printf "%03d" $((10#$P4))) is empty"
         else
            ANS="$(GetSet "VM ${SIDE[$P2]},1")" # Set side to memory mode
            ANS="$(GetSet "MR ${SIDE[$P2]},$(printf "%03d" $((10#$P4)))")"
            echo "Side: $P2"
            ANS="$(GetSet "ME ${ANS#*,}")"         
            PrintFreq "$ANS" "ME"
            ANS="$(GetSet "MN $(printf "%03d" $((10#$P4)))")"
            echo "Name: ${ANS#*,}"
         fi
      else
         Usage "Memory location must be between 0 and 999"
      fi
      ;;
   *)
      Usage "Valid options are FREQUENCY, POWER, PTT, CTRL and COMMAND" 
		;;
esac
