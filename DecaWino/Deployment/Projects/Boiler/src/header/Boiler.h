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
 * @file Boiler., h
 * @author Baptiste Pestourie
 * @date 2020 February 1st
 * @brief Header file for the boiler firmware. The boiler firrmware is intended for temperature characterizations.
 * 2 modes are possible, verifier(V) and prover(P).
 * The verifier is sending continously frames, and the prover turns on reception intermittently according to a given Duty Cycle.
 * The Duty Cycle can be set by changing the sleep_time variable (= sleep time between two receptions) of the device.
 * The default sleep_time when the device is turned on is defined in SLEEP_TIME. Otherwise this parameter can be changed though the serial port.
 * Send '1[new_sleep_time]' to modify the value.
 * Send '0' to both P and V to start a boiling process; the prover will switch to a duty cyle of 100% for a maiximum temeprature gradient.
 * See the platform documentation and related papers for details.
 * @todo documentation + interfacing with main anchor/tags projects
 * @see https://github.com/Hedwyn/SecureLoc
 */

#ifndef BOILER_H
#define BOILER_H

#include <SPI.h>
#include <DecaDuino.h>

/* identifier */
#ifndef NODE_ID
  #define NODE_ID 1
#endif

#if (NODE_ID == 2)
  #define VERIFIER 1
  #define PROVER 0
#else // (NODE_ID == 1)
  #define VERIFIER 0
  #define PROVER 1
#endif

/* TImebase parameters */
#define DW1000_TIMEBASE 15.65E-12
#define DW1000_TIMEBASE_MS 60E6
#define TIMEOUT 1000
#define DUTY_CYCLE 25 //in %
#define FRAME_TIME_US 4180
//#define SLEEP_TIME FRAME_TIME_US * (100 / DUTY_CYCLE)
#define SLEEP_TIME 0//413820
/* Serial parameters */
#define ASCII_NUMBERS_OFFSET 48


#define BUFFER_LEN 128

/* states */
#define IDLE 0
#define USB_SERIAL 1
#define PING 2
#define PONG 3

/* RX-TX parameters */
#define PLENGTH 4096

/* DB parameters */
#define CHALLENGE_LENGTH_MS 6000
#define CHALLENGE_LENGTH_SYSTEM_CLK_UNITS CHALLENGE_LENGTH_MS * DW1000_TIMEBASE_MS

/* skew calculations */
#define N_SAMPLES 50


void setup_DB();
void loop_DB();
void send_db_results();


#endif
