#include <AES_config.h>
#include <printf.h>
#include "WProgram.h"
#include <AES.h>
#include <SPI.h>

//#define ANCHOR
#include <DecaDuino.h>

#define WAITTIME 100 // set frequency here 
//#define _DEBUG_   //comment to disable debug mode
#ifdef _DEBUG_
  #define DPRINTF  Serial.print
#else
  #define DPRINTF(format, args...) ((void)0)
#endif

#ifdef _DEBUG_     //commenter cette ligne pour "supprimer" les print de test
  #define DPRINTFLN  Serial.println
#else
  #define DPRINTFLN(format, args...) ((void)0)
#endif

#define _RUN_   //commenter cette ligne pour "supprimer" les print de test
#ifdef _RUN_
  #define RPRINTF  Serial.print
#else
  #define RPRINTF(format, args...) ((void)0)
#endif

#define AIR_SPEED_OF_LIGHT 229702547.0
//#define AIR_SPEED_OF_LIGHT 299700000.0
#define DW1000_TIMEBASE 15.65E-12
#define COEFF AIR_SPEED_OF_LIGHT*DW1000_TIMEBASE

#define X_CORRECTION 1.0000000
//#define Y_CORRECTION 0.230000000 // correction de la ligne 96 du B ?
#define Y_CORRECTION 0.000000000

#define TIMEOUT 50
#define INDEX_AVERAGE_MAX 0

#define TWR_ENGINE_STATE_INIT 1
#define TWR_ENGINE_STATE_WAIT_NEW_CYCLE 2
#define TWR_ENGINE_STATE_SEND_START 3
#define TWR_ENGINE_STATE_WAIT_SEND_START 4
#define TWR_ENGINE_STATE_MEMORISE_T1 5
#define TWR_ENGINE_STATE_WATCHDOG_FOR_ACK 6
#define TWR_ENGINE_STATE_RX_ON_FOR_ACK 7
#define TWR_ENGINE_STATE_WAIT_ACK 8
#define TWR_ENGINE_STATE_MEMORISE_T4 9
#define TWR_ENGINE_STATE_WATCHDOG_FOR_DATA_REPLY 10
#define TWR_ENGINE_STATE_RX_ON_FOR_DATA_REPLY 11
#define TWR_ENGINE_STATE_WAIT_DATA_REPLY 12
#define TWR_ENGINE_STATE_EXTRACT_T2_T3 13

#define TWR_ENGINE_STATE_SEND_DATA_PI 14
#define TWR_ENGINE_STATE_IDLE 15
#define TWR_ENGINE_STATE_PREPARE_LOC 16

#define TWR_ENGINE_STATE_INIT_OFFSET 17

#define TWR_MSG_TYPE_UNKNOWN 0
#define TWR_MSG_TYPE_START 1
#define TWR_MSG_TYPE_ACK 2
#define TWR_MSG_TYPE_DATA_REPLY 3
#define NB_ROBOTS 2
void setup();
void print_value (char * str, byte * a, int bits);
void check_same (byte * a, byte * b, int bits);
void loop();
int main();

