/*! 
 * \file       board_init.c
 * \brief      Initializes peripherals on the board
 *
 * \version    1.0.0 
 * \date       April 15 2015
 * \author     Nikola Jovalekic
 *
 */

#include <sys/time.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "wiringPi.h"
#include "wiringPiSPI.h"
#include "board_init.h"
#include "radio.h"
#include "platform.h"
#include "sx1276-Fsk.h"
#include "sx1276.h"
#include "sx1276-LoRa.h"


volatile uint32_t TickCounter = 0; 						// Counts 1ms timeTicks
tRadioDriver *Radio = NULL;								// Radio structure set in main



/**************************************************************************//**
 * @brief linux_hal_get_ms() 
 * Get Curent Time of a Day in Miliseconds 
 *****************************************************************************/
uint32_t linux_hal_get_ms() {
    struct timeval t;

    if (gettimeofday(&t, NULL) < 0) {
        perror("gettimeofday");
        return -1;
    }

    return (t.tv_sec*1000 + t.tv_usec/1000);
}



/**************************************************************************//**
 * @brief Delays number of msTick Systicks (typically 1 ms)
 * @param dlyTicks Number of ticks to delay
 *****************************************************************************/
void Delay(uint32_t dlyTicks)
{
	uint32_t curTicks;

	curTicks = linux_hal_get_ms();
	while ((linux_hal_get_ms() - curTicks) < dlyTicks) ;
}



/**************************************************************************//**
 * @brief Converts a double to byte array to be written in NAND flash
 * @param[in]  x - double to be written in NAND flash
 * @param[in]  byteArray - array to be written in NAND flasah
 *
 *****************************************************************************/
void DoubleToBytes(double x, uint8_t *byteArray)
{
	memcpy(byteArray, (uint8_t*)(&x), sizeof(double));
}


/**************************************************************************//**
 * @brief Converts byte array to double
 * @param[in]   byteArray - byte array to be converted
 * @param[out]  double that represents converted byte array
 *
 *****************************************************************************/
double BytesToDouble(uint8_t byteArray[])
{
	double convertedVal = 0;

	memcpy(&convertedVal, (uint8_t*)(byteArray), sizeof(convertedVal));
	return convertedVal;
}


/**************************************************************************//**
 * @brief Converts byte array to uint32_t
 * @param[in]   byteArray - byte array to be converted
 * @param[out]  uint32_t that represents converted byte array
 *
 *****************************************************************************/
uint32_t BytesToUint32_t(uint8_t byteArray[])
{
	uint32_t convertedVal = 0;

	memcpy(&convertedVal, (uint8_t*)(byteArray), sizeof(convertedVal));
	return convertedVal;
}

/**************************************************************************//**
 * @brief Initializes the whole board (uC and RF transceiver)
 *
 *****************************************************************************/
void BoardInit()
{

    /* Initialize  wiringPI library */
    wiringPiSetup();

    wiringPiSPISetupMode (0, 5000000, 1);


	/* Initialize driver for SX1276 */
	Radio = RadioDriverInit();
	

	/* Initialize RF state machine to RF_STATE_IDLE mode */
	Radio->Init();

}

