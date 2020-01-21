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

#ifndef NODE_ID
  #define NODE_ID 0
#endif

#define MASTER_ID 1

#if (NODE_ID == MASTER_ID)
  #define MASTER
#endif

#define SLOT_LENGTH 500000 //microseconds
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
#define CALIBRATION 0.9
#define SPEED_COEFF AIR_SPEED_OF_LIGHT*DW1000_TIMEBASE*CALIBRATION

/* watchdogs */

#define TX_TIMEOUT 10
#define ACK_TIMEOUT SLOT_LENGTH_MS
#define START_TIMEOUT (NB_ANCHORS * SLOT_LENGTH_MS)
#define DATA_TIMEOUT SLOT_LENGTH_MS




#define TWR_ENGINE_STATE_INIT 0
#define TWR_ENGINE_STATE_IDLE 1
#define TWR_ENGINE_STATE_SERIAL 2
#define TWR_ENGINE_PREPARE_RANGING 3
#define TWR_ENGINE_STATE_SEND_START 4
#define TWR_ENGINE_STATE_WAIT_ACK 5
#define TWR_ENGINE_STATE_WAIT_DATA_REPLY 6
#define TWR_ENGINE_STATE_EXTRACT_T2_T3 7
#define TWR_ENGINE_STATE_SEND_DATA_PI 8


/* TWR State */
#define TWR_ON_GOING 0
#define TWR_COMPLETE 1

/* frame types */
#define TWR_MSG_TYPE_UNKNOWN 0
#define TWR_MSG_TYPE_START 1
#define TWR_MSG_TYPE_ACK 2
#define TWR_MSG_TYPE_DATA_REPLY 3
#define NB_ROBOTS 2

/* Cooperative */
#define COOPERATIVE 1


void anchor_setup();
void anchor_RxTxConfig();
void print_byte_array(byte b[8]);
int byte_array_cmp(byte b1[8], byte b2[8]);
int get_tag_idx(byte tag_ID[8]);
int anchor_loop();
int anchor_loop(byte *myID, byte *myNextAnchorID);
