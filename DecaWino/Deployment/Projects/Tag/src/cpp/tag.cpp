#include "tag.h"
#include "anchor_c.h"



static DecaDuino decaduino;
int state, previous_state;

/* UWB frames */
uint8_t txData[128];
uint8_t rxData[128];
uint16_t rxLen;

/* IDs */
byte myID[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x02};
byte targetID [8]; //Id robot reçue
byte anchorID [8];   //Id de l'ancre émettrice


/* timestamps */
uint64_t t2, t3;      //temps de réception et temps de ré-émission

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
"Send Data"
};

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
  //decaduino.setPreambleLength(256);

  /*decaduino.setRxPrf(2);
  decaduino.setTxPrf(2);
  decaduino.setDrxTune(64);
  decaduino.setRxPcode(9);
  decaduino.setTxPcode(9);*/
  /*
  decaduino.setPreambleLength(256);

  decaduino.setTBR(110);
  decaduino.setChannel(3);
  decaduino.setPACSize(16);
  decaduino.setTxPrf(64);
  decaduino.setRxPrf(64);
  decaduino.displayRxTxConfig();
  */
  /*decaduino.setPhrPower(3,0);
  decaduino.setSdPower(3,0);*/

  /*
  decaduino.setSmartTxPower(0);
  decaduino.setTxPower(18,15.5);
  */

  //tag_RxTxConfig();
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
      //decaduino.plmeRxDisableRequest();
      state = TWR_ENGINE_STATE_RX_ON;
			#ifdef COOPERATIVE
			if (ghost_anchor_id[7] != 0) {// && (next_target_id[7] != 0)) {
				state = TWR_ENGINE_GHOST_ANCHOR;
			}
			#endif

      break;

		case TWR_ENGINE_GHOST_ANCHOR:
			state = TWR_ENGINE_STATE_INIT;
			Serial.println("Switching to ghost anchor mode");
			Serial.print("Ghost Anchor ID: ");
			Serial.println(ghost_anchor_id[7]);
			anchor_setup();
			while (anchor_loop(ghost_anchor_id, next_anchor_id, 0) != TWR_COMPLETE );
			tag_setup();
			Serial.println("Ghost Anchor Job Complete");
			ghost_anchor_id[7] = 0;
			next_target_id[7] = 0;
			break;

    case TWR_ENGINE_STATE_RX_ON:
      decaduino.plmeRxEnableRequest();
      state = TWR_ENGINE_STATE_WAIT_START;
      break;

    case TWR_ENGINE_STATE_WAIT_START:
      if ( decaduino.rxFrameAvailable() ) {
        /* START format : START | targetID | anchorID */
        if ( rxData[0] == TWR_MSG_TYPE_START ) {
          Serial.println("$Start received");
          for (int i=0; i<8; i++){
           targetID [i] = rxData[i+1];
           anchorID [i] = rxData[i+9];
          }
          if ( byte_array_cmp(targetID, myID) ) {
            t2 = decaduino.getLastRxTimestamp();
            state = TWR_ENGINE_STATE_SEND_ACK;
          }
          else{
              DPRINTFLN("Not for me" );
              state = TWR_ENGINE_STATE_RX_ON;
          }

					/* Control parameters for cooperative methods */
					ghost_anchor_id[7] = rxData[25];
					next_anchor_id[7] = 1;
					next_target_id[7] = rxData[26];


        }
        else {
          DPRINTFLN("Not a START frame");
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
      //decaduino.pdDataRequest(txData, 18,1,t2 + T23);
			decaduino.pdDataRequest(txData, 18);
      while (!decaduino.hasTxSucceeded());
      t3 = decaduino.getLastTxTimestamp();
      state = TWR_ENGINE_STATE_SEND_DATA_REPLY;
      break;


    case TWR_ENGINE_STATE_SEND_DATA_REPLY:
      txData[0] = TWR_MSG_TYPE_DATA_REPLY;
      decaduino.encodeUint64(t2, &txData[17]);
      decaduino.encodeUint64(t3, &txData[25]);
      decaduino.pdDataRequest(txData, 33);
      while (!decaduino.hasTxSucceeded());
      state = TWR_ENGINE_STATE_INIT;
      break;

    default:
      state = TWR_ENGINE_STATE_INIT;
      break;
  }
}
