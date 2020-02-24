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
 * @file SkewAuthentication.h
 * @author Baptiste Pestourie
 * @date 2020 February 1st
 * @brief Header file for the Skew Authentication firmware. This firrmware has 2 modes, prover(P) and verifier(V).
 * The prover is authenticated based on its skew signature. Send '0' to both nodes to start the authentication process.
 * The two nodes will exchange frames at maximum speed such as inducing a fast temperature gradient on P.
 * V characterizes P's skew throughout the protocol. The signature is sentto the host laptop or RPI on the serial port.
 * When authentication processes are not running this firmware is similar to Boiler.
 * See the platform documentation and related papers for details.
 * @todo documentation + interfacing with main anchor/tags projects
 * @see https://github.com/Hedwyn/SecureLoc
 */

#ifndef SKEW_AUTHENTICATION_H
#define SKEW_AUTHENTICATION_H

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
#define AIR_SPEED_OF_LIGHT 299700000.0
#define DW1000_TIMEBASE 15.65E-12
#define CALIBRATION 0.9
#define SPEED_COEFF 4.2255E-3//AIR_SPEED_OF_LIGHT*DW1000_TIMEBASE*CALIBRATION
#define DW1000_TIMEBASE_MS 60E6
#define AIR_SPEED_OF_LIGHT 299700000
#define DUTY_CYCLE 25 //in %
#define FRAME_TIME_US 4180
#define AVERAGE_LENGTH 50

//#define SLEEP_TIME FRAME_TIME_US * (100 / DUTY_CYCLE)
#define SLEEP_TIME 37620
/* Serial parameters */
#define ASCII_NUMBERS_OFFSET 48

#if (VERIFIER)
  #define TIMEOUT 3//VERIFIER?2:10
#else
  #define TIMEOUT 10
#endif

#define BUFFER_LEN 128

/* states */
#define PING 0
#define PONG 1

/* RX-TX parameters */
#define PLENGTH 4096
#define LONG_PREAMBLE 4096
#define SHORT_PREAMBLE 128
#define CHANNEL 1
#define PAYLOAD_LENGTH 1

/* Challenge parameters */
#define N_TOTAL_FRAMES 2000
#define SIGNATURE_LENGTH (N_TOTAL_FRAMES / AVERAGE_LENGTH)
#define T23 38000000 //21000000
#define GUARD_TIME 3000000
#define LOCALIZE 0

/* distance calculations */
#define DMIN 0
#define DMAX 10

/* skew correction */
#define SKEW_CORRECTION 1
#define T_REF 41.2 /* reference temperature used for calculations */
#define SKEW_CORRECTION_COEFF 0.17 // should be adjusted for every tag



void setup_DB();
void loop_DB();
void send_db_results();


#endif
