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
 * @file Calibration.cpp
 * @author Baptiste Pestourie
 * @date 2020 May 1st
 * @brief Source file for the cooperative anchor firmware. This firmware is intended for DecaWino chips.
 * Anchors are fixed stations performing ranging with mobile tags.
 * The cooperative anchor firmware allow an anchor to design a tag to participate in a verification process. See the platform documentation for details.
 * @see https://github.com/Hedwyn/SecureLoc
 */

#include "Calibration.h"

static DecaDuino decaduino; /**< Instance for all DWM1000-related operations*/


/* RX-TX buffers */
static uint8_t rxData[128]; /**< Reception buffer */
static uint8_t txData[128]; /**< Emission buffer */
static uint16_t rxLen; /**< Reception buffer length*/

/* FSM */
static int state, previous_state;
static const char * fsm_states[50] = {
    "Idle",
    "Ping",
    "Pong",
    "Compute key"
};

/* Serial communications */
static int command;
int main(){
	delay(1000);
	CBKE_setup();
	while (1) {
		CBKE_loop();
		yield();
	}
	return(0);
}

/* CBKE protocol */
static int mode;
static int frame_counter;
static unsigned int watchdog_timer;
static int ping_pong_delay = PING_PONG_DELAY;
static int plength = PLENGTH;
static int pcode = 4;
static int channel = CHANNEL;
static uint64_t ts_rx;
static int delayed;
static uint64_t scheduling_accuracy = 0;


/* CBKE samples */
static Sample cbke_vector[CBKE_MAX_LENGTH];
static int cbke_counter = 0;
static int cbke_length = CBKE_LENGTH;
static double average_ts = 0;
static double average_sym = 0;
static int pacsize = 8;



void compute_average() {
    Sample *current_sample; 
    float skew = 0;
    uint64_t ts;
    double symbols = 0, timestamp = 0 ;
    int i;

    for (i = 0; i < cbke_length; i++) {
        current_sample= &cbke_vector[i];
        skew += (current_sample->skew)/cbke_length;
        ts = current_sample->timestamp;
        timestamp += ((double) ts) / cbke_length; 
        
        symbols += (double) (current_sample->symbols) / cbke_length;
    } 
    Serial.println("Average symbols");
    Serial.println(symbols);
    Serial.println("Average skew");
    Serial.println(skew);
    Serial.println("Average timestamp");
    Serial.println(timestamp);    
    average_ts = timestamp;
    average_sym = symbols;
}

void compute_std() {
    Sample *current_sample;
    uint64_t ts;
    double ts_std = 0,sym_std = 0, sym,  deviation;
    int i;

    for (i = 0; i < cbke_length; i++) {
        current_sample= &cbke_vector[i];
        ts = (double) current_sample->timestamp;
        deviation = ts - average_ts;
        sym = current_sample->symbols - average_sym;
        sym_std += abs(sym);
        ts_std += abs(deviation);
    } 
    ts_std /= cbke_length;
    sym_std /= cbke_length;
    Serial.println("STD timestamp");
    Serial.println(ts_std);  
    Serial.println("Symbols timestamp");
    Serial.println(sym_std);  
}

void extract_sample() {
    Sample *current_sample; 
    float skew;
    int symbols;

    if (cbke_counter == cbke_length) {
        DPRINTFLN("Extraction error - CBKE vector is already full");
    }
    else {
        skew = decaduino.getLastRxSkew();
        symbols = decaduino.getRxPacc();

        while (cbke_counter <= frame_counter) {
            current_sample= &cbke_vector[cbke_counter];
            current_sample->skew = skew;
            current_sample->symbols = symbols;
            current_sample->timestamp = scheduling_accuracy; 
            cbke_counter++;
        }
    }
}

void CBKE_setup() {
  
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
    decaduino.setRxBuffer(rxData, &rxLen);
    decaduino.setChannel(2);
    decaduino.setPreambleLength(PLENGTH);
    decaduino.setTxPcode(pcode);
    decaduino.setRxPcode(pcode);
    /* setting header to CBKE */
    txData[0] = CBKE_HEADER;
    state = CBKE_IDLE;
}

void CBKE_loop() {
    /* displaying state when switching state in debug mode */
    if (state != previous_state) {
        DPRINTF("State: ");
        DPRINTFLN(fsm_states[state]);
    }
    previous_state = state;
    switch (state) {
        case CBKE_IDLE:
            /* waiting for serial input */
            if (Serial.available() > 0) {
                command = Serial.parseInt();
                /* parsing command */
                switch (command) {
                    case PROVER:
                        DPRINTFLN("Switching to prover mode");
                        /* enabling reception */
                        decaduino.plmeRxEnableRequest();
                        
                        state = CBKE_PONG;
                        mode = PROVER;
                        txData[9] = mode;
                        break;

                    case VERIFIER:
                        DPRINTFLN("Switching to verifier mode");
                        ts_rx = decaduino.getSystemTimeCounter();
                        state = CBKE_PING;
                        mode = VERIFIER;
                        txData[9] = mode;
                        break;

                    case SET_PARAM:
                        /* eliminating separator */
                        Serial.read();
                        command = Serial.parseInt();
                        switch(command) {
                            case CBKE_LENGTH_P:                              
                                Serial.read();
                                cbke_length = Serial.parseInt();
                                DPRINTF("Changing cbke length to ");
                                DPRINTFLN(cbke_length);
                                break;

                            case PING_PONG_DELAY_P:
                                Serial.read();
                                ping_pong_delay = Serial.parseInt();
                                DPRINTF("Changing ping-pong delay to ");
                                DPRINTFLN(ping_pong_delay);
                                break;

                            case PLENGTH_P:
                                Serial.read();
                                plength = Serial.parseInt();
                                Serial.print("Changing plength  to ");
                                Serial.println(plength);
                                decaduino.setPreambleLength(plength);
                                break; 

                            case PCODE_P:
                                Serial.read();
                                pcode = Serial.parseInt();
                                Serial.print("Changing pcode  to ");
                                Serial.println(pcode);
                                decaduino.setTxPcode((uint8_t) pcode);
                                break; 

                            case CHANNEL_P:
                                Serial.read();
                                channel = Serial.parseInt();
                                Serial.print("Changing channel  to ");
                                Serial.println(channel);
                                decaduino.setChannel(channel);
                                break; 

                            case PACSIZE_P:
                                Serial.read();
                                pacsize = Serial.parseInt();
                                Serial.print("Changing pac size  to ");
                                Serial.println(pacsize);
                                decaduino.setPACSize(pacsize);
                                break; 
                            default:
                                DPRINTFLN("Unknown command");
                                break;
                        }
                        break;
                    
                    default:
                        DPRINTFLN("Unknown command received:");
                        DPRINTFLN(command);
                        break;

                }
                /* flushing serial buffer */
                while (Serial.read() != -1);
                
            }
            break;
        
        case CBKE_PING:
            /* sending frame */
            // if ((VERIFIER) && (frame_counter % SAMPLES_PER_BIT == 0)) {
            //     delayMicroseconds(ping_pong_delay);
            // }
            *( (int *) (txData + 1)) = frame_counter;

            if (pcode != 0) {
                if (decaduino.getSystemTimeCounter() < ts_rx + REPLY_TIME - TX_TIMEOUT){
                    delayed = 1;
                }
                else {
                    delayed = 0;
                    Serial.println("Too late for delayed send");
                    Serial.println((long) (decaduino.getSystemTimeCounter()));
                    Serial.println((long) (ts_rx + REPLY_TIME));
                }
                decaduino.pdDataRequest(txData, 10, delayed, ts_rx + REPLY_TIME);         
                DPRINTFLN("Currently sending frame, waiting for completion...");  
                while (!decaduino.hasTxSucceeded());
                if (delayed) {
                    scheduling_accuracy = (ts_rx + REPLY_TIME) - decaduino.getLastTxTimestamp();
                }
                                            
            }
            else {
                delayMicroseconds(100);
            }
            
            /* enabling reception */
            if ((mode == PROVER) && (frame_counter + 1 == cbke_length) ) {
                /* CBKE protocol is over, computing signature */
                state = CBKE_COMPUTE_KEY;
            }
            else { 
                // if (mode == VERIFIER) {
                //     frame_counter++;
                // } 
                if (NODE_ID == 1) {
                    state = CBKE_PONG; 
                    decaduino.plmeRxEnableRequest();
                    watchdog_timer = millis();  
                }
            }    

     
            break;
        
        case CBKE_PONG:
            if (Serial.available() > 0) {
                DPRINTFLN("Serial message received. Interrupting current protocol");
                decaduino.plmeRxDisableRequest();
                /* resetting counters */
                frame_counter = 0;
                cbke_counter = 0;
                state = CBKE_IDLE;
            }
            else if ( (mode == VERIFIER) && (millis() - watchdog_timer >  PONG_TIMEOUT)) {
                DPRINTF("Timeout during CBKE. Frame counter:");
                DPRINTFLN(frame_counter);
                if (frame_counter == 1) {
                    /* resetting if it was the first frame */
                    frame_counter = 0;
                }
                /* disabling reception before switching back to transmission */
                decaduino.plmeRxDisableRequest();
                state = CBKE_PING;
            }
            else {
                if (decaduino.rxFrameAvailable()) {
                    DPRINTFLN("frame received"); 
                    if ((rxData[0] == CBKE_HEADER) && (rxData[9] == !mode) ) {
                    DPRINTFLN("CBKE from verifier");
                    ts_rx = decaduino.getLastRxTimestamp();                   
                    if (mode == PROVER) {
                        frame_counter = *( (int *) (rxData + 1));

                    }    
                    extract_sample();
                    if (mode == VERIFIER) {
                        frame_counter++;
                    }             
                    if ((mode == VERIFIER) && (frame_counter == cbke_length) ) {
                        /* CBKE protocol is over, computing signature */
                        state = CBKE_COMPUTE_KEY;
                    }
                    else {
                        /* continuing protocol */
                        state = CBKE_PING;
                    }
                    DPRINTF("Frame counter:");
                    DPRINTFLN(frame_counter);
                    }
                    else {
                        decaduino.plmeRxEnableRequest();
                    }
                }

            }
            break;

        case CBKE_COMPUTE_KEY:
            DPRINTF("Vector length: ");
            DPRINTFLN(cbke_counter);

            DPRINTFLN("Symbols vector: ");
            Serial.print("#");
            for (int i = 0; i < cbke_length; i++) {
                Serial.print(cbke_vector[i].symbols);
                Serial.print(";");
            }
            Serial.println();
            delay(800);

            DPRINTFLN("Skew vector: ");
            Serial.print("^");
            for (int i = 0; i < cbke_length; i++) {
                Serial.print(cbke_vector[i].skew);
                Serial.print(";");
            }
            Serial.println();
            delay(800);

            DPRINTFLN("Timestamp vector: ");
            Serial.print("*");
            for (int i = 0; i < cbke_length; i++) {
                Serial.print((long) cbke_vector[i].timestamp);
                Serial.print(";");
            }
            Serial.println();
            delay(800);          
            Serial.println();
            compute_average();
            compute_std();


            /* resetting counters */
            frame_counter = 0;
            cbke_counter = 0;
            /* back to idle state, waiting for serial input */
            state = CBKE_IDLE;
            break;
    }

}