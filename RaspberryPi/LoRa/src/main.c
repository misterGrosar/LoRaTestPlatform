#define _BSD_SOURCE
#include <signal.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/time.h>
#include <errno.h>
#include <time.h>
#include <math.h>
#include "board_init.h"
#include "sx1276-LoRa.h"


#define BUFFER_SIZE                               9 // Payload size
#define MAX(x,y)(((x) > (y)) ? (x) : (y))

static uint16_t bufferSize = BUFFER_SIZE;

uint8_t LoRaReceivedPacket = 0;

static uint8_t masterTransimtBuffer[BUFFER_SIZE] = {0}; 	// Transmitter buffer
static uint8_t masterReceiveBuffer[BUFFER_SIZE] = {0};		// Receiver buffer

static uint8_t slaveTransmitBuffer[BUFFER_SIZE] = {0};
static uint8_t slaveReceiveBuffer[BUFFER_SIZE] = {0};


uint32_t masterTxPacketId = 0;
uint8_t masterTxPacketIdByteArray[4] = {0};
uint32_t masterRxPacketId = 0;
uint8_t masterRxPacketIdByteArray[4] = {0};

uint32_t slaveTxPacketId = 0;
uint8_t slaveTxPacketIdByteArray[4] = {0};
uint32_t slaveRxPacketId = 0;
uint8_t slaveRxPacketIdByteArray[4] = {0};

static double rssiMin = -148;
static double rssiMax = 5;
static int8_t snrMin = -20;
static int8_t snrMax = 20;

bool writeToFile = false;		// it true, program is writing to file instead to stdout
bool transmitter = true; 		// enables receiver/transmitter
bool lowFrequency = false;		// indicates wether transciever operates on low frequency (434 MHz)
bool implicitHeader = true;		// indicates wether transciever operates in Implicit header mode
bool sfSix = false;				// indicates wether transciever is set to spreading factor 6
bool bidirectional = false;		// If true, device alternates between transmitter and receiver 
uint32_t packetDelay = 1000;	// delay between airtime of two packets

double airTime = 0.0;
bool firstItteration = true;
FILE *file;

void sighandler(int);
void transmitt(void);
void receive(void);
void setBandwidth(uint8_t);
void setSpreadingFactor(uint8_t);
void setCrcOn(bool);
void setCrcValue(uint8_t);
void readArguments(int, char**);
void getDateTime(char*);
void getEpochTime(char*);
double getCurrentMilliAndMicroSec(void);
void sighandler(int);
void testMethods(void);
void openFile(void);
void closeFile(void);
double calculateOnAirTime(void);


/**
 * This is method for transmitting data
 **/
void transmitt()
{	
	// Init transmit buffer
	for (uint8_t i = 0; i < sizeof(masterTransimtBuffer); i++)
		masterTransimtBuffer[i] = 0x55;

	// Convert uint32_t to byte array
	memcpy(masterTxPacketIdByteArray, (uint8_t*)(&masterTxPacketId), sizeof(uint32_t));  

	// Copy packetID to transmitBuffer
	for (uint8_t ii = 0; ii < sizeof(uint32_t); ii++)						 
		masterTransimtBuffer[ii] = masterTxPacketIdByteArray[ii];

	// Save settings to local file if -f flag is present when first packet is transmitted
	if( writeToFile && firstItteration )
	{
		char dateTime[40];
		
		openFile();
				
		if (file != NULL)
		{
			getDateTime(dateTime);
			fprintf(file, "Created at %s\n", dateTime);
			
			fprintf(file, "Transmitting packets with LoRa signal parameters bw: %x (%s kHz), sf: %d, crc on: %x, cr: %x (%s), lf: %x, bidirectional: %x.\n",
				SX1276LoRaGetSignalBandwidth(), SX1276LoRaGetSignalBandwidthValue(), 
				SX1276LoRaGetSpreadingFactor(), SX1276LoRaGetPacketCrcOn(),
				SX1276LoRaGetCRCBin(), SX1276LoRaGetCRCValue(), lowFrequency, bidirectional);
			fprintf(file, "TxID;Timestamp(UTC);\n");
			
			fsync(file);			
			//Close file each time to prevent losing data
			closeFile();
		}
	
		printf("Transmitting packets with LoRa signal parameters bw: %x (%s kHz), sf: %d, crc on: %x, cr: %x (%s), lf: %x, bidirectional: %x.\n",
			SX1276LoRaGetSignalBandwidth(), SX1276LoRaGetSignalBandwidthValue(), 
			SX1276LoRaGetSpreadingFactor(), SX1276LoRaGetPacketCrcOn(),
			SX1276LoRaGetCRCBin(), SX1276LoRaGetCRCValue(), lowFrequency, bidirectional);
	}
	// If -f flag is not present, print settings to stdout to parse them within another program
	else if ( firstItteration )
	{
		char *biStr = "";
		char *lfStr = "";
		if( bidirectional )
		{
			biStr = "bi;";
		}
		// If 434 MHz is used for transmitting data
		if( lowFrequency )
		{
			lfStr = "lf;";
		}
		
		printf("\nSETTINGS:%x;%d;%x;%x;%s%s\n",
			SX1276LoRaGetSignalBandwidth(), SX1276LoRaGetSpreadingFactor(), 
			SX1276LoRaGetPacketCrcOn(), SX1276LoRaGetCRCBin(), lfStr, biStr);
		fflush(stdout);
	}
	
	// Transmit packets
	while(1)
	{			
		// JUST SET THE PACKET TO BE SENT AND INITIALIZE RfState TO RF_STATE_TX_INIT!!!!!
		Radio->SetTxPacket(masterTransimtBuffer, sizeof(masterTransimtBuffer)); 	
		
		while(1)
		{
			// When packet is sent, write to file or print to stdout
			if (Radio->Process() == RF_TX_DONE)
			{					
				char *timeNow;			//current time in seconds and microseconds
				getEpochTime(&timeNow);
				
				// Save resoults to local file 
				if( writeToFile )
				{
					//Open file each time to prevent losing data
					openFile();
					
					if (file != NULL)
					{
						fprintf(file, "%u;%s;\n", masterTxPacketId, &timeNow);
						fsync(file);
						
						//Close file each time to prevent losing data
						closeFile();
					}
					
					printf("TxID: %u, CurrTime: %s\n", masterTxPacketId, &timeNow);
				}
				// Print resoults to stdout to parse them within another program
				else
				{
					//prints TxID
					printf("OK:%u;%s;\n", masterTxPacketId, &timeNow);
					fflush(stdout);
				}
				
				// Convert uint32_t to byte array
				memcpy(masterTxPacketIdByteArray, (uint8_t*)(&masterTxPacketId), sizeof(uint32_t));  

				// Copy packetID to transmitBuffer
				for (uint8_t ii = 0; ii < sizeof(uint32_t); ii++)						 
					masterTransimtBuffer[ii] = masterTxPacketIdByteArray[ii];
				break;
			}
		}
		
		firstItteration = false;
		// If bi-directional mode is used
		if( bidirectional )
		{
			// immediatly switch to receiver mode
			transmitter = false;
			// On each device increase counter by two, 
			// for easier identification of device
			masterTxPacketId += 2; 
			break;
		}
		else
		{	
			// If normal mode is used, wait packetDelay milliseconds 
			// before sending new packet. This is for device synchronization
			masterTxPacketId ++;
			Delay(packetDelay);
		}
	}
}

/**
 * This method is for receiving packets
 **/
void receive()
{
	uint32_t errCnt = 0;
	// Start receiver
	Radio->StartRx();

	// Save settings to local file only once at program startup if -f flag is present
	if( writeToFile && firstItteration )
	{
		char dateTime[40];
		
		//Open file each time to prevent losing data
		openFile();
		if (file != NULL)
		{
			getDateTime(dateTime);
			fprintf(file, "Created at %s\n", dateTime);
			
			fprintf(file, "Receiving packets with LoRa signal parameters bw: %x (%s kHz), sf: %d, crc on: %x, cr: %x (%s), lf: %x, bidirectional: %x.\n",
				SX1276LoRaGetSignalBandwidth(), SX1276LoRaGetSignalBandwidthValue(), 
				SX1276LoRaGetSpreadingFactor(), SX1276LoRaGetPacketCrcOn(),
				SX1276LoRaGetCRCBin(), SX1276LoRaGetCRCValue(), lowFrequency, bidirectional);
			fprintf(file,"RxID;Current RSSI;Packet RSSI;SNR;Timestamp(UTC);ErrorNo;\n");
			
			fsync(file);
			
			//Close file each time to prevent losing data
			closeFile();
		}
		
		printf("Receiving packets with LoRa signal parameters bw: %x (%s kHz), sf: %d, crc on: %x, cr: %x (%s), lf: %x, bidirectional: %x.\n",
			SX1276LoRaGetSignalBandwidth(), SX1276LoRaGetSignalBandwidthValue(), 
			SX1276LoRaGetSpreadingFactor(), SX1276LoRaGetPacketCrcOn(),
			SX1276LoRaGetCRCBin(), SX1276LoRaGetCRCValue(), lowFrequency, bidirectional);
	}
	// Print settings to stdout to parse them within another program
	else if (firstItteration)
	{
		char *biStr = "";
		if(bidirectional)
		{
			biStr = "bi;";
		}
		
		// If 434 MHz is used for transmitting data
		if(lowFrequency)
		{
			printf("\nSETTINGS:%x;%d;%x;%x;lf;%s\n",
				SX1276LoRaGetSignalBandwidth(), SX1276LoRaGetSpreadingFactor(), 
				SX1276LoRaGetPacketCrcOn(), SX1276LoRaGetCRCBin(), biStr);
		} 
		// If 868 MHz is used for transmitting data
		else 
		{
			printf("\nSETTINGS:%x;%d;%x;%x;%s\n",
			SX1276LoRaGetSignalBandwidth(), SX1276LoRaGetSpreadingFactor(), 
			SX1276LoRaGetPacketCrcOn(), SX1276LoRaGetCRCBin(), biStr);
		}
		fflush(stdout);
	}

	// Max wait time, before switching to another mode (used in bi-directional mode)
	double maxWaitTime = 0.0; 
	
	if (firstItteration)
	{ 
		firstItteration = false;
		maxWaitTime = (airTime + packetDelay);
		masterTxPacketId = 1; // To easier identify devices when analysing data
	}
	else
	{
		maxWaitTime = (airTime + 2 * packetDelay);
	}

	double startSysTime = getCurrentMilliAndMicroSec();
	
	// Wait for packets
	while (1)
	{
		double now = getCurrentMilliAndMicroSec() - startSysTime;
		if(bidirectional && now >= maxWaitTime)
		{
			// If device was waiting maxWaitTime, and no packet was received, 
			// than switch to transmitter (used in bi-directional mode)
			transmitter = true;
			break;
		}
		// Packet was received
		if (Radio->Process() == RF_RX_DONE)
		{
			char *timeNow;	// Packet time in seconds and micro seconds
			getEpochTime(&timeNow); // Get current time
			
			Radio->GetRxPacket(slaveReceiveBuffer, (uint16_t*)&bufferSize);
			
			// Copy packetID to rxPacketIDByteArray
			for (uint8_t jj = 0; jj < sizeof(uint32_t); jj++)						 
				slaveRxPacketIdByteArray[jj] = slaveReceiveBuffer[jj];
			// Convert received data to int	
			slaveRxPacketId = BytesToUint32_t(slaveRxPacketIdByteArray);
						
			// If packet was correctly received
			if(	(SX1276LoRaGetPacketRssi() > rssiMin) && (SX1276LoRaGetPacketRssi() < rssiMax) && 
				(SX1276LoRaGetPacketSnr() > snrMin) && (SX1276LoRaGetPacketSnr() < snrMax))
			{
				double cRSSI = SX1276LoRaReadRssi(); 		// Current RSSI (this is packet average RSSI)
				double pRSSI = SX1276LoRaGetPacketRssi();	// Packet RSSI
				int8_t snr = SX1276LoRaGetPacketSnr();		// SNR				
				
				// Save resoults to local file 
				if( writeToFile )
				{
					// Open file each time to prevent losing data
					openFile();
					
					if( file != NULL )
					{
						// Save Current RSSI, Packet RSSI, SNR, timestamp, CRC ERR NUM
						fprintf(file, "%u;%.1f;%.1f;%d;%s;\n", 
								slaveRxPacketId, cRSSI, pRSSI, snr, &timeNow);
						fsync(file);
						closeFile();
					}
					printf("RxID: %u, Current RSSI: %.1f, Packet RSSI: %.1f, SNR: %d, Timestamp: %s\n", 
								slaveRxPacketId, cRSSI, pRSSI, snr, &timeNow);
				}
				/// Print resoults to stdout to parse them within another program
				else
				{
					// Print RxID, Current RSSI, Packet RSSI, SNR, timestamp
					printf("OK:%u;%.1f;%.1f;%d;%s;\n", slaveRxPacketId, cRSSI, pRSSI, snr, &timeNow);
					fflush(stdout);
				}
			}
			// CRC error occured
			else
			{
				double cRSSI = SX1276LoRaReadRssi(); 		// Current RSSI
				double pRSSI = SX1276LoRaGetPacketRssi();	// Packet RSSI
				int8_t snr = SX1276LoRaGetPacketSnr();		// SNR
				
				errCnt++; // Crc error counter
				
				// Save resoults to local file 
				if( writeToFile )
				{
					// Open file each time to prevent losing data
					openFile();
					
					if( file != NULL )
					{
						// Save Current RSSI, Packet RSSI, SNR, timestamp, CRC ERR NUM
						fprintf(file, "-1;%.1f;%.1f;%d;%s;%u;\n", cRSSI, pRSSI, snr, &timeNow, errCnt);
						fsync(file);
						closeFile();
					}
					printf("Current RSSI: %.1f, Packet RSSI: %.1f, SNR: %d, CRC ERR NUM: %u\n", 
							cRSSI, snr, pRSSI, errCnt);
				}
				/// Print resoults to stdout to parse them within another program
				else
				{
					// Print Current RSSI, Packet RSSI, SNR, timestamp, CRC ERR NUM
					printf("CRCERR:%.1f;%.1f;%d;%s;%u;\n", cRSSI, pRSSI, snr, &timeNow, errCnt);
					fflush(stdout);
				}
			}
			if(bidirectional)
			{
				// When bidirectional mode is used, wati packet delay 
				// time befor switching mode. This is for device synchronization
				Delay(packetDelay);
				transmitter = true;
				break;
			}
		}		
	}
}

/*!
 * \brief 	Change signal bandwith value. Possible BW values 
 * 			[0: 7.8kHz, 1: 10.4 kHz, 2: 15.6 kHz, 3: 20.8 kHz, 4: 31.2 kHz,
 * 			5: 41.6 kHz, 6: 62.5 kHz, 7: 125 kHz, 8: 250 kHz, 9: 500 kHz]
 * 			NOTE: with no oscilator only bandwiths 4 and higher works!!!
 * 
 * \param Signal bandwidth value 
 * \retval New BW value
 */
void setBandwidth( uint8_t bwVal )
{	
	SX1276LoRaSetOpMode( RFLR_OPMODE_SLEEP );	
	SX1276LoRaSetSignalBandwidth( bwVal );
	SX1276LoRaSetOpMode( RFLR_OPMODE_STANDBY );
}

/*!
 * \brief 	Change spreading factor. Possible SF values [6, 7, 8, 9, 10, 11, 12],
 * 			If spreading factor 6 is used, header will be set to Implicit mode 
 * 
 * \param Spreading factor value 
 * \retval New SF value
 */
void setSpreadingFactor( uint8_t sfVal )
{	
	SX1276LoRaSetOpMode( RFLR_OPMODE_SLEEP );
		
	if( sfVal == 6 )
	{	
		if(!implicitHeader)
		{
			printf("INFO4: Transciever cannot operate in Explicit header mode if Spreading factor is set to 6.\n");
		}
		sfSix = true;
		implicitHeader = true;
		SX1276LoRaSetSpreadingFactor( sfVal );		
		SX1276LoRaSetImplicitHeaderOn( implicitHeader );
		SX1276LoRaSetNbTrigPeaks( 5 );		
		SX1276LoRaSetRegDetectionTreshold( 0x0C );
	}
	else if( 6 < sfVal && sfVal <= 12 )
	{
		sfSix = false;
		SX1276LoRaSetSpreadingFactor( sfVal );
		SX1276LoRaSetImplicitHeaderOn( implicitHeader );
		SX1276LoRaSetNbTrigPeaks( 3 );
		SX1276LoRaSetRegDetectionTreshold( 0x0A );
	}
	else
	{
		printf("ERROR6: Spreading factor value %x is not valid value. Please use values from 6 to 12.\n", sfVal);
		fflush(stdout);
		sfVal = -1;
	}

	SX1276LoRaSetOpMode( RFLR_OPMODE_STANDBY );
}

/*!
 * \brief 	Turn CRC on or off. 
 * 
 * \param If set to true, CRC wil be turned on 
 * \retval Is CRC on
 */
void setCrcOn( bool crcOn )
{
	SX1276LoRaSetOpMode( RFLR_OPMODE_SLEEP );
	SX1276LoRaSetPacketCrcOn( crcOn );
	SX1276LoRaSetOpMode( RFLR_OPMODE_STANDBY );
}

/*!
 * \brief 	Set CRC value. Possible CRC values: [1: 4/5, 2: 4/6, 3: 4/7, 4: 4/8]. 
 * 
 * \param CRC value
 * \retval New CRC value 
 */
void setCrcValue( uint8_t value )
{
	SX1276LoRaSetOpMode( RFLR_OPMODE_SLEEP );
	
	if( SX1276LoRaGetPacketCrcOn() == 0 )
	{
		printf("INFO: CRC is turned OFF. Setting CRC value will not have effect untill you turn it ON.");
		fflush(stdout);
	}
	
	SX1276LoRaSetErrorCoding( value );
	SX1276LoRaSetOpMode( RFLR_OPMODE_STANDBY );
}

/**
 * Read parameters from arguments and set them as initial program values
 **/
void readArguments( int argc, char *argv[] )
{	
	if (argc > 0) {
		bool delaySet = false;
		for (uint8_t i=1; i<argc; i++)
		{
			bool isCommand = true;
			char *command;
			const char * valueStr;
			uint32_t value = 0;
			
			char *tok = argv[i], *end = argv[i];
			while ((tok = strsep(&end, "=")) != NULL) {
				if( isCommand )
				{
					isCommand = false;
					command = tok;
				}
				else
				{
					value = atol(tok);
				}
			}
				
			if (strcmp (command, "-r") == 0) // turn receiver on
			{
				transmitter = false;
				printf("INFO0: Node is in RECEIVER mode!\n");
				fflush(stdout);
			} 
			else if (strcmp (command,"-f") == 0) // bandwidth value
			{
				writeToFile = true;
				printf("INFO1: Program will WRITE TO LOCAL FILE!\n");
				fflush(stdout);
			}
			else if (strcmp (command,"-d") == 0) // delay between airtime of two packets
			{
				packetDelay = value;
				delaySet = true;
				printf("INFO2: Delay between airtime of two packets is %d ms!\n", value);
				fflush(stdout);
			}
			else if (strcmp (command,"-E") == 0) // set Explicit header mode on
			{
				if(sfSix)
				{
					implicitHeader = true;
					printf("INFO4: Transciever cannot operate in Explicit header mode if Spreading factor is set to 6.\n");
				}
				else
				{
					implicitHeader = false;
					printf("INFO4: Transciever operates in Explicit header mode.\n");
				}
				fflush(stdout);	
				SX1276LoRaSetImplicitHeaderOn( implicitHeader );							
			}
			else if (strcmp (command,"-lf") == 0) // bandwidth value
			{
				lowFrequency = true;
				printf("INFO3: Transciever operates on 434 Mhz.\n");
				SX1276LoRaSetRFFrequency( 434000000 );
				fflush(stdout);
			}
			else if (strcmp (command,"-bi") == 0) // device alternates between transmitter and receiver 
			{
				bidirectional = true;
				printf("INFO6: Transciever operates in BIDIRECTIONAL mode.\n");
				fflush(stdout);
			}
			else if (strcmp (command,"-b") == 0) // bandwidth value
			{
				if( value < 0 || value > 9 )
				{
					printf("ERROR2: Invalid value! Please use -h for help.\n");
					fflush(stdout);
					exit(1);
				}
				else 
				{
					setBandwidth( value );
				}
			} 
			else if (strcmp (command, "-s") == 0) //spreading factor
			{
				if( value < 6 || value > 12 )
				{
					printf("ERROR3: Invalid value! Please use -h for help.\n");
					fflush(stdout);
					exit(1);
				}
				else 
				{
					setSpreadingFactor( value );
				}
			} 
			else if (strcmp (command , "-e") == 0) // CRC value
			{
				if( value < 1 || value > 4 )
				{
					printf("ERROR4: Invalid value! Please use -h for help.\n");
					fflush(stdout);
					exit(1);
				}
				else 
				{
					setCrcValue( value );
				}
			} 
			else if (strcmp (command, "-c") == 0) //CRC on/off
			{
				if( value < 0 || value > 1 )
				{
					printf("ERROR5: Invalid value! Please use -h for help.\n");
					fflush(stdout);
					exit(1);
				}
				else 
				{
					setCrcOn( value );
				}
			} 
			else if (strcmp (command, "-h") == 0 || strcmp (command, "--help") == 0)
			{
				printf ("-h or --help \t show help \n");
				printf ("-r \t\t if this flag is set receiver is activated \n");
				printf ("-f \t\t save measurements to local file instead of printing them on stdout \n");
				printf ("-d \t\t delay in milliseconds between airtime of two packets. Default value is 1000 ms.\n");
				printf ("-b \t\t set bandwith value [0: 7.8kHz, 1: 10.4 kHz, 2: 15.6 kHz, 3: 20.8 kHz, 4: 31.2 kHz \n");
				printf (" 5: 41.6 kHz, 6: 62.5 kHz, 7: 125 kHz, 8: 250 kHz, 9: 500 kHz]. \n");
				printf ("-s \t\t set spreading factor value [6: 64, 7: 128, 8: 256, 9: 512, 10: 1024, 11: 2048, 12: 4096] chips \n");
				printf ("-e \t\t set error coding (crc) value [1: 4/5, 2: 4/6, 3: 4/7, 4: 4/8]. \n");
				printf ("-E \t\t if this flag is set, transceiver will operate in explicit header mode. \n");
				printf ("-c \t\t set 1 to turn crc on or 0 to turn off. \n");
				printf ("-lf \t\t if this flag is set, transciever will work on low frequency (434 MHz). \n");
				printf ("-bi \t\t if this flag is set, transciever alternates between transmitter and receiver. \n");
				exit(0);
			}
		}
		
		// To ensure correct working in bidirectional mode
		if( bidirectional && !delaySet ){
			printf("ERROR6: If transceiver operates in bidirectional mode, delay time has to be set. Please use -h for help.\n");
			fflush(stdout);
			exit(1);
		}
	}
}

/**
 * Get formated current time (in accuracy of milliseconds)
 **/
void getDateTime(char *dateTime){
	char buffer[40];
	int millisec;
	struct tm* tm_info;
	struct timeval tv;

	gettimeofday(&tv, NULL);

	millisec = (int)(tv.tv_usec/1000.0); // Round to nearest millisec
	if (millisec>=1000) { // Allow for rounding up to nearest second
		millisec -=1000;
		tv.tv_sec++;
	}

	tm_info = localtime(&tv.tv_sec);
	strftime(buffer, 26, "%d.%m.%Y %H:%M:%S", tm_info);	
	snprintf(dateTime, 40, "%s.%03d", buffer, millisec);
}

/**
 * Get epoche time in seconds and microseconds 
 */
void getEpochTime(char *timeNow)
{	
	struct timeval now;
	int rc = gettimeofday(&now, NULL);
	
	if(rc==0)
	{
		snprintf(timeNow, 20, "%u.%06u", now.tv_sec, now.tv_usec);
	}
	else
	{
		printf("ERROR7: while getting time of day\n");
		snprintf(timeNow, 20, "");
		fflush(stdout);
	}
}

/**
 * Returns current time in milliseconds with accuracy of microsecond
 */
double getCurrentMilliAndMicroSec()
{
	struct timeval now;
	int rc = gettimeofday(&now, NULL);
	
	if(rc==0)
	{
		return now.tv_sec * 1000.0 + now.tv_usec / 1000.0;
	}
	return 0;
}

/**
 * Handle interrupt signal. Write to file or to stcout and terminate program
 */
void sighandler(int signum)
{
	if( writeToFile )
	{
		fprintf(file, "EOF\n");
		fclose(file);
	
		printf("\n\nINFO: Interupt signal caught.\nFinishing writing to file and exiting the program.\n");
	}
	else
	{
		printf("ERROR0: Interupt signal caught.\nExiting the program.\n\n");
		fflush(stdout);
	}
	exit(0);
}
	
/**
 * This method is for test purpuses and serves as a cheat sheet for 
 * some most usefull LoRa methods. 
 */
void testMethods(){
	printf("--------- Start Test ---------\n");
	
	printf("Current LoRa operation mode: 0x%x\n", SX1276LoRaGetOpMode());
	
	printf("Bw hex: 0x%x\n", SX1276LoRaGetSignalBandwidth());
	printf("Bw: %d kHz\n", SX1276LoRaGetSignalBandwidthValue());
	SX1276LoRaSetSignalBandwidth(1);
	printf("Bw (10.4 kHz): %.2f kHz\n", SX1276LoRaGetSignalBandwidthValue());
	
	printf("CRC on: %d\n", SX1276LoRaGetPacketCrcOn());	
	SX1276LoRaSetPacketCrcOn(0);
	printf("CRC on: %d\n", SX1276LoRaGetPacketCrcOn());	
	SX1276LoRaSetPacketCrcOn(1);
	
	printf("CRC hex: 0x%x\n", SX1276LoRaGetCRCBin());
	printf("CRC: %s\n", SX1276LoRaGetCRCValue());
	SX1276LoRaSetErrorCoding(3);
	printf("CRC (4/7): %s\n", SX1276LoRaGetCRCValue());
	
	printf("Spreading factor: %d\n", SX1276LoRaGetSpreadingFactor());
	printf("Spreading factor: %s chirps\n", SX1276LoRaGetSpreadingFactorInChirps());
	SX1276LoRaSetSpreadingFactor(12);
	printf("Spreading factor (12): %d\n", SX1276LoRaGetSpreadingFactor());
	
	/** And also methods: **/
	//SX1276LoRaGetPacketRssi();
	//SX1276LoRaGetPacketSnr();
	//printf("RX Gain: %u\n", SX1276LoRaReadRxGain());
	
	printf("--------- End of Test ---------\n"); 
}

/**
 * Open file
 **/
void openFile()
{
	file = fopen("/home/pi/projects/LoRa/tests/measurements.csv", "a");
	if (file == NULL)
	{
		printf("ERROR opening file!\n");
	}
}

/**
 * Close file
 **/
void closeFile()
{
	if (file != NULL)
	{
		fclose(file);
	}
}	

/**
 * Calculate packets airtime.
 * This formula is from Semtechs SX1276 chips datasheet
 **/
double calculateOnAirTime()
{
	int bw = SX1276LoRaGetSignalBandwidth();
	double bwValue = 0;
	
	if( bw == 0x0 )
		bwValue = 7.8;
	else if( bw == 0x1 )
		bwValue = 10.4;
	else if( bw == 0x2 )
		bwValue = 15.6;
	else if( bw == 0x3 )
		bwValue = 20.8;
	else if( bw == 0x4 )
		bwValue = 31.25;
	else if( bw == 0x5 )
		bwValue = 41.7;
	else if( bw == 0x6 )
		bwValue = 62.5;
	else if( bw == 0x7 )
		bwValue = 125.0;
	else if( bw == 0x8 ){
		bwValue = 250.0;
	}
	else if( bw == 0x9 )
		bwValue = 500.0;
	
	int h = 0;
	if (implicitHeader)
		h = 1;
	int de = 0;
	if(SX1276LoRaGetLowDatarateOptimize())
		de = 1;
		
	double tSym = (pow(2, SX1276LoRaGetSpreadingFactor()) / (bwValue * 1000)) * 1000;
	double tPream = (SX1276LoRaGetPreambleLength() + 4.25) * tSym;
	double a = ((8 * SX1276LoRaGetPayloadLength()) - (4 * SX1276LoRaGetSpreadingFactor()) + 28 + 16 - (20 * h));
	double b = (4 * (SX1276LoRaGetSpreadingFactor() - (2 * de)));
	double mVal = ceil(a / b) * (SX1276LoRaGetErrorCoding() + 4);
	double payleadSymbNB = 8.0 + MAX(mVal, 0.0);
	
	double tPayload = payleadSymbNB * tSym;
	double tPacket = tPream + tPayload;
		
	return tPacket;
}

int main(int argc, char *argv[])
{
	// Initialization of the LoRa chip
	BoardInit();
	
	// For implicit header mode is important to set payload lenght, 
	// because it is not recovered on the receiver side
	SX1276LoRaSetPayloadLength( BUFFER_SIZE );
	
	// Read console arguments and set LoRa parametters
	readArguments(argc, argv);
	
	// Catch Ctrl+C interrupt key
	signal(SIGINT, sighandler);
	
	// Calculate LoRa packet airtime with current LoRa parameter settings 
	airTime = calculateOnAirTime();
	printf("INFO5: Packet airtime is %.3f ms.\n", airTime);
	
	// Transmit or receive packets. If bi-directional mode is used,
	// this loop itterates between transmitter and receiver, otherwise 
	// only one mode is used during program runtime 
	while (1)
	{
		if (transmitter)
		{
			transmitt();
		}
		else
		{
			receive();
		}
	}
	
	return(0);
}
