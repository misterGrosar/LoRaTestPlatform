'''
----------------------------------------------------------
 This is server side python script for saving received GPS 
 position from mobile device. Received data has been sent via MQTT.
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
_settingsLocation = ['/serverSettings.json']

# paho-MQTT settings (this settings are overwritten with ones from file)
_topicGPSLog = ["lora/testGPSLog"] 	# MQTTs topic name
_username = [""] 				# MQTTs username
_passwd = [""] 					# MQTTs password
_ip = [""] 			# Server IP where MQTT is installed
_port = [8883] 						# Server port where MQTT listens
_keepAlive = [60]				 	# Time (in seconds) of inactivity before ping is sent to MQTT server

# Database settings (this settings are overwritten with ones from file)
_dbUsername = [""] 	# Database username
_dbPasswd = [""] 	# Database password
_dbIp = ["localhost"] 	# Database IP
_dbTable = ["lora"] 	# Database table

_exceptionSent = [False] # Indicates if email notification has already been sent (to send it only once)

_client = mqtt.Client(client_id="logGPSServer") # MQTT client
_dbConnection = [None] 							# Database connection
_script_dir = [""] 								# This scripts absolute path

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
	_client.subscribe(_topicGPSLog[0])


def on_message(client, userdata, msg):
	'''
	Save message 'msg' obtained from device to database. One message can come from only one device at once.
	:param msg: message received over MQTT
	'''

	# Decode MQTT message to UTF-8
	msgPayloadStr = str(msg.payload.decode("utf-8"))
	print ("Topic: "+ msg.topic+"\nMessage: " + msgPayloadStr)

	# Connect to the database
	_dbConnection[0] = pymysql.connect(host=_dbIp[0],
					user=_dbUsername[0],
					password=_dbPasswd[0],
					db=_dbTable[0],
					charset='utf8',
					cursorclass=pymysql.cursors.DictCursor)
	try:
		# Parse message into JSON data
		messJson = json.loads(msgPayloadStr)

		lon = None # Device GPS longitude
		if "lon" in messJson:
			lon = messJson["lon"]
		lat = None # Device GPS latitude
		if "lat" in messJson:
			lat = messJson["lat"]
		time = None # Time when location was measured
		if "time" in messJson:
			time = messJson["time"]

		# Insert time and location of mobile device
		if lon is not None and lat is not None and time is not None:
			values = (lon, lat, time)
			querry = """INSERT INTO `travel_location` (`id`, `lon`, `lat`, `timestamp`) VALUES (NULL, %s, %s, %s);"""
		
			mId = saveToDb(querry, values)

			if mId == -1:
				printAndLog("ERROR SAVING location info to db.")

	except Exception as e:
		print("\n!!!!!!!!!!!!Exception!!!!!!!!!!!!!")
		printAndLog("EXCEPTION occurred while parsing JSON from " + msg.topic + ". Exception: " + str(e))
		printAndLog ("Topic: "+ msg.topic+"\nMessage: " + msgPayloadStr)
		
		if not _exceptionSent[0]:
			# In case of exception send mail to warn user
			msgBody = 'There has been some error while parsing JSON GPS data received form MOBILE DEVICE.\n\n Error description: ' + str(e) + '.\n\nReceived JSON message: ' + msgPayloadStr
			
			sendemail(from_addr    = '', 
				to_addr_list = [''],
				cc_addr_list = [], 
				subject      = 'MOBILE DEVICE: Error parsing JSON GPS data', 
				message      = msgBody,
				login        = '', 
				password     = '')
		
			_exceptionSent[0] = True
	finally:
		_dbConnection[0].close()
	

def saveToDb(querry, values):
	'''
	Handle saving data to database
	:param query: query string
	:param values: values to save
	:return: row id
	'''

	try:
		cursor = _dbConnection[0].cursor()
		cursor.execute(querry, values)

		# Connection is not autocommit by default.
		# You must commit to save your changes.
		_dbConnection[0].commit()
		return cursor.lastrowid
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
					_topicGPSLog[0] = mosqSett["topicGPSLog"]
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
		_client.subscribe(_topicGPSLog[0], 0) # Subscribe to topic
	except IOError as e:
		if e.errno == 101 or e.errno == 113:
			printAndLog("\nNo connection to MQTT topic " + _topicGPSLog[0] + ". No internet connection\n")
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
