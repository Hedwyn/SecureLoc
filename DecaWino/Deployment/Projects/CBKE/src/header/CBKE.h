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
 * @file CBKE.h
 * @author Baptiste Pestourie
 * @date 2020 May 1st
 * @brief Source file for the cooperative anchor firmware. This firmware is intended for DecaWino chips.
 * Anchors are fixed stations performing ranging with mobile tags.
 * The cooperative anchor firmware allow an anchor to design a tag to participate in a verification process. See the platform documentation for details.
 * @see https://github.com/Hedwyn/SecureLoc
 */
#ifndef CBKE_H
#define CBKE_H

#include <SPI.h>
#include <DecaDuino.h>
#include "quantize.h"

// #define DEBUG   //comment to disable debug mode
#ifdef DEBUG
  #define DPRINTF  Serial.print/**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTF(format, args...) ((void)0)
#endif

#ifdef DEBUG
  #define DPRINTFLN  Serial.println/**< When defined, enables debug ouput on the serial port*/
#else
  #define DPRINTFLN(format, args...) ((void)0)
#endif

#ifndef NODE_ID
  #define NODE_ID 1
#endif
/* RX-TX parameters */
#define CHANNEL 2
#define PLENGTH 64
#define PRF 16
#define PCODE 3

/* FSM */
#define CBKE_IDLE 0
#define CBKE_PING 1
#define CBKE_PONG 2
#define CBKE_COMPUTE_KEY 3
#define CBKE_QUANTIZE 4

/* Serial commands */
#define PROVER 0
#define VERIFIER 1
#define SET_PARAM 2
#define CBKE_LENGTH_P 0
#define PING_PONG_DELAY_P 1
#define PLENGTH_P 2
#define PCODE_P 3
#define EAVESDROPPER 4
#define PRF_P 5


/* MAC parameters */
#define CBKE_HEADER 7


/* CIR accumulator */
#define ACC_LENGTH 15
#define ACC_OFFSET 6
#define MEAN_WINDOW_LENGTH 3
#define REF_POINTS_ACC (ACC_LENGTH / MEAN_WINDOW_LENGTH)
#define TOTAL_TAPS REF_POINTS_ACC* NB_CHANNELS_EFFECTIVE
#define DISPLAY_ACCUMULATOR 0
#define DISPLAY_DELAY 500
#define ENABLE_CIR 1
#define NORMALIZE_CIR 1

/* CBKE parameters */
#define MAX_PULSE_SAMPLE_LENGTH 288

#define PING_PONG_DELAY 1/**Delay to wait before each tranmission in the ping-pong exchanges, in us */
#define SAMPLES_PER_BIT 3
#define ENABLE_CHANNEL_SWITCH 1
#define NB_CHANNELS 6

#if ENABLE_CHANNEL_SWITCH
  #define NB_CHANNELS_EFFECTIVE NB_CHANNELS
#else
  #define NB_CHANNELS_EFFECTIVE 1  
#endif

#if DISPLAY_ACCUMULATOR 
  #define PONG_TIMEOUT 1000 /**< In ms */
#else
  #define PONG_TIMEOUT 150/**< In ms */
#endif

#define CBKE_MAX_LENGTH 2000 /**< Maximum number of frames for a single CBKE protocol */


#if CBKE_MAX_LENGTH < MAX_PULSE_SAMPLE_LENGTH
  #define PULSE_SAMPLE_LENGTH CBKE_MAX_LENGTH
#else
  #define PULSE_SAMPLE_LENGTH MAX_PULSE_SAMPLE_LENGTH
#endif

#if ENABLE_CIR
  #define CBKE_LENGTH PULSE_SAMPLE_LENGTH /**< Total number of frames for a single CBKE protocol */
#else 
  #define CBKE_LENGTH 1000 /**< Total number of frames for a single CBKE protocol */
#endif
#define TAP_LENGTH (PULSE_SAMPLE_LENGTH / NB_CHANNELS_EFFECTIVE)

/* Quantization parameters */

#define KEY_CHUNK_LENGTH 2 * TAP_LENGTH
#define MAX_CHUNKS MAX_PULSE_SAMPLE_LENGTH
#define ENABLE_QUANTIZATION 1



typedef struct Sample{
    float rssi;
    float fp_power;
    float snr;
    float los_indicator;
}Sample;

typedef struct Pulse_sample{
  float magnitude[TAP_LENGTH];
  float phase[TAP_LENGTH];
}Pulse_sample;


void extract_sample();
void setPcode(int pcode_idx);
void CBKE_loop();
void CBKE_setup();

#endif