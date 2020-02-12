#include "Boiler.h"

static DecaDuino decaduino;
static int previous_state, state, next_state, frame_counter = 0;
static uint8_t txBuffer[BUFFER_LEN], rxBuffer[BUFFER_LEN];
static uint64_t start_ts, current_time;
static char serial_command;
static uint16_t rxLen = 0;
static int timeout, has_clock_reset = 0;
static int dummy_calculation;
static float last_skew;
static double skew_acc = 0;
static const char * states[50]=
{
"Init",
"Serial",
"Ping",
"Pong",
};



void setup_DB() {
  delay(7000);
  pinMode(13, OUTPUT);
  SPI.setSCK(14);
  if (!decaduino.init()) {
    Serial.println("DecaDuino init failed");
  }
  /* Rx-TX parameters */
  decaduino.setRxBuffer(rxBuffer, &rxLen);
	//decaduino.plmeRxEnableRequest();

  /* RX-TX parameters */
  decaduino.setPreambleLength(PLENGTH);
  decaduino.setRxPrf(2);
  decaduino.setTxPrf(2);

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
        while (!decaduino.hasTxSucceeded());
        //dummy_calculation = frame_counter / 11;
      }
      //timeout = micros();
      //state = PONG;
      frame_counter++;
      if ((frame_counter % 5) == 0) {

        //Serial.println(frame_counter);
        //Serial.print("Temperature: ");
        Serial.print(frame_counter);
        Serial.print("|");
        Serial.println(decaduino.getTemperature());
      }
      break;

    case PONG:
      if (decaduino.rxFrameAvailable()) {
        if (SLEEP_TIME != 0) {
          delayMicroseconds(SLEEP_TIME);
        }
        decaduino.plmeRxEnableRequest();
        if (frame_counter == 0) {
          /* communication has just been established, recording starting timestamp */
          start_ts = VERIFIER?decaduino.getLastTxTimestamp():decaduino.getLastRxTimestamp();
          Serial.println("Communication established");
          Serial.print("Starting timestamp:");
          Serial.println((long) start_ts);
        }
        last_skew = decaduino.getLastRxSkew();
        if ((last_skew > -25) && (last_skew < 25) ) {
          skew_acc += last_skew;
          frame_counter++;
        }
        if ((frame_counter % N_SAMPLES) == 0) {
          skew_acc /= N_SAMPLES;
          //Serial.println(frame_counter);
          //Serial.print("Temperature: ");
          Serial.print(skew_acc);
          Serial.print("|");
          Serial.println(decaduino.getTemperature());
          skew_acc = 0;
        }

      }

      break;

    default:
      break;

    }
}
