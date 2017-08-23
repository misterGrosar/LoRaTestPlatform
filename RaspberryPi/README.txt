!!!! IMPORTANT !!!!
This folder structure should remanin as it is.
If you change it, you have to correct paths in some files.
!!!!!!!!!!!!!!!!!!!

******* Installation instructions *******
1. Copy ALL files in this folder to folder on your Raspberry Pi 3
(Path to folder on my Raspberry Pi 3 was /home/pi/projects/).

2. Go to folder LoRa/src/ and compile C program files:
	& ./compile
	
3. Install paho-mqtt Python library on your Raspberry Pi:
	& pip install paho-mqtt==1.2.3
	
If using newer version of paho-mqtt, the Python scripts have to be changed,
because paho-mqtt library versions greater than 1.2.3 
are not compatible with this version.

4. Fill MQTT and database credentials and settings.

5. Run main.py script in folder LoRa/Python:
	& sudo python3 main.py
	
If everything is O.K., program should print your broker IP address, device number 
and line saying "Connected with rc: 0". If you set device to transmitter, transmitted
packet numbers will apear.



******* Some important notes *******
- In folder LoRa/tests/ are saved all measurement backups.

- If you want, you can also run deviceReboot.py script which listens to commands
sent over MQTT for remote device reboot. Command to send reboot command is:
	& mosquitto_sub -h <broker_ip> -p 8883 -v -t "lora/testReboot" -u <username> -P <password> -d -f <path_to_json_file>/rebootDevices.json

Example of rebootDevices.json file is in "Command center" directory.

- You must set unique device id in device settings JSON file (parameter "id").
This id is used for executing correct instructions and settings when they are 
received via MQTT. Instructions can be sent using following comand:
	& mosquitto_pub -h <broker_ip> -p 8883 -t "lora/test" -u <username> -P <password> -d -f <path_to_json_file>/LoRaSettings.json
	
Example of LoRaSettings.json file is in "Command center" directory.