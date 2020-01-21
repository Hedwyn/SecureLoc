#include <SPI.h>
#include <DecaDuino.h>




/**
 * Les trois fonctions ci dessous permettent d'afficher des messages.
 * En commentant les bonnes lignes on affiche les messages du Debug ou du fonctionnement normal
 */

#define _DEBUG_
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

#define T23 100000000
#define FRAME_LEN 64

#ifndef NODE_ID
  #define NODE_ID 1
#endif

#define TWR_ENGINE_STATE_INIT 0
#define TWR_ENGINE_STATE_RX_ON 2
#define TWR_ENGINE_STATE_WAIT_START 3
#define TWR_ENGINE_STATE_SEND_ACK 4
#define TWR_ENGINE_STATE_SEND_DATA_REPLY 5
#define TWR_ENGINE_STATE_SERIAL 6

#define TWR_MSG_TYPE_UNKNOWN 0
#define TWR_MSG_TYPE_START 1
#define TWR_MSG_TYPE_ACK 2
#define TWR_MSG_TYPE_DATA_REPLY 3



#define TIME_SHIFT 500
#define ASCII_NUMBERS_OFFSET 48


void tag_setup();
int byte_array_cmp(byte b1[8], byte b2[8]);
void print_byte_array(byte b[8]);
void tag_RxTxConfig();
void loop();
