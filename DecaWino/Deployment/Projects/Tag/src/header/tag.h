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



#define _DEBUG_
#ifdef _DEBUG_
  #define DPRINTF  Serial.print /**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTF(format, args...) ((void)0)
#endif

#ifdef _DEBUG_
  #define DPRINTFLN  Serial.println /**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTFLN(format, args...) ((void)0)
#endif


#ifndef NODE_ID
  #define NODE_ID 1/**< Default tag ID. Should be defined during compilation when deploying*/
#endif

/* FSM states */
#define TWR_ENGINE_STATE_INIT 0 /**< Default starting state*/
#define TWR_ENGINE_GHOST_ANCHOR 1 /**< State for ghost anchor operations when designated as such*/
#define TWR_ENGINE_STATE_RX_ON 2 /**< Turns on reception, checks for ghost anchor calls*/
#define TWR_ENGINE_STATE_WAIT_START 3 /**< Start frames polling - gets t2 when receiving*/
#define TWR_ENGINE_STATE_SEND_ACK 4 /**< Sends ACK frame in TWR protocol- gets t3 when sending*/
#define TWR_ENGINE_STATE_SEND_DATA_REPLY 5 /**< Sends DATA frame containing (t2,t3) in TWR protocol*/


#define TWR_MSG_TYPE_START 1  /**< START frame header*/
#define TWR_MSG_TYPE_ACK 2 /**< ACK frame header*/
#define TWR_MSG_TYPE_DATA_REPLY 3 /**< DATA frame header*/
#define GUARD_TIME 40000000 /**< Superior to minimum Rx turn-on time*/





/** @brief DecaWino setup for Tag mode
  * @author Baptiste Pestourie
  * @date 2020 January 1st
*/
void tag_setup();

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
