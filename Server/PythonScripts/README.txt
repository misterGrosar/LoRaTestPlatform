1. Copy scripts in this file to the server.

2. Change paho-mqtt and database connection 
setting in each server script to the ones you use.

2.For runnng Python scripts you will need to install
the following programs on your server:

------------------------------------------------------
MySQL:
------------------------------------------------------
Install MySQL:
	& sudo apt-get update
	& sudo apt-get install mysql-server

Configure MySQL:
	& sudo mysql_secure_installation
	
Test MySQL:
	& systemctl status mysql.service
	
Start MySQL:
	& sudo systemctl mysql start
	
------------------------------------------------------
phpMyAdmin:
------------------------------------------------------
Install:
	& apt-get install phpmyadmin php-mbstring php-gettext

Explicitly enable the PHP mcrypt and mbstring extensions:
	& sudo phpenmod mcrypt
	& sudo phpenmod mbstring
	
Restart Apache:
	& systemctl restart apache2
	
------------------------------------------------------
PYMySQL:
------------------------------------------------------
Download python whl file from https://pypi.python.org/pypi/PyMySQL#downloads
and install it:
	& pip3 install path/to/PyMySQL.whl
	
Or run:
	& sudo apt-get install python3-pymysql

------------------------------------------------------
paho-mqtt Python library:
------------------------------------------------------
Install:
	& pip install paho-mqtt==1.2.3
	
If using newer version of paho-mqtt, the Python scripts have to be changed,
because paho-mqtt library versions greater than 1.2.3 
are not compatible with this version.


3. You can run this scripts as normal Python scripts (with sudo privilegues):
	& sudo python3 <script_name.py>
	
!!!NOTE: you will have to configure and run MQTT broker before you
can start this scripts!!!