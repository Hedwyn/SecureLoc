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
 * @file Tag.h
 * @author Baptiste Pestourie
 * @date 2019 December 1st
 * @brief Header file for the cooperative anchor firmware. This firmware is intended for DecaWino chips.
 * Tags are the mobile nodes localized by the anchors.
 * @see https://github.com/Hedwyn/SecureLoc
 */

#ifndef TAG_H
#define TAG_H

#include <SPI.h>
#include <DecaDuino.h>
#include "anchor_c.h"
#include <math.h>
#include "Multilateration.h"


#define INT_MAX 2147483647
#define DEBUG
#ifdef DEBUG
  #define DPRINTF  Serial.print /**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTF(format, args...) ((void)0)
#endif

#ifdef DEBUG
  #define DPRINTFLN  Serial.println /**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTFLN(format, args...) ((void)0)
#endif

#define VERBOSE
#ifdef VERBOSE
  #define VPRINTF  Serial.print /**< When defined, enables debug ouput on the serial port*/
#else
  #define VPRINTF(format, args...) ((void)0)
#endif

#ifdef VERBOSE
  #define VPRINTFLN  Serial.println /**< When defined, enables debug ouput on the serial port*/
#else
  #define VPRINTFLN(format, args...) ((void)0)
#endif


#define T23 100000000 /**< When delayed send is enabled, waiting time between ACK and DATA frame*/

#ifndef NODE_ID
  #define NODE_ID 1/**< Default tag ID. Should be defined during compilation when deploying*/
#endif

/* Rx-TX parameters */
#define CHANNEL 2 
#define PLENGTH 256

/* FSM states */
#define TWR_ENGINE_STATE_INIT 0 /**< Default starting state*/
#define TWR_ENGINE_GHOST_ANCHOR 1 /**< State for ghost anchor operations when designated as such*/
#define TWR_ENGINE_STATE_RX_ON 2 /**< Turns on reception, checks for ghost anchor calls*/
#define TWR_ENGINE_STATE_WAIT_START 3 /**< Start frames polling - gets t2 when receiving*/
#define TWR_ENGINE_STATE_SEND_ACK 4 /**< Sends ACK frame in TWR protocol- gets t3 when sending*/
#define TWR_ENGINE_STATE_SEND_DATA_REPLY 5 /**< Sends DATA frame containing (t2,t3) in TWR protocol*/
#define TWR_ENGINE_STATE_SERIAL 6/**<Handles serial communications with the host*/

#define TWR_MSG_TYPE_START 1  /**< START frame header*/
#define TWR_MSG_TYPE_ACK 2 /**< ACK frame header*/
#define TWR_MSG_TYPE_DATA_REPLY 3 /**< DATA frame header*/
#define GUARD_TIME 40000000 /**< Superior to minimum Rx turn-on time*/

/* platform parameters */
#define NB_ANCHORS 4/**< Total number of anchors on the platform */
#define PLATFORM_LENGTH 2./**<Length of the rectangle formed by the anchors (y coord) */
#define PLATFORM_WIDTH 1./**<Width of the rectangle formed by the anchors (x coord) */
#define DEFAULT_ANCHOR_1_POSITION {.x = 0., .y = 0.}
#define DEFAULT_ANCHOR_2_POSITION {.x = 0., .y = PLATFORM_LENGTH}
#define DEFAULT_ANCHOR_3_POSITION {.x = PLATFORM_WIDTH, .y = PLATFORM_LENGTH}
#define DEFAULT_ANCHOR_4_POSITION {.x = PLATFORM_WIDTH, .y = 0.}
#define DEFAULT_GHOST_ANCHOR {.x = PLATFORM_WIDTH / 2, .y = PLATFORM_LENGTH / 2}

/* DWM1000 Time-of-flight parameters */
#define AIR_SPEED_OF_LIGHT 299700000.0 /**< Speed of light constant to extract distances from time-of-flight measurements*/
#define DW1000_TIMEBASE 15.65E-12 /**< Resolution of the system clock - value of 1 bit*/
#define CALIBRATION 0.9 /**< Calibration coefficient to apply to the distance measurements*/
#define SPEED_COEFF 4.2255E-3/**<DW1000_TIMEBASE*CALIBRATION * AIR_SPEED_OF_LIGHT */

/* Attack parameters */
#define NOISE_STD 0.5/**<Standard deviation of the random distance shift applied by the attack (uniform law) */
#define TARGET_REFRESH_TIME 0/**<Period bewteen two distance shift random generations. SHould be low enough to be realistic. */
#define MANUAL 1 /**<In manual mode, the attack is entirely handled though the serial port. The tag does not get its position itself nor does it chose the target */
#define COMPUTE_POSITION 1 /**<If enabled, the attacker computes itself its position based on the distances received. If not, the position used is the (biased) position computed by the 3d engine */

/* Sliding Window parameters */
#define DMIN 0
#define DMAX 5
#define SW_LENGTH 10

/** @brief DecaWino setup for Tag mode
  * @author Baptiste Pestourie
  * @date 2020 January 1st
*/
void internal_attack_setup();

/** @brief RX/TX setup for DW1000 in tag mode.
  * Sets the channel, preamble length, preamble code and PRF.
  * @author Baptiste Pestourie
  * @date 2019 January 1st
*/
void tag_RxTxConfig();

/** @brief One iteration of the main FSM loop for TWR, with default ID parameters in header file
  * @author Baptiste Pestourie
  * @date 2019 January 1st
*/
void loop();

#endif
