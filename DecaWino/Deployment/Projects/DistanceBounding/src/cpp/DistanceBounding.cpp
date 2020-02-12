#include "DistanceBounding.h"

static DecaDuino decaduino;
static int previous_state, state, next_state, frame_counter = 0;
static uint8_t txBuffer[BUFFER_LEN], rxBuffer[BUFFER_LEN];
static uint64_t start_ts, current_time;
static char serial_command;
static uint16_t rxLen = 0;
static int timeout, has_clock_reset = 0;
static const char * states[50]=
{
"Init",
"Serial",
"Ping",
"Pong",
};



void setup_DB() {
  delay(1000);
  pinMode(13, OUTPUT);
  SPI.setSCK(14);
  if (!decaduino.init()) {
    Serial.println("DecaDuino init failed");
  }
  /* Rx-TX parameters */
  decaduino.setRxBuffer(rxBuffer, &rxLen);
	decaduino.plmeRxEnableRequest();

  /* RX-TX parameters */
  decaduino.setPreambleLength(PLENGTH);

  /* starting state */
  previous_state = IDLE;
  if (VERIFIER) {
    state = PING;
    previous_state = IDLE;
    Serial.println("Starting as Verifier");
  }
  else {
    state = PONG;
    decaduino.plmeRxEnableRequest();
    Serial.println("Starting as Prover");
  }
  timeout = micros();
}

void send_db_results() {
  /* sends  frame_counter to host */
  Serial.print("$ DB ended succesfully.\n[Frame exchanged]: ");
  Serial.println(frame_counter);
  Serial.print("[Skew]: ");
  Serial.println(decaduino.getLastRxSkew());
}


void loop_DB() {
  // if (state != previous_state) {
  //   Serial.print("$State: ");
  //   Serial.println(states[state]);
  // }
  previous_state = state;

  switch(state) {
    case IDLE:
      /* waiting any input from host */
      if (Serial.available()) {
        state = USB_SERIAL;
        next_state = IDLE;
      }
      break;

    case USB_SERIAL:
      /* reading serial command */
      serial_command = Serial.read(); // { used as termination character
      while ((serial_command == '\r') || (serial_command == '\n')) {
       /* skipping */
       serial_command = Serial.read();
      }

      if (serial_command == -1) {
       /* Nothing was available */
       state = next_state;
      }

      else {
        switch(serial_command - ASCII_NUMBERS_OFFSET) {
         case 0:
           Serial.println("$ Initiating Distance-Bounding Protocol");
           next_state = PING;
           break;

         default:
           Serial.println("$ unknown command received:");
           Serial.println(serial_command);
           break;
        }

        // Staying in Serial state if bytes are still available in buffer
        if (Serial.available() > 0) {
         state = USB_SERIAL;
        }

        else {
         state = next_state;
        }
      }
     break;

    case PING:
      /* sending an empty frame */
      if (!decaduino.pdDataRequest(txBuffer,1)) {
        Serial.println("Sending failed");
      }
      else {
        /* waiting for TX completion */
        //while (!decaduino.hasTxSucceeded());
      }

      /* switching immeditately to reception */
      decaduino.plmeRxEnableRequest();
      /* checking if communication has been established */
      if ( (VERIFIER) && (frame_counter > 0) ) {
          /* checking if the protcol has ended */
          current_time = decaduino.getSystemTimeCounter();
          if (current_time < start_ts) {
            has_clock_reset = 1;
          }
          if ((has_clock_reset) && (current_time > start_ts)) {
            send_db_results();
            frame_counter = 0;
            state = IDLE;
            has_clock_reset = 0;
          }
      }
      timeout = micros();
      state = PONG;
      break;

    case PONG:
      if (decaduino.rxFrameAvailable()) {
        if (frame_counter == 0) {
          /* communication has just been established, recording starting timestamp */
          start_ts = VERIFIER?decaduino.getLastTxTimestamp():decaduino.getLastRxTimestamp();
          Serial.println("Communication established");
          Serial.print("Starting timestamp:");
          Serial.println((long) start_ts);
        }
        frame_counter++;
        state = PING;
      }
      if (VERIFIER && (micros() - timeout > 500)) {
        //Serial.println("Timeout");
        state = PING;
        decaduino.plmeRxDisableRequest();
      }
      break;

    default:
      break;

    }
}
