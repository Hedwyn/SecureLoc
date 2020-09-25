/****************************************************************************
* Copyright (C) 2019 LCIS Laboratory - Baptiste Pestourie
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, in version 3.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program. If not, see <http://www.gnu.org/licenses/>.
*
* This program is part of the SecureLoc Project @https://github.com/Hedwyn/SecureLoc
 ****************************************************************************/

/**
 * @file Calibration.h
 * @author Baptiste Pestourie
 * @date 2020 May 1st
 * @brief Source file for the cooperative anchor firmware. This firmware is intended for DecaWino chips.
 * Anchors are fixed stations performing ranging with mobile tags.
 * The cooperative anchor firmware allow an anchor to design a tag to participate in a verification process. See the platform documentation for details.
 * @see https://github.com/Hedwyn/SecureLoc
 */


#include <SPI.h>
#include <DecaDuino.h>

#define DEBUG   //comment to disable debug mode
#ifdef DEBUG
  #define DPRINTF  Serial.print/**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTF(format, args...) ((void)0)
#endif

#ifdef DEBUG
  #define DPRINTFLN  Serial.println/**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTFLN(format, args...) ((void)0)
#endif

#ifndef NODE_ID
  #define NODE_ID 1
#endif
/* RX-TX parameters */
#define CHANNEL 2
#define PLENGTH 256

/* FSM */
#define CBKE_IDLE 0
#define CBKE_PING 1
#define CBKE_PONG 2
#define CBKE_COMPUTE_KEY 3

/* Serial commands */
#define PROVER 0
#define VERIFIER 1
#define SET_PARAM 2
#define CBKE_LENGTH_P 0
#define PING_PONG_DELAY_P 1
#define PLENGTH_P 2
#define PCODE_P 3
#define CHANNEL_P 4
#define PACSIZE_P 5


/* MAC parameters */
#define CBKE_HEADER 7
#define PONG_TIMEOUT 50 /**< In ms */

/* CBKE parameters */
#define CBKE_LENGTH 500 /**< Total number of frames for a single CBKE protocol */
#define CBKE_MAX_LENGTH 2000 /**< Maximum number of frames for a single CBKE protocol */
#define PING_PONG_DELAY 20000 /**Delay to wait before each tranmission in the ping-pong exchanges, in us */
#define SAMPLES_PER_BIT 10
#define REPLY_TIME 60000000
#define TX_TIMEOUT 8000000

typedef struct Sample{
    int symbols;
    uint64_t timestamp;
    float skew;
}Sample;

void compute_average();
void extract_sample();
void CBKE_loop();
void CBKE_setup();
