#include <AES_config.h>
#include <printf.h>
#include "WProgram.h"
#include <AES.h>
#include <SPI.h>
#include "PKCE.h"

#include <DecaDuino.h>
#define EXTENDED 1
#define ALOHA 0
#define ALOHA_COLLISION_DELAY 20
#define DMAX 10
#ifndef NB_ANCHORS
  #define NB_ANCHORS 4
#endif

#ifndef ANCHOR
  #define ANCHOR 1
#endif

#define SLOT_LENGTH 50000 //microseconds
#define SLOT_LENGTH_MS (SLOT_LENGTH / 1000)
#define IN_US 1E6 //microseconds

#define _DEBUG_   //comment to disable debug mode
#ifdef _DEBUG_
  #define DPRINTF  Serial.print
#else
  #define DPRINTF(format, args...) ((void)0)
#endif

#ifdef _DEBUG_
  #define DPRINTFLN  Serial.println
#else
  #define DPRINTFLN(format, args...) ((void)0)
#endif



#define ASCII_NUMBERS_OFFSET 48

#define AIR_SPEED_OF_LIGHT 299700000.0
#define DW1000_TIMEBASE 15.65E-12
#define COEFF AIR_SPEED_OF_LIGHT*DW1000_TIMEBASE

/* watchdogs */

#define TX_TIMEOUT 10
#define ACK_TIMEOUT SLOT_LENGTH_MS
#define START_TIMEOUT (NB_ANCHORS * SLOT_LENGTH_MS)
#define DATA_TIMEOUT SLOT_LENGTH_MS





#define TWR_ENGINE_STATE_INIT 0
#define TWR_ENGINE_STATE_SERIAL 1
#define TWR_ENGINE_STATE_WAIT_NEW_CYCLE 2
#define TWR_ENGINE_STATE_SEND_START 3
#define TWR_ENGINE_STATE_WAIT_ACK 4
#define TWR_ENGINE_STATE_WAIT_DATA_REPLY 5
#define TWR_ENGINE_STATE_EXTRACT_T2_T3 6
#define TWR_ENGINE_STATE_SEND_DATA_PI 7
#define TWR_ENGINE_STATE_IDLE 8




#define TWR_ENGINE_STATE_SEND_ACK 19
#define TWR_ENGINE_STATE_WAIT_SENT 20
#define TWR_ENGINE_STATE_MEMORISE_T3 21
#define TWR_ENGINE_STATE_WAIT_BEFORE_SEND_DATA_REPLY 22
#define TWR_ENGINE_STATE_SEND_DATA_REPLY 23
#define TWR_ENGINE_STATE_ENCRYPTION 24
#define TWR_ENGINE_STATE_MEMORISE_T2 25

/* frame types */
#define TWR_MSG_TYPE_UNKNOWN 0
#define TWR_MSG_TYPE_START 1
#define TWR_MSG_TYPE_ACK 2
#define TWR_MSG_TYPE_DATA_REPLY 3
#define NB_ROBOTS 2

void setup();
void print_byte_array(byte b[8]);
int byte_array_cmp(byte b1[8], byte b2[8]);
void anchor_loop();
int main();
