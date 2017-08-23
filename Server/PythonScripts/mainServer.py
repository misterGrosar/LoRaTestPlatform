'''
----------------------------------------------------------
 This is server side python script for saving received MQTT
 messages form devices to database.
----------------------------------------------------------
'''
import signal
import sys
import os
import paho.mqtt.client as mqtt
import json
import pymysql
import datetime
import smtplib
from email.mime.text import MIMEText

# Settings file
_settingsLocation = ['/serverSettingsLocal.json']

# paho-MQTT settings (this settings are overwritten with ones from file)
_topicPub = ["lora/testPub"] 	# MQTTs topic name
_username = [""] 		# MQTTs username
_passwd = [""] 	# MQTTs password
_ip = [""] 		# Server IP where MQTT is installed
_port = [8883] 					# Server port where MQTT listens
_keepAlive = [60] 				# Time (in seconds) of inactivity before ping is sent to MQTT server

# Database settings (this settings are overwritten with ones from file)
_dbUsername = [""] 	# Database username
_dbPasswd = [""] 	# Database password
_dbIp = ["localhost"] 	# Database IP
_dbTable = ["lora"] 	# Database table

# Email settings for notifications about errors
_emailAddress = ''
_emailUsername = ''
_emailPassword = ''

_exceptionSent = [False] # Indicates if email notification has already been sent (to send it only once)

_client = mqtt.Client(client_id="mainPythonServer") # MQTT client
_dbConnection = [None] 								# Database connection
_script_dir = [""] 									# This scripts absolute path

#Current LoRa settings
_LoRaSettingsDictionary = {}
_LoRaSensorIdsDict = {}


def signalHandler(signal, frame):
	'''
	This method handles proper termination of the program when SIGINT is caught
	'''

	printAndLog("\nCtrl+C pressed. Exiting program.\n")                
	_client.disconnect()
	sys.exit(0)


def on_connect(client, userdata, rc):
	'''
	Method subscribes to topic when MQTT client is connected with MQTT broker
	'''

	printAndLog ("Connected with rc: " + str(rc))
	_client.subscribe(_topicPub[0])


def on_message(client, userdata, msg):
	'''
	Save message 'msg' obtained from device to database. One message can come from only one device at once.
	:param msg: message received over MQTT
	'''

	# Decode MQTT message to UTF-8
	msgPayloadStr = str(msg.payload.decode("utf-8"))
	print ("\nMessage: " + msgPayloadStr + "\n")

	# Connect to the database
	_dbConnection[0] = pymysql.connect(host=_dbIp[0],
					user=_dbUsername[0],
					password=_dbPasswd[0],
					db=_dbTable[0],
					charset='utf8',
					cursorclass=pymysql.cursors.DictCursor)
	deviceId = -1 # Current id of device form which this data originates from
	try:
		# Parse message into JSON data
		messJson = json.loads(msgPayloadStr)

		deviceId = messJson["devId"]

		locationInfo = None # Current device location
		if "location" in messJson:
			locationInfo = messJson["location"]

		currentSettings = messJson["settings"] # Device settings
		dataArr = messJson["data"] # Packets and messages obtained on device

		# Check if device used bidirectional communication
		bidirectional = False
		if "bidirectional" in messJson:
			bidirectional = messJson["bidirectional"]
		# Check if message is from receiver or transmitter
		receiver = False
		if "rec" in messJson:
			receiver = messJson["rec"]

		gpsLon = None # Device GPS longitude
		if "lon" in locationInfo:
			gpsLon = locationInfo["lon"]
		gpsLat = None # Device GPS latitude
		if "lat" in locationInfo:
			gpsLat = locationInfo["lat"]
		locDesc = "" # Additional user description of devices location
		if "locDesc" in locationInfo:
			locDesc = locationInfo["locDesc"]
		startTime = None # Time when measurements were started
		if "time" in dataArr[0]:
			startTime = dataArr[0]["time"]
		freqency = 1 # 1 is for high (868 MHz) frequency, 2 is for low (434 MHz) frequency
		if currentSettings["lowFreq"]:
			freqency = 2
		

		# If settings have changed or they are not jet saved
		if not deviceId in _LoRaSettingsDictionary or settingsChanged(currentSettings, deviceId):
			printAndLog("\nSettings have changed...")
		
			querySelect = """SELECT id FROM `settings` WHERE frequency="%s" AND bandwidth="%s" AND spreading_factor="%s" AND code_rate="%s" AND coding_rate_on="%s" ORDER BY id DESC LIMIT 1"""
			values = (freqency, currentSettings["bw"], currentSettings["sf"], currentSettings["cr"], currentSettings["crcOn"])
		
			# Check if entry for this set of settings already exists in db
			settingsId = getOneFromDb(querySelect, values)

			# If settings are already saved in database
			if settingsId is not None:
				settingsId = settingsId["id"]
				printAndLog("\nSettings exists in database, id = " + str(settingsId))
				
				querySelect = """SELECT * FROM sensor WHERE device_id=%s AND longitude=%s AND latitude=%s AND settings=%s AND receiver=%s ORDER BY id DESC"""
				values = (deviceId, gpsLon, gpsLat, settingsId, receiver)

				# Get previously saved device id
				sensorId = getOneFromDb(querySelect, values)
				
				if sensorId is not None:
					printAndLog("\tSensor id from database, id = " + str(sensorId["id"]) + "\n")
					_LoRaSensorIdsDict[deviceId] = sensorId["id"] # Save it for later use
				else:
					printAndLog("\tSensor DOES NOT exists in database.\n")
			# If there is no entry in database for this set of settings, save it to database
			else:
				printAndLog("\nSettings DOES NOT exists in database.\n")
				
				query = """INSERT INTO `settings` (`id`, `frequency`, `bandwidth`, `spreading_factor`, `code_rate`, `coding_rate_on`) VALUES (NULL, %s, %s, %s, %s, %s);"""
				settingsId = saveToDb(query, values)
				
				if settingsId != -1:
					printAndLog("\tSettings saved to database.\n")
				
			# Save settings for current device to dictionary for later use
			_LoRaSettingsDictionary[deviceId] = currentSettings

			# Save device id in database
			if settingsId != -1 and deviceId not in _LoRaSensorIdsDict:
				query = """INSERT INTO `sensor` (`id`, `device_id`, `longitude`, `latitude`, `location_description`, `settings`, `receiver`, `measurements_started_at`) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s);"""
				values = (deviceId, gpsLon, gpsLat, locDesc, settingsId, receiver, startTime)

				sensorId = saveToDb(query, values)
				
				if sensorId != -1:
					printAndLog("\tSensor inserted into database, id = " + str(sensorId) + ".")
					_LoRaSensorIdsDict[deviceId] = sensorId
				else:
					printAndLog("\tSensor IS NOT INSERTED into database.")

		# Parse message data
		for data in dataArr:
			status = 1 #OK
			if data["status"] == "CRCERR":
				status = 2
			elif data["status"] == "ERR":
				status = 3
			elif data["status"] == "rxOnGoing":
				status = 4
			elif data["status"] == "signalDetected":
				status = 5
			elif data["status"] == "headerInfoValid":
				status = 6

			if "location" in data:
				gpsLon = data["location"]["lon"]
				gpsLat = data["location"]["lat"]
				locDesc = data["location"]["locDesc"]

			# In bidirectional mode, mixed data is in the same message because device alternates between transmitter and receiver
			if bidirectional and status == 1 and ("pRSSI" not in data or "SNR" not in data):
				receiver = False
			else:
				receiver = True

			# Parse receiver data
			if receiver:
				if status == 1 or status == 2 or status == 4 or status == 5 or status == 6:
					if status == 2:
						printAndLog("!!!!!!!!!!CRC ERROR!!!!!!!!!!")

					rxId = None # Packet sequential number
					if "rxId" in data:
						rxId = data["rxId"]
					crcErrNo = None # CRC sequential error number
					if "crcErrNo" in data:
						crcErrNo = data["crcErrNo"]
					
					additionalData = None # Possible additional data
					if "additionalData" in data:
						additionalData = data["additionalData"]
					
					cRSSI = None # Current RSSI value
					if "cRSSI" in data:
						cRSSI = data["cRSSI"]

					pRSSI = None # Measured packets RSSI value
					if "pRSSI" in data:
						pRSSI = data["pRSSI"]

					SNR = None # Measured packets SNR value
					if "SNR" in data:
						SNR = data["SNR"]

					time = None # Time when packet was received
					if "time" in data:
						time = data["time"]

					query = ""
					insertNewValue = False
					# For packets with status OK and CRC error
					if status == 1 or status == 2:
						if status == 1: # packet OK
							querySelect = """SELECT * FROM measurements WHERE sensor_id=%s AND rx_id=%s AND current_rssi=%s AND packer_rssi=%s AND snr=%s AND timestamp=%s AND crc_err_no IS NULL AND status=%s ORDER BY id DESC;"""
							values = (_LoRaSensorIdsDict[deviceId], rxId, cRSSI, pRSSI, SNR, str(time), status)
						else: # CRC error
							querySelect = """SELECT * FROM measurements WHERE sensor_id=%s AND rx_id IS NULL AND current_rssi=%s AND packer_rssi=%s AND snr=%s AND timestamp=%s AND crc_err_no=%s AND status=%s ORDER BY id DESC;"""
							values = (_LoRaSensorIdsDict[deviceId], cRSSI, pRSSI, SNR, str(time), crcErrNo, status)
						
						# Check if entry for this set of data already exists in db
						rowId = getOneFromDb(querySelect, values)
						# If not prepare query statement
						if rowId is None:
							additional = "This sensor was on location: " + locDesc
							query = """INSERT INTO `measurements` (`id`, `sensor_id`, `rx_id`, `current_rssi`, `packer_rssi`, `snr`, `timestamp`, `crc_err_no`,`packet_gsp_longitude`,	`packet_gsp_latitude`, `additional_sensor_data`, `status`)
										VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
							values = (_LoRaSensorIdsDict[deviceId], rxId, cRSSI, pRSSI, SNR, str(time), crcErrNo, gpsLon, gpsLat, additional, status)
							insertNewValue = True

					# For rxOnGoing = 4, signalDetected = 5 and headerInfoValid = 7
					elif status == 4 or status == 5 or status == 6:
						querySelect = """SELECT * FROM measurements WHERE sensor_id=%s AND rx_id IS NULL AND timestamp=%s AND status=%s ORDER BY id DESC"""
						values = (_LoRaSensorIdsDict[deviceId], str(time), status)
						
						# Check if entry for this set of data already exists in db
						rowId = getOneFromDb(querySelect, values)
						# If not prepare query statement
						if rowId is None:
							additional = "This sensor was on location: " + locDesc
							query = """INSERT INTO `measurements` (`id`, `sensor_id`, `timestamp`, `additional_sensor_data`, `status`)
										VALUES (NULL, %s, %s, %s, %s);"""
							values = (_LoRaSensorIdsDict[deviceId], str(time), additional, status)
							insertNewValue = True
					# Save measurement to database
					if insertNewValue:
						mId = saveToDb(query, values)

						if mId == -1:
							printAndLog("ERROR SAVING message from RECEIVER to db.")
					else:
						printAndLog("Measurement entry already in database. RxId: " + str(rxId) + ", timestamp: " + str(time) + ", status: " + str(status))

				elif status == 3:
					printAndLog(data["description"])
			
			# Parse transmitter data
			else:
				if status == 1:
					rxId = None # Packet sequential number
					if "rxId" in data:
						rxId = data["rxId"]
					time = None # Time when packet was transmitted
					if "time" in data:
						time = data["time"]
					
					additionalData = None # Possible additional data
					if "additionalData" in data:
						additionalData = data["additionalData"]
	
					querySelect = """SELECT * FROM measurements WHERE sensor_id=%s AND rx_id=%s AND current_rssi IS NULL AND packer_rssi IS NULL AND snr IS NULL AND timestamp=%s AND crc_err_no IS NULL AND status=%s ORDER BY id DESC;"""
					values = (_LoRaSensorIdsDict[deviceId], rxId, str(time), status)

					# Check if entry for this set of data already exists in db
					rowId = getOneFromDb(querySelect, values)
					# If not save it to database
					if rowId is None:
						additional = "This sensor was on location: " + locDesc
						query = """INSERT INTO `measurements` (`id`, `sensor_id`, `rx_id`, `current_rssi`, `packer_rssi`, `snr`, `timestamp`, `crc_err_no`,`packet_gsp_longitude`,	`packet_gsp_latitude`, `additional_sensor_data`, `status`)
						VALUES (NULL, %s, %s, NULL, NULL, NULL, %s, NULL, %s, %s, %s, %s);"""

						values = (_LoRaSensorIdsDict[deviceId], rxId, str(time), gpsLon, gpsLat, additional, status)

						mId = saveToDb(query, values)

						if mId == -1:
							printAndLog("ERROR SAVING message from TRANSMITTER to db.")
					else:
						printAndLog("Transmitter data already in database. RxId: " + str(rxId) + ", timestamp: " + str(time))

				# Error messages from device
				elif status == 3:
					printAndLog(data["description"])
	except json.JSONDecodeError as e:
		print("\n!!!!!!!!!!!!Exception!!!!!!!!!!!!!")
		printAndLog("EXCEPTION occured while parsin JSON from " + msg.topic + ". Exception: " + e.msg + ", error position: " + e.pos + ", col: " + e.col + ", lineno: " + e.lineno)
		printAndLog ("Topic: "+ msg.topic+"\nMessage: " + msgPayloadStr)
		
		if not _exceptionSent[0]:
			# In case of exception send mail to warn user
			msgBody = 'There has been some error while parsing JSON data received form nodes.\n\n Error description: ' + str(e) + '.\n\nReceived JSON message: ' + msgPayloadStr
			
			sendemail(from_addr    = _emailAddress,
				to_addr_list = [_emailAddress],
				cc_addr_list = [], 
				subject      = 'Error parsing JSON data', 
				message      = msgBody,
				login        = _emailUsername,
				password     = _emailPassword)
		
			_exceptionSent[0] = True
	finally:
		_dbConnection[0].close()


def settingsChanged(settings, deviceId):
	'''
	Check if previously saved settings for device with 'deviceId' differs from
	current settings obtained from received JSON
	:param settings: previous settings
	:param deviceId: device id of device to check settings for
	'''

	if deviceId in _LoRaSettingsDictionary:
		prevSettJson = _LoRaSettingsDictionary[deviceId]
		return prevSettJson["bw"] != settings["bw"] and prevSettJson["sf"] != settings["sf"] and prevSettJson["crcOn"] != settings["crcOn"] and prevSettJson["cr"] != settings["cr"] and prevSettJson["lowFreq"] != settings["lowFreq"]
	return True


def saveToDb(query, values):
	'''
	Handle saving data to database
	:param query: query string
	:param values: values to save
	:return: row id
	'''

	try:
		cursor = _dbConnection[0].cursor()
		cursor.execute(query, values)

		# Connection is not autocommit by default.
		# You must commit to save your changes.
		_dbConnection[0].commit()
		return cursor.lastrowid
	except Exception as e:
		printAndLog("Database writing error: " + e)
	return -1


def getOneFromDb(query, values):
	'''
	Get one row from database
	:param query: query string
	:param values: query values
	:return: cursor with one row of data
	'''

	try:
		cursor = _dbConnection[0].cursor()
		cursor.execute(query, values)
		return cursor.fetchone()
	except Exception as e:
		printAndLog("Database writing error: " + e)
	return -1


def getMultipleFromDb(query, values):
	'''
	Get multiple rows from database
	:param query: query string
	:param values: query values
	:return: cursor with multiple rows from database
	'''

	try:
		cursor = _dbConnection[0].cursor()
		cursor.execute(query, values)
		return cursor.fetchall()
	except Exception as e:
		printAndLog("Database writing error: " + e)
	return -1


def printAndLog(msg):
	'''
	Print 'msg' on screen and also log it to file
	:param msg: message to print and log
	'''

	print(msg)
	try:
		with open(_script_dir[0] + '/main.log', 'a') as resFile:
			# Write message to log file with current timestamp
			resFile.write("[" + datetime.datetime.now().strftime("%d.%m.%Y:%H:%M:%S") + "]: " + msg.strip() + "\n")
	except OSError as e:
		print("ERROR: cant write to log file. Error no = " + e.errno)


def readDeviceSettings():
	'''
	Reads MQTT and database credentials from JSON file
	'''

	try:
		fileData = ""
		# Reads entire file
		with open(_script_dir[0] + _settingsLocation[0], 'r') as f:
			for l in f:
				fileData += l
				
		if fileData:
			try:
				# Parse JSON data obtained from file
				devSettJson = json.loads(fileData)

				# If MQTT settings are present, load them
				if "mosquitto" in devSettJson:
					mosqSett = devSettJson["mosquitto"]
					# MQTT settings
					_topicPub[0] = mosqSett["topicPub"]
					_username[0] = mosqSett["username"]
					_passwd[0] = mosqSett["passwd"]
					_ip[0] = mosqSett["ip"]
					printAndLog("Broaker ip: " + _ip[0])
					_port[0] = mosqSett["port"]
					_keepAlive[0] = mosqSett["keepAlive"]

				# If settings for database connection are present, load them
				if "db" in devSettJson:
					dbSett = devSettJson["db"]
					_dbUsername[0] = dbSett["username"]
					_dbPasswd[0] = dbSett["passwd"]
					_dbIp[0] = dbSett["ip"]
					_dbTable[0] = dbSett["table"]
			except Exception as e:
				printAndLog("ERROR parsing json from "+ _settingsLocation[0] + ": " + str(e))
	except OSError as e:
		printAndLog("ERROR: cant open or read " + _settingsLocation[0] + " file. Error no = " + str(e.errno))


def runMQTTclient(username, password, ip, port, keepAlive):
	'''
	Connect to MQTT broker and subscribe to topic
	:param username: MQTT username
	:param password: MQTT password
	:param ip: MQTT server IP address
	:param port: MQTT server port
	:param keepAlive: Client will send ping after keepAlive seconds, if no message has been received in that time
	'''

	# MQTT callback methods
	_client.on_connect = on_connect
	_client.on_message = on_message
	# Set credentials
	_client.username_pw_set(username, password)
	try:
		_client.connect(ip, port, keepAlive) # Connect to MQTT
		_client.subscribe(_topicPub[0], 0) # Subscribe to topic
	except IOError as e:
		if e.errno == 101 or e.errno == 113:
			printAndLog("\nNo connection to MQTT topic " + _topicPub[0] + ". No internet connection\n")
		else:
			raise

	_client.loop_forever(retry_first_connection=False) # Loops forever and waits for messages from broker


def sendemail(from_addr, to_addr_list, cc_addr_list,
              subject, message,
              login, password,
              smtpserver='smtp.gmail.com', smtpport=587):  # split smtpserver and -port
	'''
	Send email with warning
	'''
	header  = 'From: %s\n' % from_addr
	header += 'To: %s\n' % ','.join(to_addr_list)
	header += 'Cc: %s\n' % ','.join(cc_addr_list)
	header += 'Subject: %s\n\n' % subject
	message = header + message

	print("Sending email...")
	try:
		server = smtplib.SMTP(smtpserver, smtpport)  # use both smtpserver  and -port 
		server.starttls()
		server.login(login,password)
		problems = server.sendmail(from_addr, to_addr_list, message)
		server.quit()
	except:
		printAndLog("Error while sending email.")
	print("... email has been sent")


def main():
	# Catch SIGINT interrupt signals
	signal.signal(signal.SIGINT, signalHandler)
	# Get this scripts absolute path
	_script_dir[0] = os.path.dirname(os.path.abspath('__file__'))
	# Read MQTT and database settings from file
	readDeviceSettings()

	# Run MQTT client and message parser
	runMQTTclient(_username[0], _passwd[0], _ip[0], _port[0], _keepAlive[0])


main()
