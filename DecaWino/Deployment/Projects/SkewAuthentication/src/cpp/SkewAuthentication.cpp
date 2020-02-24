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
 * @file SkewAuthentication.cpp
 * @author Baptiste Pestourie
 * @date 2020 February 1st
 * @brief Source file for the Skew Authentication firmware. This firrmware has 2 modes, prover(P) and verifier(V).
 * @todo documentation + interfacing with main anchor/tags projects
 * The prover is authenticated based on its skew signature. Send '0' to both nodes to start the authentication process.
 * The two nodes will exchange frames at maximum speed such as inducing a fast temperature gradient on P.
 * V characterizes P's skew throughout the protocol. The signature is sentto the host laptop or RPI on the serial port.
 * When authentication processes are not running this firmware is similar to Boiler.
 * See the platform documentation and related papers for details.
 * @see https://github.com/Hedwyn/SecureLoc
 */


#include "SkewAuthentication.h"

static DecaDuino decaduino;
static int previous_state, state, next_state, frame_counter = 0, distance_ctr = 0, temperature_ctr = 0, n_total_frames = N_TOTAL_FRAMES, bonus_frames = 0;
static int signature_length = SIGNATURE_LENGTH;
static uint8_t txBuffer[BUFFER_LEN], rxBuffer[BUFFER_LEN];
static uint64_t start_ts, current_time;
static int serial_command;
static uint16_t rxLen = 0;
static int timeout;
static float last_skew;
static double skew_acc = 0;
static float signature[1000];
static int signature_idx = 0;
static int authentication_running = 0;
static int duty_cycle = 10;
static int sleep_time = SLEEP_TIME;
static uint8_t is_delayed = 0;
static uint64_t departure_time;
static uint64_t timestamp, lastTxTimestamp;
static double distance, distance_acc = 0, temperature_acc = 0;
static long tof;
static double currentTemp, lastTemp;
static const char * states[50]=
{
"Ping",
"Pong"
};

void handleSerial() {
  Serial.print("Serial Event ! Received:");
  Serial.println(serial_command);
  switch(serial_command) {
    case '0':
      Serial.println("$ Initiating Authentication");
      authentication_running = 1;
      frame_counter = 0;
      skew_acc = 0;
      timestamp = decaduino.getSystemTimeCounter();
      if (VERIFIER) {
        decaduino.setPreambleLength(LONG_PREAMBLE);
      }
      else {
        decaduino.setPreambleLength(SHORT_PREAMBLE);
        is_delayed = LOCALIZE?1:0;
      }
      timeout = millis() + TIMEOUT;
      break;

    case '1':
      duty_cycle = Serial.parseInt();
      /* Flushing buffer */
      while (Serial.read() != -1);
      Serial.print("Switching to duty cycle: ");
      sleep_time = duty_cycle;
      Serial.println(duty_cycle);
      break;

      case '2':
        n_total_frames = Serial.parseInt();
        signature_length = n_total_frames / AVERAGE_LENGTH;
        /* Flushing buffer */
        while (Serial.read() != -1);
        Serial.print("Switching to protocol length: ");
        Serial.println(n_total_frames);
        break;

      case '3':
        serial_command = Serial.parseInt();
        decaduino.setChannel(serial_command);
        /* Flushing buffer */
        while (Serial.read() != -1);
        Serial.println("Switching channel ");
        break;

      case '4':
        serial_command = Serial.parseInt();
        decaduino.setTxPrf(serial_command);
        decaduino.setRxPrf(serial_command);
        /* Flushing buffer */
        while (Serial.read() != -1);
        Serial.println("Switching PRF ");
        break;

    default:
      Serial.println("Unknwn command received");
      break;
  }
}

void setup_DB() {
  delay(3000);
  pinMode(13, OUTPUT);
  SPI.setSCK(14);
  Serial.begin(9600);
  if (!decaduino.init()) {
    Serial.println("DecaDuino init failed");
  }
  /* Rx-TX parameters */
  decaduino.setRxBuffer(rxBuffer, &rxLen);
	//decaduino.plmeRxEnableRequest();

  /* RX-TX parameters */
  decaduino.setPreambleLength(PLENGTH);
  decaduino.setChannel(CHANNEL);
  decaduino.setRxPrf(2);
  decaduino.setTxPrf(2);

  /* starting state */
  previous_state = PING;
  if (VERIFIER) {
    state = PING;
    previous_state = PONG;
    Serial.println("Starting as Verifier");
  }
  else {
    state = PONG;
    bonus_frames = AVERAGE_LENGTH -1;
    decaduino.plmeRxEnableRequest();
    Serial.println("Starting as Prover");
  }
  timeout = micros();

  /* getting temperature */
  lastTemp = decaduino.getTemperature();
  while ( (lastTemp < 15) || (lastTemp > 60)) {
      lastTemp = decaduino.getTemperature();
  }
}

void send_db_results() {
  /* sends  frame_counter to host */
  Serial.print("$ DB ended succesfully.\n[Frame exchanged]: ");
  Serial.println(frame_counter);
  Serial.print("[Skew]: ");
  Serial.println(decaduino.getLastRxSkewCRI());
}


void loop_DB() {
  // if (state != previous_state) {
  //   Serial.print("$State: ");
  //   Serial.println(states[state]);
  // }
  previous_state = state;

  switch(state) {
    case PING:

      /* sending an empty frame */
      if (is_delayed) {
        departure_time = timestamp + T23;
        if (decaduino.getSystemTimeCounter() < departure_time - GUARD_TIME) {
          decaduino.pdDataRequest(txBuffer,PAYLOAD_LENGTH, is_delayed, departure_time);
        }
        else {
          /* Too late. Switching to a non-scheduled frame */
          Serial.println("$ too late, cancelling scheduling");
          decaduino.pdDataRequest(txBuffer,PAYLOAD_LENGTH);
        }
      }
      else {
        /* transmissions scheduling disabled. Sending non-delayed frame */
        decaduino.pdDataRequest(txBuffer,PAYLOAD_LENGTH);
      }
      /* waiting for TX completion */
      while (!decaduino.hasTxSucceeded());

      // Serial.print("$ Total time: ");
      // Serial.println((long) (decaduino.getLastTxTimestamp() - timestamp));
      if (authentication_running) {
        if (frame_counter == n_total_frames + bonus_frames) {
          authentication_running = 0;
          Serial.println("$ Authentication completed");
          Serial.println("$ Sending Signature");

          Serial.print("#");
          for (int i = 0; i < signature_length; i++) {
            Serial.print(signature[i]);
            Serial.print("|");
          }
          Serial.println();
          if (PROVER) {
            Serial.println("going back to reception state");
            state = PONG;
            decaduino.plmeRxEnableRequest();
          }
        }
        else {
          decaduino.plmeRxEnableRequest();
          state = PONG;
          timeout = millis() + TIMEOUT;
        }
      }


      if (!authentication_running) {
        serial_command = Serial.read();
        if (serial_command !=  -1) {
          handleSerial();
        }
      }
      break;

    case PONG:

      if (decaduino.rxFrameAvailable()) {
        timestamp = decaduino.getLastRxTimestamp();
        if (authentication_running) {
          state = PING;
        }
        else {
          if (sleep_time != 0) {
            delayMicroseconds(sleep_time);
          }
          decaduino.plmeRxEnableRequest();
        }
        /* If ranging is enabled, calculating distance */
        if (VERIFIER && LOCALIZE) {
          lastTxTimestamp = decaduino.getLastTxTimestamp();
          tof = ( timestamp - lastTxTimestamp- T23);
          distance = (double) tof * SPEED_COEFF;
          if ((distance > DMIN) && (distance < DMAX)) {
            distance_acc += distance;
            distance_ctr += 1;
          }
          if (distance_ctr == AVERAGE_LENGTH) {
            distance_ctr = 0;
            distance_acc /= AVERAGE_LENGTH;
            Serial.print("$ Distance: ");
            Serial.println(distance_acc);
            distance_acc = 0;
          }
        }
        last_skew = decaduino.getLastRxSkew();


        if ((last_skew > -25) && (last_skew < 25) ) {
          if ((VERIFIER) && (SKEW_CORRECTION)) {
            last_skew += (lastTemp - T_REF) * SKEW_CORRECTION_COEFF;
          }
          skew_acc += last_skew;
          frame_counter++;
        }
        if ((frame_counter % AVERAGE_LENGTH) == 0) {
          skew_acc /= AVERAGE_LENGTH;
          if (authentication_running) {
            if (signature_idx < signature_length) {
              signature[signature_idx] = skew_acc;
              signature_idx++;
            }
          }

          Serial.print(skew_acc);
          Serial.print("|");
          Serial.println(lastTemp);
          skew_acc = 0;
        }
      }
      /* computing temperature */
      currentTemp = decaduino.getTemperature();
      if ( (currentTemp > 0) && (currentTemp < 100)) {
        temperature_acc += currentTemp;
        temperature_ctr++;
      }
      if (temperature_ctr == AVERAGE_LENGTH) {
        temperature_ctr = 0;
        lastTemp = temperature_acc / AVERAGE_LENGTH;
        temperature_acc = 0;
      }
      /* checking for timeouts */
      if (authentication_running && (millis() > timeout)) {
        state = PING;
        Serial.println("$ Timeout");
        timestamp = decaduino.getSystemTimeCounter();
        decaduino.plmeRxDisableRequest();
      }
      if (!authentication_running) {
        serial_command = Serial.read();
        if (serial_command !=  -1) {
          handleSerial();
        }
      }
      break;

    default:
      break;

    }
}
