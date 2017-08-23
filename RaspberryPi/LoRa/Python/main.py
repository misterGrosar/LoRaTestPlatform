'''
This is Raspberry Pis 3 Model B Python script for running subprocess where
LoRa transceiver program (in our case written in C) is running.
  
NOTES: 
- 	If -f or -start command line arguments are present and there is no
	internet connection at script startup, program will not start untill
	first MQTT client connection timeout. After that program will write 
	results to file and to paho mqtts buffer (data in this buffer will
	be sent automatically when connection to broker will be established).
'''

import subprocess
import signal
import sys
import os
import paho.mqtt.client as mqtt
import json
from threading import Thread
from time import sleep
from time import time
import datetime

_DEVICE_ID = [-1] 	# Unique device id
_gpsLat = [0]		# GPS latitude 
_gpsLon = [0]		# GPS longitude
_locDesc = [""]		# Device location description

#LoRa settings
_receiver = [False] 			# True if this device is receiver, false if transmitter

_writeToFileArr = [False] 		# Does program writes to file too
_spreadingFactorArr = ["8"] 	# LoRa spreading factor
_bandwidthArr = ["7"] 			# LoRa bandwidth
_crcOnArr = [True]				# Is CRC on
_crcValueArr = ["4"]			# Coding rate value
_timeBetweenPackets = ["1000"] 	# Delay between airtime of two packets
_lowFrequency = [False] 		# If True, transciever operates on 434 MHz
_bidirect = [False]				# If true, device alternates between transmitter and receiver 


_args = []

_killAndStartNew = [False] 	# Flag to restart LoRa C subprocess
_isKilled = [False]			# Indicates that LoRa C subprocess is not running anymore
_startLoRaProgram = [False]	# Flag to start LoRa C subprocess
_debug = [False]

_DATA_BUFFER = [[]]						# Message buffer
_INIT_BUFFER_SIZE = [8]					# Initial message buffer size
_BUFFER_SIZE = [_INIT_BUFFER_SIZE[0]]	# Buffer size
_fileSuffix = [""]

_LoRaSubprocess = [""]			# LoRa C subprocess
_client = mqtt.Client()			# MQTT client
_connectedToServer = [False]	# Is MQTT client connected to broker


'''
This settings ARE OVERWRITTEN IN readDeviceSettings() method!!!
'''
# paho-MQTT settings
_topicSub = ["lora/test"]		# MQTTs topic name for retrieving settings and commands
_topicPub = ["lora/testPub"]	# MQTTs topic name for publishing messages
_username = [""]			# MQTTs username
_passwd = [""]				# MQTTs password
_ip = [""]			# MQTTs broker IP address
_port = [8883]					# MQTTs broker port
_keepAlive = [60]				# Time (in seconds) of inactivity, before ping is sent to MQTT server


def signalHandler(signal, frame):
	'''
	Handle SIGINT signal. Kill LoRa thread, sent unpublished data, 
	disconnect MQTT client and terminate the script.
	'''
	printAndLog("\nCtrl+C pressed. Exiting program.\n")

	# Prevent rerunning LoRa program
	_isKilled[0] = True
	_startLoRaProgram[0] = False

	if _LoRaSubprocess[0] is not "" and _LoRaSubprocess[0].poll() is None:
		try:
			# Kill LoRa C program running as subprocess
			_LoRaSubprocess[0].send_signal(signal)
		except Exception as e:
			printAndLog("ERROR killing C process with error code " + str(e.errno) + ": " + str(e))
	_LoRaSubprocess[0] = ""
	
	if _writeToFileArr[0]:
		saveToFile("EOF;\n\n");
	# Publish unpublished messages
	publishData()
	
	try:
		# Disconnect MQTT client
		_client.disconnect()
	except Exception as e:
		printAndLog("ERROR disconnecting MQTT client with error code " + str(e.errno) + ": " + str(e))
	# Terminate this script
	sys.exit(0)
	

def killOldProgram():
	'''
	Kill old LoRa C program and prevent automatic start of new one 
	untill new parameters are received via MQTT 
	'''
	if _LoRaSubprocess[0] is not "":
		printAndLog ("Killing current LoRa transciever.")
		try:
			# Kill LoRa C program running as subprocess
			_LoRaSubprocess[0].send_signal(signal.SIGINT)
		except Exception as e:
			printAndLog("ERROR killing C process with error code " + str(e.errno) + ": " + str(e))
	# Prevent starting new LoRa C program
	_killAndStartNew[0] = False
	
	if _writeToFileArr[0]:
		saveToFile("FINISHING_PROGRAM;\n\n");


def on_connect(client, userdata, rc):
	'''
	Method subscribes to the topic, when MQTT client is connected with MQTT broker
	'''
	printAndLog ("Connected with rc: " + str(rc))
	_connectedToServer[0] = True
	_client.subscribe(_topicSub[0], 0)


def on_message(client, userdata, msg):
	'''
	Method handles received message containing device settings and instructions
	'''
	settingId = 1
	restartTransmittion = False
	
	try:
		# Decode MQTT message to UTF-8
		msgPayloadStr = str(msg.payload.decode("utf-8"))
		printAndLog("Topic: "+ msg.topic+"\nMessage: " + msgPayloadStr)
	except Exception as e:
		printAndLog("ERROR decoding MQTTs message with error code " + str(e.errno) + ": " + str(e))
	
	try:
		# Parse message into JSON format
		loraSettingsJson = json.loads(msgPayloadStr)

		# Get settings and instructions for this device
		for dev in loraSettingsJson["devices"]:
			if dev["id"] == _DEVICE_ID[0]:
				restartTransmittion = dev["restartT"]
				
				# Get new settings only if LoRa C subprocess is going to be restarted
				if restartTransmittion:
					_startLoRaProgram[0] = dev["start"]
					_receiver[0] = dev["rec"]
					_bidirect[0] = dev["bidirectional"]
					settingId = dev["setId"]	
							
					if "gpsLat" in dev:
						_gpsLat[0] = dev["gpsLat"]
					if "gpsLon" in dev:
						_gpsLon[0] = dev["gpsLon"]
					if "locDesc" in dev:
						_locDesc[0] = dev["locDesc"]
					if "debug" in dev:
						_debug[0] = dev["debug"]
				break
				
		# Restart LoRa C subprocess		
		if restartTransmittion:	
			# Store data obtained so far to paho mqtts buffer (publish data). 
			# This data will be sent automatically when (if) client will connect to broker.
			publishData()
			
			# Buffer settings
			buffSettings = loraSettingsJson["buffer"]			
			_INIT_BUFFER_SIZE[0] = buffSettings["buffSize"]
		
			if not _receiver[0] and not _bidirect[0]:
				# Initial buffer size for transmitter is 1/4 of size of receivers, 
				# because transmitter has 3/4 less log messages for each transmitted 
				# packet than it does receiver (it doesn't have modem statuses).
				_INIT_BUFFER_SIZE[0] = _INIT_BUFFER_SIZE[0] / 4		
			_BUFFER_SIZE[0] = _INIT_BUFFER_SIZE[0]
			
			# Settings for LoRa C program (LoRa parameters)
			for param in loraSettingsJson["parameters"]:
				if param["settingId"] == settingId:	
					_bandwidthArr[0] = param["bw"]
					_spreadingFactorArr[0] = param["sf"]
					_crcOnArr[0] = param["crcOn"]
					_crcValueArr[0] = param["crcVal"]
					_timeBetweenPackets[0] = param["delay"]
					_lowFrequency[0] = param["lowFreq"]
					break
			
			_killAndStartNew[0] = True
			# Kill old LoRa C subprocess and start new one automatically
			killOldProgram()
	except Exception as e:
		printAndLog("ERROR parsing json from MQTT with error code " + str(e.errno) + ": " + str(e))


def runMQTTclient(topicSub, username, password, ip, port, keepAlive):
	'''
	Connect to MQTT broker and subscribe to topic
	'''
	# Callback methods
	_client.on_connect = on_connect
	_client.on_message = on_message

	#Set MQTT brokers credentials
	_client.username_pw_set(username, password)
	
	try:
		_client.connect(ip, port, keepAlive) # Connect to broaker
		_client.subscribe(topicSub, 0) # Subscribe to topic
	except IOError as e:
		if (e.errno == 101 or e.errno == 113):
			printAndLog("No connection to MQTT topic {}.\nNo internet connection. Writing to file.\n".format(topicSub))
			handleErr(topicSub, username, password, ip, port, keepAlive)				
			
		elif e.errno == 110:
			printAndLog("MQTT Connection timed out. Trying to reconect...")
			handleErr(topicSub, username, password, ip, port, keepAlive)
		else:
			printAndLog("NOT HANDLED ERROR with error code " + str(e.errno) + ": " + str(e))            

	_client.loop_start() # Loops forever and waits for messages from broker
	
	
def handleErr(topicSub, username, password, ip, port, keepAlive):
	'''
	Handle MQTT errors
	'''
	# Write this message only once 
	if _LoRaSubprocess[0] == "":
		# Even if there is no internet connection, run LoRa program
		# with last known settings (= settings from command line arguments)
		# and write data to file.
		setFileName()
		saveToFile("No internet connection. Staring writing to file.\n")
		
		_startLoRaProgram[0] = True
	
	sleep(30)
	# Try to reconnect
	runMQTTclient(topicSub, username, password, ip, port, keepAlive)
	
	    
def runLoRaProgram():
	'''
	------------- THIS IS SCRIPTS MOST IMPORTANT METHOD-----------------
	This method runs main transciever program and does all the hard work
	of parsing data form C program. It also publishes received data to 
	_topicPub MQTT topic.
	--------------------------------------------------------------------
	'''
	if _isKilled[0] == False:
		
		# Wait for start command before starting transciever
		while True:
			if _startLoRaProgram[0]:
				_startLoRaProgram[0] = False
				break
			# If kill command has been sent while program is idle 
			# (transciever is idle), then terminate this subprocess
			if _isKilled[0]:
				sys.exit(0)
			sleep(1)
		
		# Clear buffer
		resetBuffer()
		
		if _bidirect[0]:
			printAndLog("-------------------\nStarting new LoRa BIDIRECTIONAL transciever.\n-------------------\n")
		elif _receiver[0]:
			printAndLog("-------------------\nStarting new LoRa RECEIVER.\n-------------------\n")
		else:	
			printAndLog("-------------------\nStarting new LoRa TRANSMITTER.\n-------------------\n")
		# Set the file name for saving messages
		setFileName()

		# Prepare LoRa settings parameters array to pass them to LoRa program  
		_args = ["/home/pi/projects/LoRa/src/main"]

		# Transceiver works in bi-directional mode
		if _bidirect[0]:
			_args.append("-bi")
			
		# Device is receiver
		if _receiver[0]:
			_args.append("-r")
			
		# If True, transceiver works on 434 MHz, otherwise on 868 MHz
		if _lowFrequency[0]:
			_args.append("-lf")

		_args.append("-b=" + _bandwidthArr[0]) # set bandwidth
		_args.append("-s=" + _spreadingFactorArr[0]) # set spreading factor

		if _crcOnArr[0]: # If CRC is on
			_args.append("-c=1") 
			_args.append("-e=" + _crcValueArr[0]) # set coding rate 
		else:
			_args.append("-c=0")
			
		if not _receiver[0] or _bidirect[0]:
			# If this device is transmitter or works in bi-directional mode,
			# set delay between two packet transmittions
			_args.append("-d=" + _timeBetweenPackets[0]) 
		
		try:
			# Run C program in subprocess which is cappable
			# to communicate with Semtech SX1276 chip.
			# This program transmits/receives LoRa signal. 
			_LoRaSubprocess[0] = subprocess.Popen(_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except Exception as e:
			printAndLog("ERROR starting subprocess with error code " + str(e.errno) + ": " + str(e))
			# If there is no sufficient permission there is no need to continue. Kill the program
			if e.errno == 13:
				_isKilled[0] = True
				sys.exit(0)
		
		# Read subprocess output 
		while True:
			uploadData = False
			recievedDataJsonObj = ""
			ln = ""
			
			# Check if LoRa C subprocess is up and running
			if _LoRaSubprocess[0] == "":
				break
			else:
				try:
					# If LoRa C subprocess is running, catch its outputs
					ln = _LoRaSubprocess[0].stdout.readline().decode("UTF-8")
				except Exception as e:
					printAndLog("ERROR decoding string from C output with error code " + str(e.errno) + ": " + str(e))
				
			if '' == ln:
				break
			# Remove new line charactes in LoRa C output
			ln = ln.strip("\n")
			
			# If program is in debug mode, it prints results to console 
			# near the end of this function
			if not _debug[0]:
				print(ln)
			
			if "INFO" in ln:
				continue
			
			# This is only info about LoRa settings which LoRa C program is using.
			# This is LoRa C's forst output line when started 
			elif "SETTINGS" in ln:
				print(ln)
				# Is transceiver operates on low frequency (434 MHz)
				lowFreq = "false"
				if _lowFrequency[0]:
					lowFreq = "true"
				
				# Is transceiver operates in bi-directional mode
				bidirection = "false"
				if _bidirect[0]:
					bidirection = "true"
					
				# If transceiver operates in bidirectional mode, create file which correspond to first itteration of transceiver mode.
				# In first iteration transciever can either be a transmitter or receiver.
				if _receiver[0]:
					saveToFile("Receiving packets with LoRa signal parameters bw: {}, sf: {}, crc on: {}, cr: {}, lowFrequency: {}, bidirectional: {}.\n".format(
								_bandwidthArr[0], _spreadingFactorArr[0], _crcOnArr[0], _crcValueArr[0], lowFreq, bidirection))
					saveToFile("Status;RxID;Current RSSI;Packet RSSI;SNR;Timestamp(UTC);ErrorNo;\n")
				else:
					saveToFile("Transmitting packets with LoRa signal parameters bw: {}, sf: {}, crc on: {}, cr: {}, lowFrequency: {}, bidirectional: {}.\n".format(
								_bandwidthArr[0], _spreadingFactorArr[0], _crcOnArr[0], _crcValueArr[0], lowFreq, bidirection))
					saveToFile("Status;RxID;Timestamp(UTC);ERR;\n")
			
			# If error occured in LoRa C program
			elif "ERROR" in ln:
				uploadData = True
				
				if _receiver[0]:
					saveToFile("ERROR:-1;;;;;;{};\n".format(ln.strip()))
					recievedDataJsonObj = '{{"status":"ERR","description":"{}","time":{}}}'.format(ln.strip(),time())
				else:
					saveToFile("ERROR:-1;;{};\n".format(ln.strip()))
					recievedDataJsonObj = '{{"status":"ERR","description":"{}","time":{}}}'.format(ln.strip(),time())
			
			# If CRC error occured in LoRa C program (wrong packet CRC)	
			elif "CRCERR" in ln:
				saveToFile(ln + "\n")
				uploadData = True
				
				line = ln.split(":")				
				spltLn = line[1].split(";")
				recievedDataJsonObj = '{{"status":"CRCERR","cRSSI":{},"pRSSI":{},"SNR":{},"time":{},"crcErrNo":{}}}'.format(
											spltLn[0], spltLn[1], spltLn[2], spltLn[3], spltLn[4])
											
			# Modem statuses
			elif "rxOnGoing" in ln or "signalDetected" in ln or "headerInfoValid" in ln:
				saveToFile(ln + "\n")
				uploadData = True
				
				line = ln.split(":")				
				spltLn = line[1].split(";") # to get rid of last ";"
								
				recievedDataJsonObj = '{{"status":"{}","time":{}}}'.format(line[0], spltLn[0])
			
			# Packet transmitted or received
			elif "OK" in ln:
				saveToFile(ln + "\n")
				uploadData = True
				
				spltLn = ln.split(":")[1].split(";")
				if _receiver[0] and not _bidirect[0] or len(spltLn) > 3 and _bidirect[0]:					
					recievedDataJsonObj = '{{"status":"OK","rxId":{},"cRSSI":{},"pRSSI":{},"SNR":{},"time":{}}}'.format(
												spltLn[0], spltLn[1], spltLn[2], spltLn[3], spltLn[4])
				else:
					recievedDataJsonObj = '{{"status":"OK","rxId":{},"time":{}}}\n'.format(spltLn[0], spltLn[1])
					print("")			
			
			# Try to publish results if explicit write to file flag is not set
			if not _writeToFileArr[0]:
				
				if not recievedDataJsonObj == "":
					# Save to buffer
					_DATA_BUFFER[0].append(recievedDataJsonObj)
					if _debug[0]:
						printAndLog(ln)
						if _receiver[0] and "OK" in ln:
							print("") # Just to make console output more readable
				
				# Try to publish results if buffer is full
				if uploadData and len(_DATA_BUFFER[0]) == _BUFFER_SIZE[0]:				
					printAndLog("Publish data...")
										
					# Paho mqtts publish() method is buffering messages on its own 
					# if there is no connection to broker or if connection is lost.
					# All messages will be send when connection to broker is reestablished.
					publishData()
					
					# Delete buffers content
					resetBuffer()
			
			# If command to restart the transmittion has been send over MQTT,
			# stop current trasmiter or receiver
			if _killAndStartNew[0]:
				# Store it to paho mqtts buffer (publish data). This data will be sent automatically
				# when (if) client will connect to broker.
				publishData()
				
				# Terminate current LoRa C program
				killOldProgram()
				break
			
		# Start new LoRa C program with newly obtained parameters
		runLoRaProgram()


def formJSONReplay():
	'''
	Create json replay with received LoRa data
	'''
	recStr = "false"
	if _receiver[0]:
		recStr = "true"
	lowFreq = "false"
	if _lowFrequency[0]:
		lowFreq = "true"
	bi = "false"
	if _bidirect[0]:
		bi = "true"
	return '{{"devId":{},"location":{{"lat":{},"lon":{}, "locDesc":"{}"}},"settings":{{"bw":{},"sf":{},"crcOn":{},"cr":{},"lowFreq":{}}},"bidirectional":{},"rec":{},"data":[{}]}}'.format(
		_DEVICE_ID[0],_gpsLat[0],_gpsLon[0],_locDesc[0],_bandwidthArr[0],_spreadingFactorArr[0],str(_crcOnArr[0]).lower(),_crcValueArr[0],lowFreq,bi,
		recStr,readBufferResults(_DATA_BUFFER[0]))


def publishData():
	'''
	Publish data
	'''
	if len(_DATA_BUFFER[0]) > 0:
		# Create JSON message
		publishJson = formJSONReplay()
		# Publish JSON message
		publish_resoult = _client.publish(_topicPub[0], publishJson, 1, True)
	
		if publish_resoult[0] == mqtt.MQTT_ERR_SUCCESS:
			printAndLog("...Success")
		else:
			printAndLog("...Failure")
			

def resetBuffer():
	'''
	Reset buffer to initial state
	'''
	_DATA_BUFFER[0] = []


def readBufferResults(bufferToRead):
	'''
	Get content of the buffer
	'''
	bufferLines = ""
	for val in bufferToRead:
		bufferLines += val + ","
	return bufferLines.rstrip(",") #remove last comma


def saveToFile(resToWrte):
	'''
	Save data to file
	'''
	try:
		with open('/home/pi/projects/LoRa/tests/measurements_' + _fileSuffix[0] + '.csv', 'a') as resFile:
			resFile.write(resToWrte)
	except OSError as e:
		printAndLog("ERROR: cant write results to file. Error no = " + str(e.errno))


def readDeviceSettings():
	'''
	Reads device settings from file
	'''
	try:
		fileData = ""
		with open('/home/pi/projects/device_settings.json', 'r') as f:
			# Read entire file
			for l in f:
				fileData += l
				
		if fileData:
			try:
				# Parse data to JSON format
				devSettJson = json.loads(fileData)
				
				_DEVICE_ID[0] = devSettJson["id"] # This device unique id
				# paho-MQTT settings
				_username[0] = devSettJson["username"]
				_passwd[0] = devSettJson["passwd"]
				_ip[0] = devSettJson["ip"]
				printAndLog("Broaker ip: " + _ip[0])
				_port[0] = devSettJson["port"]
				_keepAlive[0] = devSettJson["keepAlive"]
			except Exception as e:
				printAndLog("ERROR parsing json from device_settings.json with error code " + str(e.errno) + ": " + str(e))
			
		printAndLog("\n--------------------")
		printAndLog("Device Id = " + str(_DEVICE_ID[0]))
		printAndLog("--------------------\n")
	except OSError as e:
		printAndLog("ERROR: cant open or read device_settings.json file. Error no = " + str(e.errno))
		

def setFileName():
	'''
	Set unique filename
	'''
	if _fileSuffix[0] == "":
		rec = "t_"
		if _bidirect[0]:
			rec = "b_"
		elif _receiver[0]:
			rec = "r_"
		_fileSuffix[0] = rec + datetime.datetime.now().strftime("%d_%m_%Y") + "_" + str(int(time()))
			
				
def printAndLog(msg):
	'''
	Print messages on screen and log them to file
	'''
	print(msg)
	try:
		# Get absolute path to this scripts
		script_dir = os.path.dirname(os.path.abspath('__file__'))
		if script_dir == "" or script_dir == "/" or script_dir == None:
			script_dir = "/home/pi/projects/LoRa/Python"
		with open(script_dir + '/main.log', 'a') as resFile:
			# Write message to log file with current timestamp
			resFile.write("[" + datetime.datetime.now().strftime("%d.%m.%Y:%H:%M:%S") + "]: " + msg.strip() + "\n")
	except OSError as e:
		print("ERROR: cant write to log file. Error no = " + str(e.errno))


def readCommandLineArgs():
	'''
	Read command line arguments
	'''
	cmdArgs = sys.argv
	
	for i in range(1, len(cmdArgs)):
		split = cmdArgs[i].split("=")
		
		command = split[0]
		if len(split) == 2:
			val = split[1]
		
		if command == "-r":
			_receiver[0] = True
			
		elif command == "-f":
			_writeToFileArr[0] = True
			_startLoRaProgram[0] = True
			
		elif command == "-lf":
			_lowFrequency[0] = True
			
		elif command == "-bi":
			_bidirect[0] = True
			
		elif command == "-d":
			if val == "":
				printAndLog("ERROR6: Invalid value of -d argument! Please use -h for help.\n")
				sys.exit(0)
			else:
				_timeBetweenPackets[0] = val
			
		elif command == "-b":
			if val == "" or int(val) < 0 or int(val) > 9:
				printAndLog("ERROR2: Invalid value of -b argument! Please use -h for help.\n")
				sys.exit(0)
			else:
				_bandwidthArr[0] = val
				
		elif command == "-s":
			if val == "" or int(val) < 6 or int(val) > 12:
				printAndLog("ERROR3: Invalid value of -s argument! Please use -h for help.\n")
				sys.exit(0)
			else:
				_spreadingFactorArr[0] = val
				
		elif command == "-e":
			if val == "" or int(val) < 1 or int(val) > 4:
				printAndLog("ERROR4: Invalid value of -e argument! Please use -h for help.\n")
				sys.exit(0)
			else:
				_crcValueArr[0] = val
				
		elif command == "-c":
			if val == "" or int(val) < 0 or int(val) > 1:
				printAndLog("ERROR5: Invalid value of -c argument! Please use -h for help.\n")
				sys.exit(0)
			elif int(val) == 0:
				_crcOnArr[0] = False
			else:
				_crcOnArr[0] = True
		
		elif command == "-start":		
			_startLoRaProgram[0] = True
				
		elif command == "-h" or command == "--help":
			print("-h or --help \t show help")
			print("-start \t\t manually start transciever and don't wait for start command from server \n")
			print("-r \t\t if this flag is set receiver is activated")
			print("-f \t\t save measurements to local file instead of forwording them to server")
			print("-d \t\t delay in milliseconds between airtime of two packets. Default value is 1000 ms.")
			print("-b \t\t set bandwith value [0: 7.8kHz, 1: 10.4 kHz, 2: 15.6 kHz, 3: 20.8 kHz, 4: 31.2 kHz, 5: 41.6 kHz, 6: 62.5 kHz, 7: 125 kHz, 8: 250 kHz, 9: 500 kHz]")
			print("-s \t\t set spreading factor value [6: 64, 7: 128, 8: 256, 9: 512, 10: 1024, 11: 2048, 12: 4096] chips")
			print("-e \t\t set error coding (crc) value [1: 4/5, 2: 4/6, 3: 4/7, 4: 4/8]")
			print("-E \t\t if this flag is set, transceiver will operate in explicit header mode.");
			print("-c \t\t set 1 to turn crc on or 0 to turn off")
			print("-lf \t\t if this flag is set, transciecer operates on 434 MHz")
			print("-bi \t\t if this flag is set, transciever alternates between transmitter and receiver")
			# Terminate script
			sys.exit(0)


def main():
	# Catch SIGINT interrupt signal
	signal.signal(signal.SIGINT, signalHandler)
	
	# Set inital buffer size for transmitter
	if not _receiver[0] and not _bidirect[0]:
		# Initial buffer size for transmitter is 1/4 of size of receivers, 
		# because transmitter has 3/4 less log messages for each transmitted 
		# packet than it does receiver (it doesn't have modem statuses).
		_INIT_BUFFER_SIZE[0] = _INIT_BUFFER_SIZE[0]/4
		_BUFFER_SIZE[0] = _BUFFER_SIZE[0]/4
	
	# Read device settings from JSON file
	readDeviceSettings()
	# Read program settings from command line
	readCommandLineArgs()
	
	if __name__ == "__main__":
			# MQTT client thread
			threadMQTT = Thread(target = runMQTTclient, args = (_topicSub[0],_username[0], _passwd[0], _ip[0], _port[0], _keepAlive[0]))
			threadMQTT.start()
			# LoRa parser thread
			threadLoRa = Thread(target = runLoRaProgram, args = ( ))
			threadLoRa.start()

			threadMQTT.join()
			threadLoRa.join()


main()
