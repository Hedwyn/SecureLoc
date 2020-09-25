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
 * @file CBKE.cpp
 * @author Baptiste Pestourie
 * @date 2020 May 1st
 * @brief Source file for the cooperative anchor firmware. This firmware is intended for DecaWino chips.
 * Anchors are fixed stations performing ranging with mobile tags.
 * The cooperative anchor firmware allow an anchor to design a tag to participate in a verification process. See the platform documentation for details.
 * @see https://github.com/Hedwyn/SecureLoc
 */

#include "CBKE.h"

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
static int plength;
static int pcode = PCODE;
static int prf = PRF;
static int delay_timer;
static int global_timer;
static int is_eavesdropper = 0;
static int channel_rotation[NB_CHANNELS] = {4, 5, 1, 3, 2, 7};
static int pcode_rotation_16[NB_CHANNELS] = {7, 3, 1, 5, 4, 8};
static int pcode_rotation_64[NB_CHANNELS] = {4, 3, 4, 3, 4, 3};
static int channel_idx = 0;
static int channel_switch_flag = 0;

/* quantization */
static char key_chunks[TOTAL_TAPS][KEY_CHUNK_LENGTH];
static int chunk_ctr = 0;
static int key_length;



/* CBKE samples */
static Sample cbke_vector[CBKE_MAX_LENGTH];
static Pulse_sample pulse_vector[TOTAL_TAPS];
static int cbke_counter = 0;
static int cbke_length = CBKE_LENGTH;
static int16_t re[ACC_LENGTH], im[ACC_LENGTH];
static float ampl_accumulator[ACC_LENGTH];
static float phase_accumulator[ACC_LENGTH];
static float pulse_buffer[MAX_PULSE_SAMPLE_LENGTH];
static int nb_total_pulses;



float getSNR() {
    float snr;
    snr = pow(decaduino.getFpAmpl2(), 2) / pow(decaduino.getCire(), 2);
    snr = 10 * log10(snr);
    return(snr);
}

void extract_sample() {
    Sample *current_sample; 
    float rssi, fp_power, snr, los_indicator;
    uint8_t f1;
    uint16_t f2, f3;
    if (cbke_counter == cbke_length) {
        DPRINTFLN("Extraction error - CBKE vector is already full");
    }
    else {
        rssi = decaduino.getRSSI();
        fp_power = decaduino.getFpPower();
        snr =  getSNR();
        los_indicator = rssi - fp_power;

        // f1 = decaduino.getFpAmpl1();
        // f2 = decaduino.getFpAmpl2();
        // f3 = decaduino.getFpAmpl3();
        while (cbke_counter <= frame_counter) {
            current_sample= &cbke_vector[cbke_counter];
            current_sample->rssi = rssi;
            current_sample->fp_power = fp_power;
            current_sample->snr = snr;
            current_sample->los_indicator = los_indicator;

            // current_sample->rssi = (float) f1;
            // current_sample->fp_power = (float) f2;
            // current_sample->snr = (float) f3;

            
            cbke_counter++;
        }
    }
}

void extract_accumulator() {
    float ampl, phase, mean_ampl = 0, mean_phase = 0, center_ampl = 0, center_phase = 0;
    int tap_idx, j, k = 0, lag;
    /* going to the next lags series only when the channel rotation is complete */
    lag = frame_counter - (channel_idx * SAMPLES_PER_BIT);
    lag = (lag / NB_CHANNELS_EFFECTIVE) + (lag % NB_CHANNELS_EFFECTIVE);
    tap_idx = REF_POINTS_ACC * channel_idx;
    j = tap_idx;
    /* detection can occur in the middle of the peak; substracting 3 to always get peak start */
    int fp_idx = (int) (decaduino.getFpIndex() >> 6) + ACC_OFFSET;
    // Serial.println(frame_counter);
    // Serial.println(channel_idx);
    decaduino.getAccumulatedCIR(fp_idx , fp_idx + ACC_LENGTH, re, im);
    if (frame_counter < PULSE_SAMPLE_LENGTH) {
        for (int i = 0; i < ACC_LENGTH; i++) {
            ampl = sqrt(pow((float) im[i], 2) + pow((float) re[i], 2) );
            phase = atan( (float)im[i] / (float)re[i]);
            ampl_accumulator[i] = ampl;
            phase_accumulator[i] = phase;
            /* applying averaging filter on amplitudes and phase */
            if (NORMALIZE_CIR) {
                mean_ampl += ampl;
                mean_phase += phase;
            }
            else {
                mean_ampl += pow(ampl,2);
                mean_phase += pow(phase,2);
            }

            k++;
            if (k == MEAN_WINDOW_LENGTH) {
                k = 0;
                if (NORMALIZE_CIR) {
                    pulse_vector[j].magnitude[lag] = mean_ampl;// / MEAN_WINDOW_LENGTH;
                    pulse_vector[j].phase[lag] = mean_phase;// / MEAN_WINDOW_LENGTH;
                }
                else {
                    pulse_vector[j].magnitude[lag] = sqrt(mean_ampl / MEAN_WINDOW_LENGTH);
                    pulse_vector[j].phase[lag] = sqrt((mean_phase / MEAN_WINDOW_LENGTH));
                }

                center_ampl += pulse_vector[j].magnitude[lag];
                center_phase += pulse_vector[j].phase[lag];
                mean_ampl = 0;
                mean_phase = 0;
                j++;
            }
        }   

        if (!NORMALIZE_CIR) {
            center_ampl /= j;
            center_phase /= j;
        }

        /* centering spatially magnitudes */
        for (int i = tap_idx; i < tap_idx + REF_POINTS_ACC; i++) {
            if (NORMALIZE_CIR) {
                pulse_vector[i].magnitude[lag] = (100 * pulse_vector[i].magnitude[lag]) / center_ampl;
                pulse_vector[i].phase[lag] = (100 * pulse_vector[i].phase[lag]) / center_phase;
            }
            else {
                pulse_vector[i].magnitude[lag] -= center_ampl;
                pulse_vector[i].phase[lag] -= center_phase;
            }

            mean_ampl = 0;
            mean_phase = 0;           
        }
    }
}

void display_accumulator() {
    //Pulse_sample *accumulator = &pulse_vector[frame_counter];
    Serial.print("!");
    for (int i = 0; i < ACC_LENGTH; i++) {
        Serial.print(ampl_accumulator[i]);
        Serial.print(";");
    }
    Serial.println();
}

void setPcode(int pcode_idx) {
    if (prf == 16) {
        decaduino.setTxPcode(pcode_rotation_16[pcode_idx]);
        decaduino.setRxPcode(pcode_rotation_16[pcode_idx]);
    }
    else {
        decaduino.setTxPcode(pcode_rotation_64[pcode_idx]);
        decaduino.setRxPcode(pcode_rotation_64[pcode_idx]);        
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
    decaduino.setChannel(channel_rotation[channel_idx]);
    decaduino.setPreambleLength(PLENGTH);
    setPcode(channel_idx);
    // /* setting header to CBKE */
    decaduino.setTxPrf(PRF);
    decaduino.setRxPrf(PRF);
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
                        global_timer = millis();
                        break;

                    case VERIFIER:
                        DPRINTFLN("Switching to verifier mode");
                        state = CBKE_PING;
                        mode = VERIFIER;
                        txData[9] = mode;

                        global_timer = millis();
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

                            case EAVESDROPPER:
                                Serial.read();
                                is_eavesdropper = Serial.parseInt();
                                Serial.print("Changing eavesdropper mode  to ");
                                Serial.println(is_eavesdropper);
                                break; 

                            case PRF_P:
                                Serial.read();
                                prf = Serial.parseInt();
                                Serial.print("Changing prf  to ");
                                Serial.println(prf);
                                decaduino.setTxPrf(prf);
                                decaduino.setRxPrf(prf);
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
            if ((mode == VERIFIER) && ( (frame_counter) % SAMPLES_PER_BIT == 0)&& (frame_counter != 0)) {
                if (ENABLE_CHANNEL_SWITCH) {
                    /* switching channel  */
                    channel_idx = (channel_idx + 1) % NB_CHANNELS;
                    decaduino.setChannel(channel_rotation[channel_idx]);
                    setPcode(channel_idx);
                    DPRINTF("Switching to channel ");
                    DPRINTFLN(channel_rotation[channel_idx]);
                }
                delayMicroseconds(ping_pong_delay);
            }
            *( (int *) (txData + 1)) = frame_counter;

            if (!is_eavesdropper) {
                decaduino.pdDataRequest(txData, 10);  
                DPRINTFLN(micros() - delay_timer);
                delay_timer = micros();
                DPRINTFLN("Currently sending frame, waiting for completion...");           
                while (!decaduino.hasTxSucceeded());
                DPRINTFLN("transmission completed");
                if (ENABLE_CHANNEL_SWITCH && (mode == PROVER) && ( (frame_counter + 1) % SAMPLES_PER_BIT == 0)) {
                    channel_idx = (channel_idx + 1) % NB_CHANNELS;
                    decaduino.setChannel(channel_rotation[channel_idx]);  
                    setPcode(channel_idx); 
                    DPRINTF("Switching to channel ");
                    DPRINTFLN(channel_rotation[channel_idx]);               
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
            if (DISPLAY_ACCUMULATOR) {
                delay(DISPLAY_DELAY);
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

                    if (mode == PROVER) {
                        frame_counter = *( (int *) (rxData + 1));
                    }    
                    extract_sample();
                    if (ENABLE_CIR) {
                        extract_accumulator(); 
                    }
                    if (DISPLAY_ACCUMULATOR) {
                        display_accumulator();
                    }
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
            if (mode == PROVER) {
                delay(3000);
            }
            DPRINTF("Total protocol duration: ");
            DPRINTFLN(millis() - global_timer);
            DPRINTF("Vector length: ");
            DPRINTFLN(cbke_counter);
           

            DPRINTFLN("RSSI vector: ");
            Serial.print("#");
            for (int i = 0; i < cbke_length; i++) {
                Serial.print(cbke_vector[i].rssi);
                Serial.print(";");
            }
            Serial.println();
            delay(400);

            DPRINTFLN("Fp power vector: ");
            Serial.print("^");
            for (int i = 0; i < cbke_length; i++) {
                Serial.print(cbke_vector[i].fp_power);
                Serial.print(";");
            }
            Serial.println();
            delay(400);

            DPRINTFLN("SNR vector: ");
            Serial.print("*");
            for (int i = 0; i < cbke_length; i++) {
                Serial.print(cbke_vector[i].snr);
                Serial.print(";");
            }
            Serial.println();
            delay(400);

            DPRINTFLN("LoS indicator vector:");
            Serial.print("$");
            for (int i = 0; i < cbke_length; i++) {
                Serial.print(cbke_vector[i].los_indicator);
                Serial.print(";");
            }
            Serial.println();
            delay(400);
            if (ENABLE_CIR) {
                DPRINTFLN("Magnitude vectors:");
                Serial.print("_");
                for (int i = 0; i < TOTAL_TAPS; i++) {
                    for (int j = 0; j <  min(TAP_LENGTH, cbke_length); j ++) {
                        Serial.print(pulse_vector[i].magnitude[j]);
                        Serial.print(";");
                    }
                    Serial.print("|");
                }
                Serial.println();
                delay(400);

                DPRINTFLN("Phase vectors:");
                Serial.print("&");
                for (int i = 0; i < TOTAL_TAPS; i++) {
                    for (int j = 0; j < min(TAP_LENGTH, cbke_length) ; j ++) {
                        Serial.print(pulse_vector[i].phase[j]);
                        Serial.print(";");
                    }
                    Serial.print("|");
                }
                Serial.println();
            }


            /* resetting counters */
            frame_counter = 0;
            cbke_counter = 0;

            /* resetting channel parameters */
            channel_idx = 0;
            decaduino.setChannel(channel_rotation[channel_idx]);
            setPcode(channel_idx);
            if (ENABLE_QUANTIZATION) {
                state = CBKE_QUANTIZE;
            }
            else {
                /* back to idle state, waiting for serial input */
                state = CBKE_IDLE;
            }
            break;

    case CBKE_QUANTIZE:
        Serial.println();
        Serial.print("/");
        nb_total_pulses = min(PULSE_SAMPLE_LENGTH, cbke_length);
        key_length = 0;
        for (int i = 0; i < TOTAL_TAPS; i++) {
            //get_pulse_idx_values(pulse_buffer, pulse_vector[i].magnitude, i, ACC_LENGTH, nb_total_pulses);
            key_length += quantize_chunk(pulse_vector[i].magnitude, TAP_LENGTH, &key_chunks[i][0]);         
        }  
        Serial.println();
        Serial.print("Key length:");
        Serial.println(key_length);
        // Serial.print("Bit balance: ");
        // Serial.println(check_bit_balance((char *) key_chunks, key_length));
        state = CBKE_IDLE;
        break;
    }

}