- LoRaSettings.json file is for controlling ALL devices connected to this research platform.
It can be multicasted to all devices using following MQTT command:
	& mosquitto_pub -h <broker_ip> -p 8883 -t "lora/test" -u <username> -P <password> -d -f <path_to_json_file>/LoRaSettings.json
	
This JSON file structure is described here:
{
"devices": [{
	"id":1, // device id
	"rec": true, // if true, device is receiver,
		// otherwise transmitter 
	"bidirectional": false, //if set to true, 
		// device alternates between 
		// receiver and transmitter
	"setId": 1, // settingId (from JSON array 
		// "parameters") to use with this device
	"start": true, // start measurements
	"restartT": true, // restart LoRaC subprocess
	"debug":true, 
	"gpsLat":46.050343, // device GPS latitude
	"gpsLon": 14.469144, // device GPS longitude
	"locDesc":"Test location" // device descriptions
}],
"buffer":{"buffSize": 32}, // number of LoRaC output lines
			// buffered before they are send to
			// MQTT broker
"parameters": [{	
	"settingId": 1, // setting id
	"bw": "8", // bandwidth
	"sf": "6", // spreading factor
	"crcOn": true, // is CRC on 
	"crcVal": "2", // coding rate value
	"delay": "3000", // delay between packets airtime
	"lowFreq": false // if true, transceiver operates 
			// on 434 MHz, otherwise on 868 MHz
}]
}

- rebootDevices.json is for remote device(s) reboot. You can send is using command:
	& mosquitto_sub -h <broker_ip> -p 8883 -v -t "lora/testReboot" -u <username> -P <password> -d -f <path_to_json_file>/rebootDevices.json