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
 * @file Anchor_c.h
 * @author Baptiste Pestourie
 * @date 2019 December 1st
 * @brief Header file for the cooperative anchor firmware. This firmware is intended for DecaWino chips.
 * Anchors are fixed stations performing ranging with mobile tags.
 * The cooperative anchor firmware allow an anchor to design a tag to participate in a verification process. See the platform documentation for details.
 * @see https://github.com/Hedwyn/SecureLoc
 */

#ifndef ANCHOR_C_H
#define ANCHOR_C_H

#include <SPI.h>
#include <DecaDuino.h>
#include <math.h>

#define EXTENDED 1  /**< Enables extended DATA mode- sends an extended set of PHY data to RPI (TODO)*/
#define ALOHA 0 /**< Enables ALOHA scheduling- check any documentation on ALOHA for further information */
#define ALOHA_COLLISION_DELAY 20  /**< Delayed to wait when detecting collisions in ALOHA mode*/
#define DMAX 10  /**< Maximum distance considered as realistic - should be adapted to the environment*/
#ifndef NB_ANCHORS
  #define NB_ANCHORS 4/**< Default total number of anchors, should be defined during compilation*/
#endif

#ifndef NODE_ID
  #define NODE_ID 1/**< Default tag ID. Should be defined during compilation when deploying*/
#endif

#define MASTER_ID 1 /**< Enables Master anchor mode. The Master anchor is responsible for the cooperative operations and the TDMA watchdog*/

#if (NODE_ID == MASTER_ID)
  #define MASTER /**< Enables Master anchor mode. The Master anchor is responsible for the cooperative operations and the TDMA watchdog*/
#endif

#define SLOT_LENGTH 200000 /**< TDMA slot length, in microseconds*/
#define SLOT_LENGTH_MS (SLOT_LENGTH / 1000) /**< TDMA slot length, in milliseconds*/
#define IN_US 1E6 /**< Second to microsecond conversion*/

//#define _DEBUG_   //comment to disable debug mode
#ifdef _DEBUG_
  #define DPRINTF  Serial.print/**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTF(format, args...) ((void)0)
#endif

#ifdef _DEBUG_
  #define DPRINTFLN  Serial.println/**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTFLN(format, args...) ((void)0)
#endif



#define ASCII_NUMBERS_OFFSET 48/**< Char to printable value conversion for serial communications*/

#define AIR_SPEED_OF_LIGHT 299700000.0 /**< Speed of light constant to extract distances from time-of-flight measurements*/
#define DW1000_TIMEBASE 15.65E-12 /**< Resolution of the system clock - value of 1 bit in s*/
#define DW1000_TIMEBASE_US 15.65E-6 /**< Resolution of the system clock - value of 1 bit in us*/
#define CALIBRATION 0.9 /**< Calibration coefficient to apply to the distance measurements*/
#define SPEED_COEFF AIR_SPEED_OF_LIGHT*DW1000_TIMEBASE*CALIBRATION /**< Calibrated speed of light constantt*/

/* watchdogs */

#define TX_TIMEOUT 10 /**< Watchdog for failed transmission that never complete*/
#define ACK_TIMEOUT SLOT_LENGTH_MS /**< Acknowledgment watchdog in TWR protocol*/
#define DATA_TIMEOUT SLOT_LENGTH_MS /**< DATA watchdog in TWR protocol*/
#define START_TIMEOUT (NB_ANCHORS * SLOT_LENGTH_MS) /**< START watchdog for TDMA scheduling - triggered when previous anchor stayed quiet*/



/* Ranging FSM states */

#define TWR_ENGINE_STATE_INIT 0/**<Default starting state*/
#define TWR_ENGINE_STATE_IDLE 1/**< Handles TDMA/Aloha scheduling in-between TWR protocols*/
#define TWR_ENGINE_STATE_SERIAL 2/**< Handles serial communications with the host RPI*/
#define TWR_ENGINE_PREPARE_RANGING 3/**< When reaching the attributed TDMA slot, starts TWR protocol*/
#define TWR_ENGINE_STATE_SEND_START 4/**< Sends START to the target tag*/
#define TWR_ENGINE_STATE_WAIT_ACK 5/**< ACK polling - back to INIT if timeout */
#define TWR_ENGINE_STATE_WAIT_DATA_REPLY 6/**< DATA polling - back to INIT if timeout */
#define TWR_ENGINE_STATE_EXTRACT_T2_T3 7/**< Computes time-of-flight & distance */
#define TWR_ENGINE_STATE_SEND_DATA_PI 8/**< Sends the distance & other PHY data to host RPI */


/* TWR State & parameters */
#define TWR_ON_GOING 0/**< Ret value for main loop - TWR protocol is still running */
#define TWR_COMPLETE 1/**< Ret value for main loop - TWR protocol complete */
#define DIFFERENTIAL_TWR 1/**<If set, all anchors will compute the distance on each start frame using a diffential calculation*/
#define PLATFORM_LENGTH 3.04/**< Length of the rectangle formed by the anchor (anchor 1 -> anchor 2) */
#define PLATFORM_WIDTH 3.04/**< Width of the rectangle formed by the anchor (anchor 1 -> anchor 4) */
#define T23 100000000 /**< When delayed send is enabled, waiting time between ACK and DATA frame*/
#define SKEW_CORRECTION 1/**< Applies a correction on the ToF calculation based on the clock skew with the target tag*/

/* frame types */
#define TWR_MSG_TYPE_START 1  /**< START frame header*/
#define TWR_MSG_TYPE_ACK 2 /**< ACK frame header*/
#define TWR_MSG_TYPE_DATA_REPLY 3 /**< DATA frame header*/
#define NB_ROBOTS 1/**< Total number of mobile tags*/

/* Cooperative */
#define COOPERATIVE 0 /**< Enables cooperative mode - see documentation for further details*/
#if (COOPERATIVE)
  #define NB_GHOST_ANCHORS 1 /**< Total number of ghost anchors in cooperative mode*/
#else
  #define NB_GHOST_ANCHORS 0
#endif

#define NB_TOTAL_ANCHORS (NB_ANCHORS + NB_GHOST_ANCHORS) /**< Total number of anchors including ghost anchors*/

/** The position of a given tag identified by its id, in the (x,y,z)
 coordinates system */
typedef struct Tag_position{
  byte *tagID; /**<pointer to the tag ID in the tag ID list */
  float x;/**<Coordinates on (anchor1 - anchor2) axis */
  float y;/**<Coordinates on (anchor1 - anchor4) axis */
  float z;/**<Altitude */
}Tag_position;

/** The position of a given tag identified by its id, in the (x,y,z)
 coordinates system */
typedef struct Anchor_position{
  byte *anchorID; /**<pointer to the anchor ID in the anchor ID list */
  float x;/**<Coordinates on (anchor1 - anchor2) axis */
  float y;/**<Coordinates on (anchor1 - anchor4) axis */
  float z;/**<Altitude */
}Anchor_position;

/** @brief process serial frames containing tag positions
  * @author Baptiste Pestourie
  * @date 2020 March 1st
*/
void serial_process_tag_position();

/** @brief DecaWino setup for anchor mode
  * @author Baptiste Pestourie
  * @date 2019 December 1st
*/
void anchor_setup();

/** @brief RX/TX setup for DW1000 in anchor mode.
  * Sets the channel, preamble length, preamble code and PRF.
  * @author Baptiste Pestourie
  * @date 2019 December 1st
*/
void anchor_RxTxConfig();

/** @brief Displays an 8-bytes array on the serial port
  * @author Baptiste Pestourie
  * @date 2019 December 1st
*/
void print_byte_array(byte b[8]);

/** @brief Checks if two 8-bytes array are equal
  * @author Baptiste Pestourie
  * @date 2019 December 1st
  * @param 8-bytes array (ID format)
  * @returns True if all the elements in both arrays are equal
*/
int byte_array_cmp(byte b1[8], byte b2[8]);

/** @brief Computes the time elasped since the timestamp provided, based on the DWM1000 system clock 
  * @author Baptiste Pestourie
  * @date 2020 March 1st
  * @param timestamp the reference timestamp for the elasped time
  * @return elapsed time as a double, in microseconds
*/
double compute_elapsed_time_since(uint64_t timestamp);

/** @brief computes the distance in differential Two-Way Ranging mode
  * Used when the anchor is listening to the TWR of another anchor.
  * @author Baptiste Pestourie
  * @date 2020 March 1st
*/
void compute_DTWR();

/** @brief computes the distance in direct Two-Way Ranging mode
  * Used when the anchor performing the TWR protocol itself.
  * @author Baptiste Pestourie
  * @date 2020 March 1st
*/
void compute_DWR();

/** @brief Finds the index of a given tag ID in the tag ID list
  * @author Baptiste Pestourie
  * @date 2019 December 1st
  * @param b1 8-byte array
  * @param b2 8-byte array
  * @return the index of the tag ID if found, -1 otherwise
*/
int get_tag_idx(byte tag_ID[8]);

/** @brief One iteration of the main FSM loop for TWR, with default ID parameters in header file
  * @author Baptiste Pestourie
  * @date 2019 December 1st
  * @returns TWR state (/!\ different from the FSM state))
*/
int anchor_loop();

/** @brief One iteration of the main FSM loop for TWR
  * @author Baptiste Pestourie
  * @date 2019 December 1st
  * @param myID anchor ID to use
  * @param myNextAnchorID ID of the following anchor
  * @returns TWR state (/!\ different from the FSM state))
*/
int anchor_loop(byte *myID, byte *myNextAnchorID);


#endif
