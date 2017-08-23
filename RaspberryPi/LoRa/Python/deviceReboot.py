'''
This script reboots device. It listens for command sent over MQTTs topic
'''
import os
import signal
import paho.mqtt.client as mqtt
import json
from time import sleep
import sys

_DEVICE_ID = [-1] 		# Unique device id
_client = mqtt.Client()	# MQTT client

'''
This settings ARE OVERWRITTEN IN readDeviceSettings() method!!!
'''
# paho-MQTT settings
_topicSub = ["lora/reboot"]	# MQTTs topic
_username = [""]		# MQTTs username
_passwd = [""]			# MQTTs password
_ip = [""]		# MQTTs broker ip
_port = [8883]				# MQTTs port
_keepAlive = [60]			# Time (in seconds) of inactivity, before ping is sent to MQTT server 


def signalHandler(signal, frame):
	'''
	Handle SIGINT signal. Kill LoRa thread, sent unpublished data, 
	disconnect MQTT client and terminate the script.
	'''
	
	print("\nCtrl+C pressed. Exiting program.\n")
	_client.disconnect()
	sys.exit(0)
	

def on_connect(client, userdata, rc):
	'''
	Method subscribes to the topic, when MQTT client is connected with MQTT broker
	'''
	print("Connected with rc: " + str(rc))
	_client.subscribe(_topicSub[0], 0)


def on_message(client, userdata, msg):
	'''
	Method handles received message and reboots device
	'''
	reboot = False

	# Decode MQTT message to UTF-8
	msgPayloadStr = str(msg.payload.decode("utf-8"))
	print("Topic: "+ msg.topic+"\nMessage: " + msgPayloadStr)

	try:
		# Parse message into JSON format
		loraSettingsJson = json.loads(msgPayloadStr)

		# Device settings
		for dev in loraSettingsJson["devices"]:
			if dev["id"] == _DEVICE_ID[0]:
				reboot = dev["reboot"]
				break

		# Reboot device if message contained reboot command for this device
		if reboot:
			print("reboot")
			os.system("sudo reboot") 
			
	except Exception as e:
		print("ERROR parsing json: " + str(e))
		

def runMQTTclient(username, password, ip, port, keepAlive):
	'''
	Connect to MQTT broker and subscribe to topic
	'''
	
	# Cakkback methods
	_client.on_connect = on_connect
	_client.on_message = on_message

	# Set MQTT credentials
	_client.username_pw_set(username, password)
	
	try:
		_client.connect(ip, port, keepAlive) # Connect to broaker
		_client.subscribe(_topicSub[0], 0) # Subscribe to topic
	except IOError as e:
		if (e.errno == 101 or e.errno == 113):
			print("No connection to MQTT topic {}.\nNo internet connection.\n".format(_topicSub[0]))
			handleErr(username, password, ip, port, keepAlive)
			
		elif e.errno == 110:
			print("MQTT Connection timed out. Trying to reconect...")
			handleErr(username, password, ip, port, keepAlive)
		else:
			print("NOT HANDLED ERROR: " + str(e))              

	_client.loop_forever() # Loops forever and waits for messages from broker
	

def handleErr(username, password, ip, port, keepAlive):
	'''
	Handle MQTT errors
	'''
	
	# Try to reconnect
	sleep(10)
	runMQTTclient(username, password, ip, port, keepAlive)
	
	
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
			# Parse data to JSON format
			devSettJson = json.loads(fileData)
			
			_DEVICE_ID[0] = devSettJson["id"] # This device unique id
			# paho-MQTT settings
			_username[0] = devSettJson["username"]
			_passwd[0] = devSettJson["passwd"]			
			_ip[0] = devSettJson["ip"]
			print("Broker ip: " + _ip[0])
			_port[0] = devSettJson["port"]
			_keepAlive[0] = devSettJson["keepAlive"]
			
		print("\n--------------------")
		print("Device Id = " + str(_DEVICE_ID[0]))
		print("--------------------\n")
	except OSError as e:
		print("ERROR: cant open or read device_settings.json file. Error no = " + e.errno)
		
		
def main():
	# Catch SIGINT interrupt signal
	signal.signal(signal.SIGINT, signalHandler)
	# Read device settings from JSON file
	readDeviceSettings()
	# Runs MQTT client and waits for messages
	runMQTTclient(_username[0], _passwd[0], _ip[0], _port[0], _keepAlive[0])
	
	
main()
