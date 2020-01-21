#include "anchor_c.h"


/* libraries */

static DecaDuino decaduino;


/* RX-TX buffers */
static uint8_t rxData[128];
static uint8_t txData[128];
static uint16_t rxLen;

/* state machine iterators */
static int state = TWR_ENGINE_STATE_INIT;
static int previous_state = TWR_ENGINE_STATE_IDLE;
static int next_state;
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
};

/* RX IDs - when receiving frames from tags or anchors */
static byte targetID[][8]= { {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x01},// bots
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x02},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01}, //anchors
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x06},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09}};
static byte rxID[8];
static byte nextTarget[8];
static int next_target_idx = 0; //  index on tag to localize in the next round


/* Anchor ID's */
static byte MYID[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, NODE_ID}; // identifiant de l'ancre
static byte anchorID[8]; //anchorID field for received frames
static byte MY_NEXT_ANCHOR_ID[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}; // filled by getId()
static byte nextAnchorID[8] ={0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}; // buffer for the next anchor field in RX frames

/* Two-Way Ranging protocol   */
static unsigned long timeout;
static bool has_timedout;
static uint64_t t1, t2, t3, t4;
static int32_t tof,tof_skew;
static float distance, distance_skew;


/* Serial communications */
static char serial_command, target_id;
static bool is_target_anchor;

/* Scheduling */
static int aloha_delay;
static bool my_turn;
static uint64_t slot_start;
static uint64_t last_start_frame;
static int delayed;

/* Cooperative methods */
struct control_frame{
  byte anchor_id;
  byte tag_id;
  byte sleep_slots; // in slot number
};
static control_frame next_ghost_anchor = {.anchor_id = 0, .tag_id = 0, .sleep_slots = 0};


#ifdef MASTER
void getNextGhostAnchor() {
  Serial.println("I'm Master, sending control frame");
  next_ghost_anchor.anchor_id = NB_ANCHORS;
  next_ghost_anchor.tag_id = (next_target_idx + 1) % NB_ROBOTS;
  next_ghost_anchor.sleep_slots = NB_ANCHORS + next_ghost_anchor.anchor_id - 2;
}
#endif

void getID() {
	#ifdef NODE_ID
		/* setting up anchor id */
		MYID[7] = NODE_ID;

		/* setting up next anchor ID */
		#ifdef NB_ANCHORS
		/* checking if this anchors has the highest ID */
			if (NODE_ID == NB_ANCHORS) {
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
	int i = 0, ret = 1;
	for (i = 0; i <8; i++) {
		if (b1[i] != b2[i]) {
			ret = 0;
			break;
		}
	}
	return(ret);
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

  decaduino.plmeRxEnableRequest();
  timeout = millis() + START_TIMEOUT + (NODE_ID - 1) * SLOT_LENGTH * 1E-3;
  DPRINTFLN("Starting");
  #ifdef MASTER
    state = TWR_ENGINE_STATE_SEND_START;
  #else
    state = TWR_ENGINE_STATE_INIT;
  #endif
  state = TWR_ENGINE_STATE_INIT;
}

void anchor_RxTxConfig() {
	decaduino.setRxBuffer(rxData, &rxLen);
}


int anchor_loop() {
  return(anchor_loop(MYID, MY_NEXT_ANCHOR_ID));
}

int anchor_loop(byte *myID, byte *myNextAnchorID) {
  int ret = TWR_ON_GOING;
  if (state != previous_state) {
    Serial.print("$State: ");
    Serial.println(states[state]);
  }
  previous_state = state;

  switch (state) {
    case TWR_ENGINE_STATE_INIT:
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

      decaduino.plmeRxEnableRequest();
      state = TWR_ENGINE_STATE_IDLE;
      break;

		case TWR_ENGINE_STATE_IDLE :
      if (ALOHA) {
        state = TWR_ENGINE_PREPARE_RANGING;
				break;
      }
			if (millis() > timeout) {
				/* the DATA frame of the previous frame has never been received. Forcing a new cycle */
				state = TWR_ENGINE_PREPARE_RANGING;
        delayed = 0;
        DPRINTFLN("$Timeout- Starting new cycle");
        decaduino.plmeRxDisableRequest();
				break;
			}

      if ( decaduino.rxFrameAvailable() ) {
				my_turn = false;
        DPRINTFLN("$ Frame received");
				/* checking START frames for anchor ranging request */
				if ( rxData[0] == TWR_MSG_TYPE_START ) {
          DPRINTFLN("$ Start received");
					/* extracting target ID */
					for (int i = 0; i < 8; i++) {
						nextTarget[i] = rxData[i + 1];
            nextAnchorID[i] = rxData[i+17];

					}
          Serial.print("Next Target= ");
          print_byte_array(nextTarget);
          Serial.println();

					DPRINTF("$ID received:");
					DPRINTFLN((int) nextAnchorID[7] );
					DPRINTF("$My ID ");
					DPRINTFLN((int) myID[7]);
				}
				if (byte_array_cmp(nextAnchorID, myID))
				{
					my_turn = true;
          last_start_frame = decaduino.getLastRxTimestamp();
				}
				/* checking DATA frames for end of cycle */
				if (my_turn && ( rxData[0] == TWR_MSG_TYPE_DATA_REPLY )) {
					Serial.println("$It's my turn");
          Serial.print("$ID of the next anchor: ");
          print_byte_array(myNextAnchorID);
          #ifndef MASTER
            next_target_idx = get_next_target_idx(nextTarget);
          #endif
					state = TWR_ENGINE_PREPARE_RANGING;
          slot_start =  last_start_frame + (SLOT_LENGTH / (DW1000_TIMEBASE * IN_US) );
          delayed = 1;
        }

        if (state == TWR_ENGINE_STATE_IDLE) {
          decaduino.plmeRxEnableRequest();
        }
      }

      break;

    case TWR_ENGINE_STATE_SERIAL:
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
            Serial.println("$ command #2 received");
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

      // control frame
      txData[25]= next_ghost_anchor.anchor_id;
      txData[26] = next_ghost_anchor.tag_id;
      txData[27] = next_ghost_anchor.sleep_slots;

			/* Sending frame */
      if(!decaduino.pdDataRequest(txData, 28, delayed, slot_start) ){
        DPRINTFLN("$Could not send the frame");
      }

			/* going back to the regular cycle if the target was an anchor */
      if(is_target_anchor) {
        is_target_anchor = false;
        next_target_idx = 0;
      }
			/* waiting completion */
			timeout = millis() + TX_TIMEOUT;
			has_timedout = false;
      Serial.println("$ Waiting Frame");
      while (!decaduino.hasTxSucceeded());
			t1 = decaduino.getLastTxTimestamp();
			/* enabling reception for the incoming ACK */
			decaduino.plmeRxEnableRequest();
			timeout = millis() + ACK_TIMEOUT;
			state = TWR_ENGINE_STATE_WAIT_ACK;
      break;

    case TWR_ENGINE_STATE_WAIT_ACK:
      if ( millis() > timeout ) {
        state = TWR_ENGINE_STATE_INIT;
        DPRINTFLN("$timeout on waiting ACK");
        ret = TWR_COMPLETE;
				break;
      }

      if ( decaduino.rxFrameAvailable() ) {
        if ( rxData[0] == TWR_MSG_TYPE_ACK ) {
          for (int i=0; i<8; i++){
						/* getting dest ID */
              rxID[i]=rxData[i+1];
          }
          if (byte_array_cmp(rxID,myID)) {
						t4 = decaduino.getLastRxTimestamp();
						/* enabling reception for DATA frame */
						timeout = millis() + DATA_TIMEOUT;
						decaduino.plmeRxEnableRequest();
            state = TWR_ENGINE_STATE_WAIT_DATA_REPLY;
          }
					else{
						/* previous frame was for another dest - re-enabling reception */
						decaduino.plmeRxEnableRequest();
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
      if ( millis() > timeout ) {
				DPRINTFLN("$timeout on waiting DATA");
        ret = TWR_COMPLETE;
        state = TWR_ENGINE_STATE_INIT;
				break;
      }
      if ( decaduino.rxFrameAvailable() ) {
        if ( rxData[0] == TWR_MSG_TYPE_DATA_REPLY ) {
          for (int i=0; i<8; i++){
							/* getting dest ID */
              rxID[i]=rxData[1+i];
          }

					if (byte_array_cmp(rxID, myID) ) {
              state = TWR_ENGINE_STATE_EXTRACT_T2_T3;
          }
					else {
						/* previous frame was for another dest - re-enabling reception */
						decaduino.plmeRxEnableRequest();
						DPRINTFLN("$DATA was not for me /sadface");
          }
        }
				else {
					/* previous frame was not an ACK - re-enabling reception */
          decaduino.plmeRxEnableRequest();
					DPRINTFLN("$RX frame is not a DATA");
				}
      }
      break;

    case TWR_ENGINE_STATE_EXTRACT_T2_T3: //Etat d'extraction des distances. Décryptage et id
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
			/* Frame format *anchorID|tagID|t1|t2|t3|t4|RSSI# */
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

      /* RSSI */
			Serial.print("|");
      Serial.print(decaduino.getRSSI() );
      Serial.println("#\n");

      state = TWR_ENGINE_STATE_INIT;
      ret = TWR_COMPLETE;
      break;

    default:
      state = TWR_ENGINE_STATE_INIT;
      break;


  }
  return(ret);
}
