#ifndef DB_H
#define DB_H

#include <SPI.h>
#include <DecaDuino.h>

#ifndef NODE_ID
  #define NODE_ID 1
#endif


/* TImebase parameters */
#define DW1000_TIMEBASE 15.65E-12
#define DW1000_TIMEBASE_MS 60E6
#define TIMEOUT 1000

/* Serial parameters */
#define ASCII_NUMBERS_OFFSET 48

/* identifier */
#if (NODE_ID == 2)
  #define VERIFIER 1
  #define PROVER 0
#else // (NODE_ID == 1)
  #define VERIFIER 0
  #define PROVER 1
#endif

#define BUFFER_LEN 128

/* states */
#define IDLE 0
#define USB_SERIAL 1
#define PING 2
#define PONG 3

/* RX-TX parameters */
#define PLENGTH 64

/* DB parameters */
#define CHALLENGE_LENGTH_MS 6000
#define CHALLENGE_LENGTH_SYSTEM_CLK_UNITS CHALLENGE_LENGTH_MS * DW1000_TIMEBASE_MS


void setup_DB();
void loop_DB();
void send_db_results();


#endif
