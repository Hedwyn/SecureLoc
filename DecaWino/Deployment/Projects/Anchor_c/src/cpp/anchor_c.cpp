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
 * @file Anchor_c.cpp
 * @author Baptiste Pestourie
 * @date 2019 December 1st
 * @brief Source file for the cooperative anchor firmware. This firmware is intended for DecaWino chips.
 * Anchors are fixed stations performing ranging with mobile tags.
 * The cooperative anchor firmware allow an anchor to design a tag to participate in a verification process. See the platform documentation for details.
 * @see https://github.com/Hedwyn/SecureLoc
 */


#include "anchor_c.h"
/* libraries */

static DecaDuino decaduino; /**< Instance for all DWM1000-related operations*/


/* RX-TX buffers */
static uint8_t rxData[128]; /**< Reception buffer */
static uint8_t txData[128]; /**< Emission buffer */
static uint16_t rxLen; /**< Reception buffer length*/

/* state machine iterators */
static int state = TWR_ENGINE_STATE_INIT; /**< Current State variable for the FSM*/
static int previous_state = TWR_ENGINE_STATE_IDLE; /**< Previous state variable for the FSM- used to keep track of state changes*/
static int next_state; /**< Next state variable for the FSM - state to go after a serial call*/
static const char * states[50]=
{
"Init",
"Idle",
"Serial",
"Prepare Ranging",
"Send Start",
"Wait ACK",
"WAIT DATA",
"Extract Timestamps",
"Send to Pi",
};/**< States names for the debug output*/

/* RX IDs - when receiving frames from tags or anchors */
static byte anchorsID[NB_ANCHORS][8];
static Anchor_position anchorsPositions[4] = {
  {anchorsID[0], 0 , 0 , 0},
  {anchorsID[1], 0 , PLATFORM_LENGTH , 0},
  {anchorsID[2], PLATFORM_WIDTH , PLATFORM_LENGTH , 0},
  {anchorsID[3], PLATFORM_WIDTH , 0 , 0}
};
static Anchor_position myPosition;
static byte targetID[][8]= { {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x01},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x02}};/**< Mobile tags IDs*/
static byte rxID[8];/**< Recipient ID buffer when receving a frame*/
static byte nextTarget[8]; /**< Buffer for the ID of the next tag to localize*/
static int next_target_idx = 0;  /**< Index of the next tag to localize ID in the tag's ID list targetID[]*/


/* Anchor ID's */
static byte MYID[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, NODE_ID};  /**< Node's anchor ID */
static byte anchorID[8]; /**< Buffer for the anchor ID field in Rx frames */
static byte MY_NEXT_ANCHOR_ID[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}; /**< ID of the following anchor in the TDMA scheduling. Filled bu getID() */
static byte nextAnchorID[8] ={0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}; /**< Buffer for the following anchor ID field in Rx frames */
static byte *verifierID;/**< Points to the identifier of the verifier ID for the current ranging protocol */

/* Two-Way Ranging protocol   */
static unsigned long timeout; /**< Timeout variable for all the watchdogs (on Acknowledgment/DATA/Start frames) */
static bool has_timedout; /**< Whether the last ranging process has timed out or not */
static uint64_t t1, t2, t3, t4; /**< Timestamp for Two-Way Ranging */
static int32_t tof; /**< Time-of-flight calculated after TWR protocol */
static int32_t tof_skew;  /**< Time-of-flight calculated after TWR protocol after skew correction */
static float distance; /**< Distance calculated after TWR protocol */
static float distance_skew;/**< Distance calculated after TWR protocol after skew correction */
static int has_position_been_resfreshed = 0;
static int differential_twr = DIFFERENTIAL_TWR;
static uint64_t tof_to_anchors[NB_ANCHORS];
static int ranging_timer;/**<Records the duration of a single TWR protocol, in us */

/* Serial communications */
static char serial_command; /**< Serial command (on one digit) received on the last serial communication */
static char target_id; /**< Target Anchor ID for a given serial command, e.g. inter-anchor ranging */
static bool is_target_anchor; /**< whether the target of the current ranging is an anchor or not */

/* Scheduling */
static int aloha_delay; /**< In Aloha scheduling mode, the delay to wait after a collision*/
static bool my_turn; /**< Switches true when the anchor can start a ranging process */
static uint64_t slot_start; /**< Timestamp for the beginning of the next TDMA slot. This timestamp is used by a delayed send */
static uint64_t last_start_frame; /**< Timestamp of the last start frame received, required to calculate the start timestamp of the next TDMA in slot_start */
static int delayed; /**< Boolean, true if delayed transmissions are enabled */

/* Cooperative methods */
/** Ghost Anchor Request structure sent to designated tags in cooperative protocols.
  * The tag receiving this will have to localize another tag at a given time
  * The designated tag usesa specific anchor ID for that purpose
  */
struct control_frame{
  byte anchor_id; /**< ID that the designated tag is going to use to its anchor turn */
  int target_idx; /**<  ID of the target that the designated tag should localize*/
  byte next_anchor_id; /**< ID of the next anchor to call during the designated tag verification process*/
  byte sleep_slots; /**< Number of slots that the designated tag should sleep before starting the verification process*/
};
static control_frame next_ghost_anchor = {.anchor_id = 0, .target_idx = 0, .next_anchor_id = 0, .sleep_slots = 0}; /**< Ghost anchor request sent to designated tags */
Tag_position tag_positions[NB_ROBOTS];

#ifdef MASTER
void getNextGhostAnchor() {
  Serial.println("I'm Master, sending control frame");
  next_ghost_anchor.anchor_id = NB_TOTAL_ANCHORS;
  next_ghost_anchor.target_idx = next_target_idx;
  next_ghost_anchor.next_anchor_id = 1;
  next_ghost_anchor.sleep_slots = NB_TOTAL_ANCHORS;//+ next_ghost_anchor.anchor_id - 2;
}
#endif

void serial_process_tag_position() {
  int idx = 0, found = 0;
  byte tag_id;
  tag_id = (byte) Serial.parseInt();
  while ((idx < NB_ROBOTS) && (!found)) {
    if (tag_id == targetID[idx][7]) {
      found = 1;
    }
    else {
      idx++;
    }
  }
  if (!found) {
    Serial.println("Unknown tag. Dismissing command");
  }
  else {
    tag_positions[idx].tagID = targetID[idx];
    tag_positions[idx].x = Serial.parseFloat();
    tag_positions[idx].y = Serial.parseFloat();
    tag_positions[idx].z = Serial.parseFloat();
    //TODO: handle improper formatting
  }
}



/** @brief Gets the anchor ID from header file configuration in default mode
  * @author Baptiste Pestourie
  * @date 2019 December 1st
*/
void getID() {
	#ifdef NODE_ID
    /* setting up every anchor ID */
    for (int i = 0; i < NB_ANCHORS; i++) {
      memcpy( (void *) &anchorsID[i], (const void *) MYID, 7 );
      /* changing last byte */
      anchorsID[i][7] = i + 1;
    }
		/* setting up anchor id */
		MYID[7] = NODE_ID;

		/* setting up next anchor ID */
		#ifdef NB_TOTAL_ANCHORS
		/* checking if this anchors has the highest ID */
			if (NODE_ID == NB_TOTAL_ANCHORS) {
				/* the next anchor is the first one */
				MY_NEXT_ANCHOR_ID[7] = 1;
			}
			else {
				MY_NEXT_ANCHOR_ID[7] = NODE_ID + 1;
			}
		#else
			MY_NEXT_ANCHOR_ID[7] = NODE_ID + 1;
		#endif
	#else
		DPRINTFLN("ANCHOR id has not been defined during compilation. Default ID : 0 \n");
	#endif
}




/** @brief Attributes an ID to the anchor
  * @param id - The Id to give to the anchor
  * @author Baptiste Pestourie
  * @date 2019 December 1st
*/
void getID(byte id) {
  MYID[7] = id;
}

void print_byte_array(byte b[8]) {
	/* print byte array as an hex string */
	int i;
	for (i = 0; i < 8; i ++) {
		if (b[i] < 16) {
			/* first digit is 0; printing 0 explicitly */
			Serial.print("0");
		}
		Serial.print(b[i],HEX);
	}
}

int get_next_target_idx(byte tag_ID[8]) {
  int idx = 0;
  while (targetID[idx][7] != tag_ID[7]) {
    idx++;
  }
  Serial.print("$ Tag IDx:");
  Serial.println(idx);
  return(idx);
}

int byte_array_cmp(byte b1[8], byte b2[8]) {
  /* checks for equality between two byte array */
	int i = 0, ret = 1;
	for (i = 0; i <8; i++) {
		if (b1[i] != b2[i]) {
			ret = 0;
			break;
		}
	}
	return(ret);
}


void compute_tof_to_anchors() {
  long tof;
  /* getting the position of this anchors */
  memcpy((void *) &myPosition, (const void *) &anchorsPositions[NODE_ID -1], sizeof(Anchor_position));
  Serial.println("My position is: ");
  Serial.println(myPosition.x);
  Serial.println(myPosition.y);

  /* computing ToF to anchors */
  for (int i = 0; i < NB_ANCHORS; i ++) {
    tof_to_anchors[i] = 100;
  }
  
}

double_t compute_elapsed_time_since(uint64_t timestamp) {
  double elasped_time;
  elasped_time = DW1000_TIMEBASE_US * (double) (decaduino.getSystemTimeCounter() - timestamp);
  return(elasped_time);
}

void anchor_setup() {
  delay(1000);
  pinMode(13, OUTPUT);
  SPI.setSCK(14);

  if ( !decaduino.init() )  {
    while(1) {
			/* blinking led */
      digitalWrite(13, HIGH);
      delay(50);
      digitalWrite(13, LOW);
      delay(50);
    }
  }
  getID();

  /* Setting RX-TX parameters */
  anchor_RxTxConfig();

  /* computing ToF to other anchors */
  compute_tof_to_anchors();

  /* getting the starting timestamp for timeouts */
  timeout = millis() + START_TIMEOUT + (NODE_ID - 1) * SLOT_LENGTH * 1E-3;
  DPRINTFLN("Starting");

  /* The master anchor gets the first target to localize in the targets list */
  #ifdef MASTER
    for (int i = 0; i < NB_ROBOTS; i++) {
      tag_positions[i].tagID = targetID[i];
    }
    state = TWR_ENGINE_STATE_SEND_START;
  #else
    state = TWR_ENGINE_STATE_INIT;
    /* enabling reception */
    decaduino.plmeRxEnableRequest();
  #endif
  state = TWR_ENGINE_STATE_INIT;
}

void anchor_RxTxConfig() {
	decaduino.setRxBuffer(rxData, &rxLen);
}


int anchor_loop() {
  /* using default parameters */
  return(anchor_loop(MYID, MY_NEXT_ANCHOR_ID));
}

int anchor_loop(byte *myID, byte *myNextAnchorID) {
  int ret = TWR_ON_GOING;
  if (state != previous_state) {
    DPRINTF("$State: ");
    DPRINTFLN(states[state]);
  }
  previous_state = state;

  switch (state) {
    case TWR_ENGINE_STATE_INIT:
      /** Starting state of the FSM. CHecks for timeouts and restart a TWR cycle for the Master anchor.
      * For the others, skip directly to IDLE state */
      #ifdef MASTER
      if (myID[7] == MASTER_ID) {
        timeout = millis() + START_TIMEOUT + SLOT_LENGTH * 1E-3;
        Serial.println("$ Master Timeout Set");
      }
      else {
        timeout = millis() + 2 * START_TIMEOUT + NODE_ID * SLOT_LENGTH * 1E-3;
      }
      #else
        timeout = millis() + 2 * START_TIMEOUT + NODE_ID * SLOT_LENGTH * 1E-3;
      #endif
    
      state = TWR_ENGINE_STATE_IDLE;
      break;

		case TWR_ENGINE_STATE_IDLE:
      /* Scheduling state. In Aloha, goes straight to ranging mode.
      In TDMA, checks for the frame of the previous anchor and calculates the starting timestamp of the next ranging from the slot length */
      if (ALOHA) {
        state = TWR_ENGINE_PREPARE_RANGING;
				break;
      }
			if ((millis() > timeout) || (NB_ANCHORS == 1)){
				/* the DATA frame of the previous frame has never been received. Forcing a new cycle */
				state = TWR_ENGINE_PREPARE_RANGING;
        delayed = 0;
        Serial.println("$Timeout- Starting new cycle");
        /* pointing verifier ID to our own ID */
        verifierID = myID;
        my_turn = true;
        decaduino.plmeRxDisableRequest();
				break;
			}

      if ( decaduino.rxFrameAvailable() ) {
        DPRINTFLN("$ Frame received");
				/* checking START frames for anchor ranging request */
				if ( rxData[0] == TWR_MSG_TYPE_START ) {
          DPRINTFLN("$ Start received");
					/* extracting target ID */
					for (int i = 0; i < 8; i++) {
						nextTarget[i] = rxData[i + 1];
            anchorID[i] = rxData[i + 9];
            nextAnchorID[i] = rxData[i+17];
					}
          Serial.print("$ Next Target= ");
          print_byte_array(nextTarget);
          Serial.println();

					DPRINTF("$ID received:");
					DPRINTFLN((int) nextAnchorID[7] );
					DPRINTF("$My ID ");
					DPRINTFLN((int) myID[7]);
				
          if (byte_array_cmp(nextAnchorID, myID))
          {
            last_start_frame = decaduino.getLastRxTimestamp();
            Serial.println("$It's my turn");
            my_turn = true;
            Serial.print("$ID of the next anchor: ");
            print_byte_array(myNextAnchorID);
            Serial.println();

            /* pointing verifier ID to our own ID */
            verifierID = myID;
            #ifndef MASTER
              next_target_idx = get_next_target_idx(nextTarget);
            #endif
            state = TWR_ENGINE_PREPARE_RANGING;
            slot_start =  last_start_frame + (SLOT_LENGTH / (DW1000_TIMEBASE * IN_US) );
            delayed = 1;
          }
          else if (differential_twr) {
            /* calculating the starting time for the emitting anchor */
            t1 =  decaduino.getLastRxTimestamp() - tof_to_anchors[NODE_ID - 1];

            /* pointing the verifier ID to the current verifier */
            verifierID = anchorID;

            /* enabling reception for the incoming ACK */
            decaduino.plmeRxEnableRequest();
            timeout = millis() + ACK_TIMEOUT;
            state = TWR_ENGINE_STATE_WAIT_ACK;    

            /* going straight to wait Ack state */
            state = TWR_ENGINE_STATE_WAIT_ACK;
          }


        } 

        if (state == TWR_ENGINE_STATE_IDLE) {
          /* re-enabling reception if we are still waiting for a START */
          decaduino.plmeRxEnableRequest();
        }
      }

      break;

    case TWR_ENGINE_STATE_SERIAL:
      /* State for Serial communications.
      Handle commands from the host */
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
            Serial.println("$ [Serial command]: anchor ranging request");
            // reading anchor ID
            target_id = Serial.read();
            if ((target_id == -1) || (target_id == '\r') || (target_id == '\n') ){
              Serial.println("$ Dismissing command: no ID received");
            }
            else if ( (serial_command < ASCII_NUMBERS_OFFSET) || (serial_command > ASCII_NUMBERS_OFFSET + 9)){
              Serial.println("$ Dismissing command: invalid ID received");
            }
            else {
              next_target_idx = (int) (NB_ROBOTS + target_id - ASCII_NUMBERS_OFFSET) ;
              is_target_anchor = true;
            }
            break;

          case 1:
            Serial.println("$ Tag position received ");
            if (NODE_ID == MASTER_ID) {
              serial_process_tag_position();
              has_position_been_resfreshed = 1;
            }
            else {
              Serial.println("Only the master anchor deals with tag positions");
            }
            break;

          case 2:
            Serial.println("$ Starting PKCE");
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

    case TWR_ENGINE_PREPARE_RANGING:
    /** Checks for serial commands, otherwise proceeds to start the ranging process */

  		if (ALOHA) {
  			delay(aloha_delay);
  		}
      if (Serial.available() > 0) {
        state = TWR_ENGINE_STATE_SERIAL;
        next_state = TWR_ENGINE_STATE_SEND_START;
      }
      else {
      	state = TWR_ENGINE_STATE_SEND_START;
      }
      // getting the index of the next robot to localize
      #ifdef MASTER
        next_target_idx = (next_target_idx + 1) % NB_ROBOTS;
      #endif
      break;

    case TWR_ENGINE_STATE_SEND_START:
    /** Sending a ranging request (START frame) to the target tag */
			/* Frame format : tagID | anchorID | nextAnchorID  */
      #ifdef MASTER
        if (myID[7] == MASTER_ID) {
          getNextGhostAnchor();
          DPRINTFLN("$ [Master Anchor] Getting next ghost anchor ID");
          DPRINTF("");
        }
      #endif
			txData[0] = TWR_MSG_TYPE_START;
      for(int i=0; i<8; i++){
        txData[1+i]=targetID[next_target_idx][i];
        txData[9+i]=myID[i];
        txData[17+i]=myNextAnchorID[i];
      }


      if (NODE_ID == MASTER_ID) {
        // informing  the tag of its gposition /!\ dirty
        Serial.print("Sending position to tag ");
        Serial.println(next_target_idx);
        Serial.println(tag_positions[next_target_idx].x);
        Serial.println(tag_positions[next_target_idx].y);
        Serial.println(tag_positions[next_target_idx].z);
        if (has_position_been_resfreshed) {
          txData[25] = 1; //Enabling position
          has_position_been_resfreshed = 0;
        }
        else {
          txData[25] = 0;
        }
        *( (float *) (txData + 26)) = tag_positions[next_target_idx].x ;
        *( (float *) (txData + 30)) = tag_positions[next_target_idx].y ;
        *( (float *) (txData + 34)) = tag_positions[next_target_idx].z ;

        // control frame for cooperative approaches
        txData[38]= next_ghost_anchor.anchor_id;
        txData[39] = next_ghost_anchor.next_anchor_id;
        txData[40] = next_ghost_anchor.sleep_slots;

  			/* Sending extended frame */
        if(!decaduino.pdDataRequest(txData, 41, delayed, slot_start) ){
          DPRINTFLN("$Could not send the frame");
        }
      }
      else {
        /* Sending short frame */
        if(!decaduino.pdDataRequest(txData, 28, delayed, slot_start) ){
          DPRINTFLN("$Could not send the frame");
        }
      }

			/* going back to the regular cycle if the target was an anchor */
      if (is_target_anchor) {
        is_target_anchor = false;
        next_target_idx = 0;
      }
			/* waiting completion */
			timeout = millis() + TX_TIMEOUT;
      while ((millis() < timeout) || !decaduino.hasTxSucceeded() );

      /* starting recording ranging duration */
      ranging_timer = micros();
			t1 = decaduino.getLastTxTimestamp();
			/* enabling reception for the incoming ACK */
			decaduino.plmeRxEnableRequest();
			timeout = millis() + ACK_TIMEOUT;
			state = TWR_ENGINE_STATE_WAIT_ACK;
      break;


    case TWR_ENGINE_STATE_WAIT_ACK:
    /** Waiting for the reply (Acknowledgment frame) of the target device */
      if ( millis() > timeout ) {
        state = TWR_ENGINE_STATE_INIT;
        DPRINTFLN("$timeout on waiting ACK");
        has_timedout = true;

        /* re-enabling reception */
        decaduino.plmeRxDisableRequest();
        decaduino.plmeRxEnableRequest();
        ret = TWR_COMPLETE;
				break;
      }

      if ( decaduino.rxFrameAvailable() ) {
        if ( rxData[0] == TWR_MSG_TYPE_ACK ) {
          decaduino.plmeRxEnableRequest();
          for (int i=0; i<8; i++){
						/* getting dest ID */
              rxID[i]=rxData[i+1];
          }
          // Serial.println("$ Received ACK ID: ");
          // print_byte_array(rxID);
          // Serial.println();
          // Serial.println("$ Verifier ID: ");
          // print_byte_array(verifierID);
          Serial.println();
          //if (true) {
          if (byte_array_cmp(rxID, verifierID)) {

          t4 = decaduino.getLastRxTimestamp();
          /* enabling reception for DATA frame */
          timeout = millis() + DATA_TIMEOUT;
          state = TWR_ENGINE_STATE_WAIT_DATA_REPLY;
          }
					else{
						/* previous frame was for another dest - re-enabling reception */
						DPRINTFLN("$ACK was not for me /sadface");
          }
        }
				else {
					/* previous frame was not an ACK - re-enabling reception */
          decaduino.plmeRxEnableRequest();
					DPRINTFLN("$RX frame is not an ACK");
          }
      }
      break;

    case TWR_ENGINE_STATE_WAIT_DATA_REPLY:
    /** Waiting for the timestamps (DATA frame) of the target device */
      if ( millis() > timeout ) {
				DPRINTFLN("$timeout on waiting DATA");
        ret = TWR_COMPLETE;
        has_timedout = true;
        /* re-enabling reception */
        decaduino.plmeRxDisableRequest();
        decaduino.plmeRxEnableRequest();
        state = TWR_ENGINE_STATE_INIT;
				break;
      }

      if ( decaduino.rxFrameAvailable() ) {
        decaduino.plmeRxEnableRequest();
        if ( rxData[0] == TWR_MSG_TYPE_DATA_REPLY ) {
          for (int i=0; i<8; i++){
							/* getting dest ID */
              rxID[i]=rxData[1+i];
          }

					if (byte_array_cmp(rxID, verifierID)) {
              state = TWR_ENGINE_STATE_EXTRACT_T2_T3;
          }
					else {
						/* previous frame was for another dest */
						DPRINTFLN("$DATA was not for me /sadface");
          }
        }
				else {
					/* previous frame was not an ACK*/
					DPRINTFLN("$RX frame is not a DATA");
				}
      }
      break;

    case TWR_ENGINE_STATE_EXTRACT_T2_T3:
      /** Extracting timestamps from DATA frame and calculating the distance */
			/* extracting timestamps */
      t2 = decaduino.decodeUint64(&rxData[17]);
      t3 = decaduino.decodeUint64(&rxData[25]);

			/* computing ToF and applying skew correction */
      tof = (t4 - t1 - (t3 - t2))/2;
      tof_skew = ((t4 - t1) - (1+1.0E-6*decaduino.getLastRxSkew())*(t3 - t2))/2;

			/* computing distance */
      distance = tof * SPEED_COEFF;
      distance_skew = tof_skew * SPEED_COEFF;

			if (ALOHA) {
				/* checking for collisions */
				if ( (distance_skew < 0) || (distance_skew > DMAX) ) {
					aloha_delay = SLOT_LENGTH + NODE_ID * ALOHA_COLLISION_DELAY;
				}
				else {
					aloha_delay = SLOT_LENGTH;
				}
			}
      state = TWR_ENGINE_STATE_SEND_DATA_PI;
      break;

    case TWR_ENGINE_STATE_SEND_DATA_PI :
      /** Sends the Ranging results along with PHY data to the host RPI on serial port */
			/* Frame format *anchorID|tagID|t1|t2|t3|t4|RSSI# */
      if (my_turn) {
        Serial.println("Calculated in direct TWR");
      }
      else {
        Serial.println("Calculated in differential TWR");
      }

      Serial.print("*");
      print_byte_array(myID);

      Serial.print("|");
      print_byte_array(targetID[next_target_idx]);

      Serial.print("|");
      Serial.print(distance_skew);


      /* timestamps */
			Serial.print("|");
      Serial.print((int) t1);

			Serial.print("|");
      Serial.print((int) t2);

      Serial.print("|");
      Serial.print( (int) t3);

      Serial.print("|");
      Serial.print( (int) t4);

      /* skew */
      Serial.print("|");
      Serial.print(decaduino.getLastRxSkew());

      /* RSSI */
			Serial.print("|");
      Serial.print(decaduino.getRSSI() );

      /* First path power */
      Serial.print("|");
      Serial.print(decaduino.getFpPower());

      /* FpAmpl2 */
      Serial.print("|");
      Serial.print((int) decaduino.getFpAmpl2());

      /* Std noise */
      Serial.print("|");
      Serial.print(decaduino.getSNR());

      /* Temperature */
      Serial.print("|");
      Serial.print(decaduino.getTemperature());

      Serial.println("#\n");

      /* recording TWR duration */
      Serial.print("$ TWR duration: ");
      Serial.println(micros() - ranging_timer);
      Serial.print("$ TWR duration according to DW clock: ");
      Serial.println(compute_elapsed_time_since(t1));

      my_turn = false;   
      state = TWR_ENGINE_STATE_INIT;
      ret = TWR_COMPLETE;
      break;

    default:
      state = TWR_ENGINE_STATE_INIT;
      break;


  }
  return(ret);
}
