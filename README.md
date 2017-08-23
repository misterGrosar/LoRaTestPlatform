This programs and scripts are used for creating flexible and scalable "LoRa test platform".
This platform was build as a part of master's thesis titled
"Coverage and penetration measurements for Low Power Wide Area Network signals" 
and is released under GNU General Public Licence v3.0.

One can run all kind of LoRa measurements with this platform, which allows control over 
all devices during measurements from a single place. Instuctions how to execute commands 
using single terminal command can be found in folder "Command center", 
while instuctions for installing programs on each platform can be found in each folder.

This scripts and programs are currently configured to use Raspberry Pi 3 Model B (it probably
works with other models too, but it is not tested) and Semtechs SX1276 LoRa chips.
We used custom board containing this chip, if you want to use your chip, you will probably
have to configure DIO pin settings in file RaspberryPi/LoRa/src/sx1276-Hal.c.

Instead of Raspberry GPS module, we used Android phone for logging GPS position of
moving device. This GPS logging app can be found in Android/LogGPSPosition directory, 
while app in Android/TimeLog folder is intended for indoor use instead of LogGPSPosition app.

---- Known bug ----
When using bi-directional LoRa communication with time between packets less than 3000 ms,
synchronization between devices is lost. If time between packets is greater than 3000 ms,
everything works fine.