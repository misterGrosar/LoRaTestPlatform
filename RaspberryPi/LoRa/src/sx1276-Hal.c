/*
 * THE FOLLOWING FIRMWARE IS PROVIDED: (1) "AS IS" WITH NO WARRANTY; AND 
 * (2)TO ENABLE ACCESS TO CODING INFORMATION TO GUIDE AND FACILITATE CUSTOMER.
 * CONSEQUENTLY, SEMTECH SHALL NOT BE HELD LIABLE FOR ANY DIRECT, INDIRECT OR
 * CONSEQUENTIAL DAMAGES WITH RESPECT TO ANY CLAIMS ARISING FROM THE CONTENT
 * OF SUCH FIRMWARE AND/OR THE USE MADE BY CUSTOMERS OF THE CODING INFORMATION
 * CONTAINED HEREIN IN CONNECTION WITH THEIR PRODUCTS.
 * 
 * Copyright (C) SEMTECH S.A.
 */
/*! 
 * \file       sx1276-Hal.c
 * \brief      SX1276 Hardware Abstraction Layer
 *
 * \version    2.0.B2 
 * \date       Nov 21 2012
 * \author     Miguel Luis
 *
 * Last modified by Miguel Luis on Jun 19 2013
 */
#include <stdint.h>
#include <stdio.h>
#include <stdbool.h> 


#include "sx1276-Hal.h"
#include "wiringPi.h"
#include "wiringPiSPI.h"
#include "board_init.h"

/*!
 * SX1276 RESET I/O definitions
 */
#define RESET_PIN                                   28 //Phy: 38

/*!
 * SX1276 DIO pins  I/O definitions
 */

#define DIO0_PIN                                    24 //Phy: 35

#define DIO1_PIN                                    27 //Phy: 36

#define DIO2_PIN                                    23 //Phy: 33

#define DIO3_PIN                                    22 //Phy: 31

#define DIO4_PIN                                    26 //Phy: 32

#define DIO5_PIN                                    21 //Phy: 29

#define RXTX_PIN                                    4  //Phy: 16

#define HFSW_CTRL									2  //Phy: 13 

#define LFSW_CTRL									25 //Phy: 37 


void SX1276InitIo( void )
{

    // Configure DIO0
    pinMode (DIO0_PIN, INPUT);
    pullUpDnControl (DIO0_PIN, PUD_OFF);
    
    // Configure DIO1
    pinMode (DIO1_PIN, INPUT);
    pullUpDnControl (DIO1_PIN, PUD_OFF);
    
    // Configure DIO2
    pinMode (DIO2_PIN, INPUT);
    pullUpDnControl (DIO2_PIN, PUD_OFF);

    // Configure DIO3 as input
    pinMode (DIO3_PIN, INPUT);
    pullUpDnControl (DIO3_PIN, PUD_OFF);
    
    // Configure DIO4 as input
    pinMode (DIO4_PIN, INPUT);
    pullUpDnControl (DIO4_PIN, PUD_OFF);
    
    // Configure DIO5 as input
    pinMode (DIO5_PIN, INPUT);
    pullUpDnControl (DIO5_PIN, PUD_OFF);
	
	// Configure control pin for low freq RF switch
    pinMode (LFSW_CTRL, OUTPUT);
    pullUpDnControl (LFSW_CTRL, PUD_UP);
	
	// Configure control pin for high freq RF switch
    pinMode (HFSW_CTRL, OUTPUT);
    pullUpDnControl (HFSW_CTRL, PUD_UP);
	
	
}

void SX1276SetReset( uint8_t state )
{
	
	// Configure RESET pin
    pinMode (RESET_PIN, OUTPUT);
    pullUpDnControl (RESET_PIN, PUD_UP);
	
    if(state == RADIO_RESET_ON)
    {
        // Set RESET pin to 0
        digitalWrite (RESET_PIN, 0);
	}
	else if(state == RADIO_RESET_OFF)
	{
		// Set RESET pin to 1
        digitalWrite (RESET_PIN, 1);
	}

}

void SX1276Write( uint8_t addr, uint8_t data )
{
    SX1276WriteBuffer( addr, &data, 1 );
}

void SX1276Read( uint8_t addr, uint8_t *data )
{
    SX1276ReadBuffer( addr, data, 1 );
}

void SX1276WriteBuffer( uint8_t addr, uint8_t *buffer, uint8_t size )
{
    uint8_t i = 0;
    unsigned char tmpBuf[size+1];
    tmpBuf[0] = (unsigned char) (addr | 0x80);
    for(i = 1; i < size + 1; i++)
	tmpBuf[i] = (unsigned char) (buffer[i-1]);
    wiringPiSPIDataRW(0, tmpBuf, size+1);
}

void SX1276ReadBuffer( uint8_t addr, uint8_t *buffer, uint8_t size )
{
    uint8_t i = 0;
    unsigned char tmpBuf[size+1];
    tmpBuf[0] = (unsigned char) (addr & 0x7F);
    for(i = 1; i < size + 1; i++)
	tmpBuf[i] = 0;

    wiringPiSPIDataRW(0, tmpBuf, size+1);

    for (i = 1; i < size+1; i++)
    {
	buffer[i-1] = (uint8_t) (tmpBuf[i]); 	
    //printf("RegValue: 0x%02X\n", buffer[i-1]);    
    }
}

void SX1276WriteFifo( uint8_t *buffer, uint8_t size )
{
    SX1276WriteBuffer( 0, buffer, size );
}

void SX1276ReadFifo( uint8_t *buffer, uint8_t size )
{
    SX1276ReadBuffer( 0, buffer, size );
}



uint8_t SX1276ReadDio0( void )
{
    return digitalRead (DIO0_PIN);
}

uint8_t SX1276ReadDio1( void )
{
    return digitalRead (DIO1_PIN);
}

uint8_t SX1276ReadDio2( void )
{
    return digitalRead (DIO2_PIN);
}

uint8_t SX1276ReadDio3( void )
{
    return digitalRead (DIO3_PIN);
}

uint8_t SX1276ReadDio4( void )
{
    return digitalRead (DIO4_PIN);
}

uint8_t SX1276ReadDio5( void )
{
    return digitalRead (DIO5_PIN);
}

void SX1276WriteRxTx( uint8_t txEnable )
{
    if( txEnable != 0 )
    {
        digitalWrite (HFSW_CTRL, 1);
        digitalWrite (LFSW_CTRL, 0);

    }
    else
    {
        digitalWrite (HFSW_CTRL, 0);
        digitalWrite (LFSW_CTRL, 1);

    }
}
