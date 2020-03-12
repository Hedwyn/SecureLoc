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
 * @file Tag.cpp
 * @author Baptiste Pestourie
 * @date 2019 December 1st
 * @brief Source file for the cooperative anchor firmware. This firmware is intended for DecaWino chips.
 * Tags are the mobile nodes localized by the anchors.
 * @see https://github.com/Hedwyn/SecureLoc
 */


#include "tag.h"
#include "anchor_c.h"



static DecaDuino decaduino;/**< Instance for all DWM1000-related operations*/
static int state;/**< Previous state variable for the FSM- used to keep track of state changes*/
static int previous_state; /**< Next state variable for the FSM - state to go after a serial call*/

/* UWB frames */
static uint8_t txData[128];/**< Emission buffer */
static uint8_t rxData[128];/**< Reception buffer */
static uint16_t rxLen;/**< Reception buffer length*/

/* IDs */
static byte myID[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, NODE_ID};/**< Node's tag ID */
static byte targetID [8]; /**< Buffer for the target ID field in RX frames */
static byte anchorID [8];  /**< Buffer for the anchor ID field in RX frames */
static byte sleep_slots; /**< Number of slots to sleep when turning to sleep mode */


/* timestamps */
static uint64_t t2 = 0, t3,ts_ghost_anchor;  /**< Timestamp for TWR process */
static int ranging_timer;/**<Timer for the ranging duration*/ 

/* cooperative methods */
static byte next_target_id[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00}; /**< ID of the next target when acting as an anchor */
static byte ghost_anchor_id[8] ={0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00}; /**< ID tu claim when acting as an anchor */
static byte next_anchor_id[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00};/**< ID to call when acting as an anchor */
static Tag_position my_position = {.tagID = myID, .x = 0.0, .y = 0.0, .z = 0.0};
static const char * states[50]=
{
"Init",
"Ghost Anchor",
"Rx ON",
"Wait Start",
"Send ACK",
"Send Data"
};/**< States name for the debug output */

int main() {
	tag_setup();
	while (1) {
		loop();
		yield();
	}

	return(0);
}


void tag_setup() {
  delay(1000);
  pinMode(13, OUTPUT);
  pinMode(14, OUTPUT);
  //SPI.setSCK(13);
  SPI.setSCK(14);
  //set for anchors C and D
  //use pin 14 for A and B by uncommenting code lines above
  if ( !decaduino.init() ) {
    while(1) {
      digitalWrite(13, HIGH);
      delay(50);
      digitalWrite(13, LOW);
      delay(50);
    }
  }

	tag_RxTxConfig();
  state = TWR_ENGINE_STATE_INIT;
  previous_state = state;
}

// TODO : decaduino configure

void tag_RxTxConfig() {
	decaduino.setRxBuffer(rxData, &rxLen);
}

void loop() {
  if (state != previous_state) {
    Serial.print("$State: ");
    Serial.println(states[state]);
  }

	previous_state = state;
  switch (state) {

    case TWR_ENGINE_STATE_INIT:
		/* Default starting state */
      state = TWR_ENGINE_STATE_RX_ON;

      break;

		case TWR_ENGINE_GHOST_ANCHOR:
			/* in Cooperative mode, state for ghost anchor operations.
			The tag will switch to this state when designated by an anchor */
			state = TWR_ENGINE_STATE_INIT;
			Serial.println("Switching to ghost anchor mode");
			Serial.print("Ghost Anchor ID: ");
			Serial.println(ghost_anchor_id[7]);
			Serial.print("Number of sleep slots:");
			Serial.println((int) sleep_slots);
			anchor_setup();
			while (anchor_loop(ghost_anchor_id, next_anchor_id) != TWR_COMPLETE );
			tag_setup();
			Serial.println("Ghost Anchor Job Complete");
			ghost_anchor_id[7] = 0;
			break;

    case TWR_ENGINE_STATE_RX_ON:
			/* sleeping until next slot */
			while (decaduino.getSystemTimeCounter() - t2 < (SLOT_LENGTH / (DW1000_TIMEBASE * IN_US))  - GUARD_TIME) {
				delayMicroseconds(30);
			}
			/* Turns on reception and checks if the tag has been designated as ghost anchor in the previous ranging */
      decaduino.plmeRxEnableRequest();
      state = TWR_ENGINE_STATE_WAIT_START;
			if (COOPERATIVE && (ghost_anchor_id[7] != 0)  && (decaduino.getSystemTimeCounter() > ts_ghost_anchor + sleep_slots * SLOT_LENGTH) ) {
				//if (ghost_anchor_id[7] != 0) {// && (next_target_id[7] != 0)) {
					state = TWR_ENGINE_GHOST_ANCHOR;
				}
			else {
				delayMicroseconds(100);
			}
      break;

    case TWR_ENGINE_STATE_WAIT_START:
			/* Polling state for start request from anchors */
      if ( decaduino.rxFrameAvailable() ) {
        /* START format : START | targetID | anchorID */
    
        /*timestamping ranging start */
        ranging_timer = micros();
        if ( rxData[0] == TWR_MSG_TYPE_START ) {
          Serial.println("$Start received");
          for (int i=0; i<8; i++){
           targetID [i] = rxData[i+1];
           anchorID [i] = rxData[i+9];
          }
					Serial.print("$Anchor ID: ");
					Serial.println((int)anchorID[7]);
          if ( byte_array_cmp(targetID, myID) ) {
            t2 = decaduino.getLastRxTimestamp();
            state = TWR_ENGINE_STATE_SEND_ACK;
						if (anchorID[7] == MASTER_ID) {
							// getting position
							if (rxData[25] == 1) {
								my_position.x = *( (float *) (rxData + 26));
								my_position.y = *( (float *) (rxData + 30));
								my_position.z = *( (float *) (rxData + 34));
								Serial.println("Current position: ");
								Serial.println(my_position.x);
								Serial.println(my_position.y);
								Serial.println(my_position.z);
							}
							DPRINTFLN("Received ghost anchor request from Master");
							ghost_anchor_id[7] = rxData[37];
							next_anchor_id[7] = rxData[38];
							sleep_slots = rxData[39];
							ts_ghost_anchor = t2;
						}
          }
          else{
              DPRINTFLN("Not for me" );
              state = TWR_ENGINE_STATE_RX_ON;
          }

					/* Control parameters for cooperative methods */
        }
        else {
          DPRINTFLN("Not a START frame");
          state = TWR_ENGINE_STATE_RX_ON;
        }
      }
      break;

    case TWR_ENGINE_STATE_SEND_ACK:
			/* After receiving a START, sends an acknowledgment as defined in TWR protocol.
			Memorizes acknowledgment sending time */
      txData[0] = TWR_MSG_TYPE_ACK;           
      for( int i =0; i<8 ; i++){
        txData[1+i] = anchorID[i];
        txData[9+i] = targetID[i];
      }
      decaduino.pdDataRequest(txData, 18,1,t2 + T23);
			//decaduino.pdDataRequest(txData, 18);
      while (!decaduino.hasTxSucceeded());
      /* roughly calculating time elasped since time reception */
      Serial.print("$ Time elapsed bewteen ACK and START:");
      Serial.println(micros() - ranging_timer);
      t3 = decaduino.getLastTxTimestamp();
      state = TWR_ENGINE_STATE_SEND_DATA_REPLY;
      break;


    case TWR_ENGINE_STATE_SEND_DATA_REPLY:
			/* Sending last frame of TWR protocol, with the 2 timestamps measured */
      txData[0] = TWR_MSG_TYPE_DATA_REPLY;
      decaduino.encodeUint64(t2, &txData[17]);
      decaduino.encodeUint64(t3, &txData[25]);
      decaduino.pdDataRequest(txData, 33);
			Serial.print("$Temperature: ");
			Serial.println(decaduino.getTemperature());
      while (!decaduino.hasTxSucceeded());
      Serial.print("TWR duration: ");
      Serial.println(micros() - ranging_timer);
      state = TWR_ENGINE_STATE_INIT;
      break;

    default:
      state = TWR_ENGINE_STATE_INIT;
      break;
  }
}
