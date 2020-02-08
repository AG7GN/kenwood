#!/bin/bash
#================================================================
# HEADER
#================================================================
#% SYNOPSIS
#+   ${SCRIPT_NAME} [-hv] [-s[string]] [-p[port]] COMMAND
#%
#% DESCRIPTION
#%   CAT control script for Kenwood TM-D710G/TM-V71A.
#%   Set radio's PC port speed to ${SPEED} or change SPEED variable in this script to
#%   match radio's setting.
#%
#% OPTIONS
#%    -s [string], --string=[string]
#%                                String to string to grep for in /dev/serial/by-id 
#%                                to determine the serial port used to connect to your 
#%                                radio.  Default string: ${DEFAULT_PORTSTRING}
#%                                
#%    -p [port], --port=[port]    Serial port connection to radio (ex. /dev/ttyUSB0).
#%                                If both -p and -s are supplied, -p will be used.
#% 
#%    -h, --help                  Print this help
#%    -v, --version               Print script information
#%
#% COMMANDS
#%  ${SCRIPT_NAME} [OPTIONS] get apo      Prints Auto Power Off setting
#%  ${SCRIPT_NAME} [OPTIONS] get data     Prints the side configured for external data
#%  ${SCRIPT_NAME} [OPTIONS] get info     Prints some radio settings
#%  ${SCRIPT_NAME} [OPTIONS] get memory <channel>    
#%                                Prints memory channel configuration
#%  ${SCRIPT_NAME} [OPTIONS] get menu     Prints raw menu contents output 
#%                                (diagnostic command)
#%  ${SCRIPT_NAME} [OPTIONS] get mode     Prints mode (modulation) settings
#%  ${SCRIPT_NAME} [OPTIONS] get power    Prints power settings
#%  ${SCRIPT_NAME} [OPTIONS] get pttctrl  Prints PTT and CTRL settings
#%  ${SCRIPT_NAME} [OPTIONS] get speed    Prints external data speed (1200|9600)
#%  ${SCRIPT_NAME} [OPTIONS] get sqc      Prints SQC source
#%  ${SCRIPT_NAME} [OPTIONS] get a|b squelch
#%                                Prints squelch settings for side A or B
#%  ${SCRIPT_NAME} [OPTIONS] get timeout  Prints TX timeout setting
#%  ${SCRIPT_NAME} [OPTIONS] get vhf|uhf aip 
#%                                Prints AIP setting for VHF or UHF
#%  ${SCRIPT_NAME} [OPTIONS] set apo off|30|60|90|120|180     
#%                                Sets Automatic Power Off (minutes)
#%  ${SCRIPT_NAME} [OPTIONS] set a|b ctrl 
#%                                Sets CTRL to side A or B
#%  ${SCRIPT_NAME} [OPTIONS] set a|b data 
#%                                Sets external data to side A or B
#%  ${SCRIPT_NAME} [OPTIONS] set a|b freq <MHz>
#%                                Sets side A or B to VFO and sets frequency to <MHz>
#%  ${SCRIPT_NAME} [OPTIONS] set a|b memory <memory>
#%                                Sets side A or B to memory mode and assigns
#%                                <memory> location to it
#%  ${SCRIPT_NAME} [OPTIONS] set a|b mode vfo|memory|call|wx
#%                                Sets side A or B mode
#%  ${SCRIPT_NAME} [OPTIONS] set a|b power l|m|h     
#%                                Sets side A or B to Low, Medium or High power
#%  ${SCRIPT_NAME} [OPTIONS] set a|b ptt             
#%                                Sets PTT to side A or B
#%  ${SCRIPT_NAME} [OPTIONS] set a|b pttctrl
#%                                Sets PTT and CTRL to side A or B
#%  ${SCRIPT_NAME} [OPTIONS] set speed 1200|9600     
#%                                Sets external data speed to 1200 or 9600
#%  ${SCRIPT_NAME} [OPTIONS] set a|b squelch <0-31>  
#%                                Sets squelch level for side A or B
#%  ${SCRIPT_NAME} [OPTIONS] set timeout 3|5|10      
#%                                Sets transmit timeout (minutes)
#%  ${SCRIPT_NAME} [OPTIONS] set vhf|uhf aip on|off  
#%                                Sets squelch level for side A or B
#%  ${SCRIPT_NAME} [OPTIONS] help         Prints this help screen
#%
#%
#% EXAMPLES
#%    
#%  Locate serial port file name containing ${DEFAULT_PORTSTRING} (default search string),
#%  then set APO to 30 minutes:
#%
#%     ${SCRIPT_NAME} set apo 30
#%
#%  Override the default search string ${DEFAULT_PORTSTRING} to locate serial port
#%  connected to radio, then get radio information:
#%
#%     ${SCRIPT_NAME} -s Prolific_Technology get info
#%
#%  Specify the serial port used to connect to your radio then set radio TX timeout 
#%  to 3 minutes:
#%
#%     ${SCRIPT_NAME} -p /dev/ttyUSB0 set timeout 3
#%
#================================================================
#- IMPLEMENTATION
#-    version         ${SCRIPT_NAME} 5.0.4
#-    author          Steve Magnuson, AG7GN
#-    license         CC-BY-SA Creative Commons License
#-    script_id       0
#-
#================================================================
#  HISTORY
#     20180125 : Steve Magnuson : Script creation
#     20200203 : Steve Magnuson : New script template
# 
#================================================================
#  DEBUG OPTION
#    set -n  # Uncomment to check your syntax, without execution.
#    set -x  # Uncomment to debug this shell script
#
#================================================================
# END_OF_HEADER
#================================================================

SYNTAX=false
DEBUG=false

#============================
#  FUNCTIONS
#============================

function TrapCleanup() {
  [[ -d "${TMPDIR}" ]] && rm -r "${TMPDIR}"
  exit 0
}

function SafeExit() {
  # Delete temp files, if any
  [[ -d "${TMPDIR}" ]] && rm -r "${TMPDIR}"
  trap - INT TERM EXIT
  exit
}

function ScriptInfo() { 
	HEAD_FILTER="^#-"
	[[ "$1" = "usage" ]] && HEAD_FILTER="^#+"
	[[ "$1" = "full" ]] && HEAD_FILTER="^#[%+]"
	[[ "$1" = "version" ]] && HEAD_FILTER="^#-"
	head -${SCRIPT_HEADSIZE:-99} ${0} | grep -e "${HEAD_FILTER}" | \
	sed -e "s/${HEAD_FILTER}//g" \
	    -e "s/\${SCRIPT_NAME}/${SCRIPT_NAME}/g" \
	    -e "s/\${SPEED}/${SPEED}/g" \
	    -e "s/\${DEFAULT_PORTSTRING}/${DEFAULT_PORTSTRING}/g"
}

function Usage() { 
	printf "Usage: "
	ScriptInfo usage
	exit
}

function Die () {
	echo "${*}"
	SafeExit
}

#----------------------------

function GetSet () {
   RESULT="$($RIGCTL w "$1")"
   [ $? -eq 0 ] || Die "rigctl ERROR: $RESULT  Is the radio's PC port set to $SPEED?"
   RESULT="$(echo $RESULT | cut -d' ' -f2- | tr -cd '\40-\176')"
   echo "$RESULT"
}

function PrintMHz () {
   echo "$(printf "%0.4f" $(bc -l <<< "$1/1000000")) MHz"
}

function PrintMenu () {
	MU=($(echo $1 | tr -s ',' ' '))
	echo $MU
}

function SetMenu () {
	# $1 is the menu input, comma separated
	# $2 is the parameter to change (1-42)
	# $3 is the value to set that parameter to

	MU=($(echo $1 | tr -s ',' ' '))
	MU[$2]="$3"
	# Convert back to comma separated string
   UM="${MU[@]}"
	echo ${UM// /,}
}

function PrintDataSide () {
   local S=( "A" "B" "TX A, RX B" "TX B, RX A" )
   local MU=($(echo $1 | tr -s ',' ' '))
   echo ${S[${MU[37]}]} 
}

function PrintTimeout () {
	local T=( "3" "5" "10" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${T[${MU[15]}]}
}

function PrintVHFAIP () {
   local STATE=( "Off" "On" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${STATE[${MU[11]}]}
}

function PrintUHFAIP () {
   local STATE=( "Off" "On" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${STATE[${MU[12]}]}
}

function PrintAPO () {
	local T=( "off" "30 minutes" "60 minutes" "90 minutes" "120 minutes" "180 minutes" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${T[${MU[36]}]}
}

function PrintSQCsource () {
	local T=( "off" "busy" "SQL" "TX" "BUSY or TX" "SQL or TX" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${T[${MU[39]}]}
}

function PrintSpeed () {
	local T=( "1200" "9600" )
   local MU=($(echo $1 | tr -s ',' ' '))
	echo ${T[${MU[38]}]}
}

function PrintFreq () {
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

#============================
#  FILES AND VARIABLES
#============================

  #== general variables ==#
SCRIPT_NAME="$(basename ${0})" # scriptname without path
SCRIPT_DIR="$( cd $(dirname "$0") && pwd )" # script directory
SCRIPT_FULLPATH="${SCRIPT_DIR}/${SCRIPT_NAME}"
SCRIPT_ID="$(ScriptInfo | grep script_id | tr -s ' ' | cut -d' ' -f3)"
SCRIPT_HEADSIZE=$(grep -sn "^# END_OF_HEADER" ${0} | head -1 | cut -f1 -d:)

# Set Temp Directory
# -----------------------------------
# Create temp directory with three random numbers and the process ID
# in the name.  This directory is removed automatically at exit.
# -----------------------------------
#TMPDIR="/tmp/${SCRIPT_NAME}.$RANDOM.$RANDOM.$RANDOM.$$"
#(umask 077 && mkdir "${TMPDIR}") || {
#  Die "Could not create temporary directory! Exiting."
#}
VERSION="$(ScriptInfo version | grep version | tr -s ' ' | cut -d' ' -f 4)" 

DEV=234
SPEED=57600
DIR="/dev/serial/by-id"
# The following PORTSTRING will be used if the '-s PORTSTRING' argument is not supplied
DEFAULT_PORTSTRING="USB-Serial|RT_Systems|usb-FTDI"
PORTSTRING="$DEFAULT_PORTSTRING"

declare -A MINFREQ
MINFREQ[A]="118000000"
MINFREQ[B]="136000000"

declare -A MAXFREQ
MAXFREQ[A]="524000000"
MAXFREQ[B]="1300000000"

declare -A SIDE
SIDE[A]=0
SIDE[B]=1


#============================
#  PARSE OPTIONS WITH GETOPTS
#============================
  
#== set short options ==#
SCRIPT_OPTS=':hp:s:v-:'

#== set long options associated with short one ==#
typeset -A ARRAY_OPTS
ARRAY_OPTS=(
	[help]=h
	[version]=v
	[man]=h
	[string]=s
	[port]=p
)

# Parse options
while getopts ${SCRIPT_OPTS} OPTION ; do
	# Translate long options to short
	if [[ "x$OPTION" == "x-" ]]; then
		LONG_OPTION=$OPTARG
		LONG_OPTARG=$(echo $LONG_OPTION | grep "=" | cut -d'=' -f2)
		LONG_OPTIND=-1
		[[ "x$LONG_OPTARG" = "x" ]] && LONG_OPTIND=$OPTIND || LONG_OPTION=$(echo $OPTARG | cut -d'=' -f1)
		[[ $LONG_OPTIND -ne -1 ]] && eval LONG_OPTARG="\$$LONG_OPTIND"
		OPTION=${ARRAY_OPTS[$LONG_OPTION]}
		[[ "x$OPTION" = "x" ]] &&  OPTION="?" OPTARG="-$LONG_OPTION"
		
		if [[ $( echo "${SCRIPT_OPTS}" | grep -c "${OPTION}:" ) -eq 1 ]]; then
			if [[ "x${LONG_OPTARG}" = "x" ]] || [[ "${LONG_OPTARG}" = -* ]]; then 
				OPTION=":" OPTARG="-$LONG_OPTION"
			else
				OPTARG="$LONG_OPTARG";
				if [[ $LONG_OPTIND -ne -1 ]]; then
					[[ $OPTIND -le $Optnum ]] && OPTIND=$(( $OPTIND+1 ))
					shift $OPTIND
					OPTIND=1
				fi
			fi
		fi
	fi

	# Options followed by another option instead of argument
	if [[ "x${OPTION}" != "x:" ]] && [[ "x${OPTION}" != "x?" ]] && [[ "${OPTARG}" = -* ]]; then 
		OPTARG="$OPTION" OPTION=":"
	fi

	# Finally, manage options
	case "$OPTION" in
		h) 
			ScriptInfo full
			exit 0
			;;
		p) 
			PORT="$OPTARG"
			;;
		s) 
			PORTSTRING="$OPTARG" 
			;;
		v) 
			ScriptInfo version
			exit 0
			;;
		:) 
			Die "${SCRIPT_NAME}: -$OPTARG: option requires an argument"
			;;
		?) 
			Die "${SCRIPT_NAME}: -$OPTARG: unknown option"
			;;
	esac
done
shift $((${OPTIND} - 1)) ## shift options


#============================
#  MAIN SCRIPT
#============================

# Trap bad exits with cleanup function
trap TrapCleanup EXIT INT TERM

# Exit on error. Append '||true' when you run the script if you expect an error.
set -o errexit

# Check Syntax if set
$SYNTAX && set -n
# Run in debug mode, if set
$DEBUG && set -x 

(( $# == 0 )) && Usage

command -v bc >/dev/null || Die "Cannot find bc application.  To install it, run: sudo apt update && sudo apt install -y bc"
command -v rigctl >/dev/null || Die "Cannot find rigctl application.  Install hamlib."

P1="${1^^}"
P2="${2^^}"
P3="${3^^}"
P4="${4^^}"

[[ $P1 == "HELP" ]] && ScriptInfo full

if [[ $PORT == "" ]]
then # User did not supply serial port.  Search for it using $PORTSTRING
	MATCHES=$(ls $DIR 2>/dev/null | egrep -i "$PORTSTRING" | wc -l)
	case $MATCHES in
		0)
			Die "No devices found in $DIR with file names that contain string \"$PORTSTRING\""
			;;
		1) 
			PORT="$(ls -l $DIR 2>/dev/null | egrep -i "$PORTSTRING")"
			PORT="$(echo "$PORT" | cut -d '>' -f2 | tr -d ' ./')"
			[[ "$PORT" == "" ]] && Die "Unable to find serial port connection to radio using search string '$PORTSTRING'"
			PORT="/dev/${PORT}"
			;;
		*)
			Die "More than one cable in $DIR matches $PORTSTRING.  You must specify the cable to use with the '-p' or '-s' options."
			;;
	esac
fi

RIGCTL="$(command -v rigctl) -m $DEV -r $PORT -s $SPEED"
$RIGCTL get_info >/dev/null || Die "Unable to communicate with radio via $PORT @ $SPEED bps.  Check serial port and speed."

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
            $0 -p $PORT GET VHF AIP
            $0 -p $PORT GET UHF AIP
            echo "------------------------------------"
            $0 -p $PORT GET A FREQ
            $0 -p $PORT GET A POWER
            echo "------------------------------------"
            $0 -p $PORT GET B FREQ
            $0 -p $PORT GET B POWER
            exit 0
            ;;
         A|B|VHF|UHF)
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
         			Die "ERROR: Unable to determine PTT state $PTT"
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
         			Die "ERROR: Unable to determine CTRL state $CTRL."
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
               Die "Memory location must be between 0 and 999"
               exit 1
            fi
            ;;
			MEN*)
				GetSet "MU"
				exit 0
				;;
         *)
            Die "Invalid GET command"
            ;;
      esac
      ;;
   SET)
      case $P2 in
         A|B|VHF|UHF) # Handled in case $P3 section below 
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
      				Die "Valid speed options are 1200 and 9600"
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
      				Die "Valid APO options are off, 30, 60, 90, 120, 180"
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
      				Die "Valid SQC options are off, busy, sql, tx, busytx, sqltx"
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
      				Die "Valid timeout options are 3, 5, 10"
			   		;;	
				esac
				$0 -p $PORT GET TIMEOUT
				exit 0
				;;
         *)
            Die "Invalid SET command"
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
      Die "Valid commands are GET, SET, and HELP; also VHF and UHF for AIP." 
		;;
esac

declare -a MODE1
MODE1[0]="VFO"; MODE1[1]="Memory"; MODE1[2]="Call"; MODE1[3]="WX";

case "$P3" in
	AIP) # Advanced Intercept Point
		ANS="$(GetSet "MU")"
		case "$P2" in
			VHF)
				case "$P1" in
					GET)
						echo "VHF Advanced Intercept Point (AIP) is $(PrintVHFAIP $(GetSet "MU"))"
						;;
					SET)
		            case "$P4" in
							OFF)
								ANS="$(GetSet "MU $(SetMenu $ANS 11 0)")"
								;;
							ON)
								ANS="$(GetSet "MU $(SetMenu $ANS 11 1)")"
								;;
							*) 
								Die "AIP state must be OFF or ON"
								;;
						esac
						echo "VHF Advanced Intercept Point (AIP) is $(PrintVHFAIP $(GetSet "MU"))"
						;;
				esac
				;;
			UHF)
				case "$P1" in
					GET)
						echo "UHF Advanced Intercept Point (AIP) is $(PrintUHFAIP $(GetSet "MU"))"
						;;
					SET)
		            case "$P4" in
							OFF)
								ANS="$(GetSet "MU $(SetMenu $ANS 12 0)")"
								
								;;
							ON)
								ANS="$(GetSet "MU $(SetMenu $ANS 12 1)")"
								;;
							*) 
								Die "AIP state must be OFF or ON"
								;;
						esac
						echo "UHF Advanced Intercept Point (AIP) is $(PrintUHFAIP $(GetSet "MU"))"
						;;
				esac
				;;
		esac
		;;
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
               Die "Frequency must be between $(PrintMHz ${MINFREQ[$P2]}) and $(PrintMHz ${MAXFREQ[$P2]})"
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
                  Die "Valid modes are VFO, MEMORY, CALL, and WX"
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
                  Die "Valid power settings are H, M, and L"
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
               Die "Valid squelch settings are between 0 and 31 inclusive"
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
         Die "Memory location must be between 0 and 999"
      fi
      ;;
   *)
      Die "Valid options are AIP, FREQUENCY, POWER, PTT, CTRL and COMMAND" 
		;;
esac

SafeExit

