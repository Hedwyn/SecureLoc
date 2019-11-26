#include <AES_config.h>
#include <printf.h>
#include "WProgram.h"
#include <AES.h>
#include <SPI.h>



//#define ANCHOR
#include <DecaDuino.h>
#define EXTENDED 1
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

#define ASCII_NUMBERS_OFFSET 48
//#define AIR_SPEED_OF_LIGHT 229702547.0
#define AIR_SPEED_OF_LIGHT 299700000.0
#define DW1000_TIMEBASE 15.65E-12
#define COEFF AIR_SPEED_OF_LIGHT*DW1000_TIMEBASE

#define X_CORRECTION 0.83
//#define Y_CORRECTION 0.230000000 // correction de la ligne 96 du B ?
#define Y_CORRECTION 0.000000000

#define DELAY 1
#define TIMEOUT 2000
#define INDEX_AVERAGE_MAX 0

#define STATE_SERIAL 0
#define STATE_PING 1
#define STATE_PONG 2

#define TWR_MSG_TYPE_UNKNOWN 0
#define TWR_MSG_TYPE_START 1
#define TWR_MSG_TYPE_ACK 2
#define TWR_MSG_TYPE_DATA_REPLY 3
#define NB_ROBOTS 2
void setup();
void print_value (char * str, byte * a, int bits);
void check_same (byte * a, byte * b, int bits);
void loop();
void boil(int target_temp);
int main();
