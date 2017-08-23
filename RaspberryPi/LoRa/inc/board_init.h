/*! 
 * \file       board_init.h
 * \brief        
 *
 * \version    1.0.0
 * \date       April 15 2015
 * \author     Nikola Jovalekic
 */





#ifndef __BOARDINIT_H_
#define __BOARDINIT_H_

#include <stdint.h>
#include "radio.h"


extern volatile uint32_t TickCounter;
extern tRadioDriver *Radio;
extern uint8_t programExecution;

uint32_t linux_hal_get_ms(void);

void SysTick_Handler(void);

void Delay(uint32_t dlyTicks);

void LongDelay ( uint8_t delay );

void PushButtonCallback(uint8_t pin);

void LoRaReceiveCallback(uint8_t pin);

void DoubleToBytes(double x, uint8_t *byteArray);

double BytesToDouble(uint8_t byteArray[]);

uint32_t BytesToUint32_t(uint8_t byteArray[]);

void UsartSend(uint8_t *ptrArray, uint16_t arrayLength);

void UsartSendPartialArray(uint8_t *ptrArray, uint16_t indexStart, uint16_t indexStop);

void BoardInit (void);

#endif

