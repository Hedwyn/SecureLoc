#ifndef SKEW_AUTHENTICATION_H
#define SKEW_AUTHENTICATION_H

#include <SPI.h>
#include <DecaDuino.h>

/* identifier */
#ifndef NODE_ID
  #define NODE_ID 1
#endif

#if (NODE_ID == 2)
  #define VERIFIER 1
  #define PROVER 0
#else // (NODE_ID == 1)
  #define VERIFIER 0
  #define PROVER 1
#endif

/* TImebase parameters */
#define AIR_SPEED_OF_LIGHT 299700000.0
#define DW1000_TIMEBASE 15.65E-12
#define CALIBRATION 0.9
#define SPEED_COEFF 4.2255E-3//AIR_SPEED_OF_LIGHT*DW1000_TIMEBASE*CALIBRATION
#define DW1000_TIMEBASE_MS 60E6
#define AIR_SPEED_OF_LIGHT 299700000
#define DUTY_CYCLE 25 //in %
#define FRAME_TIME_US 4180
#define AVERAGE_LENGTH 50

//#define SLEEP_TIME FRAME_TIME_US * (100 / DUTY_CYCLE)
#define SLEEP_TIME 37620
/* Serial parameters */
#define ASCII_NUMBERS_OFFSET 48

#if (VERIFIER)
  #define TIMEOUT 3//VERIFIER?2:10
#else
  #define TIMEOUT 10
#endif

#define BUFFER_LEN 128

/* states */
#define PING 0
#define PONG 1

/* RX-TX parameters */
#define PLENGTH 4096
#define LONG_PREAMBLE 4096
#define SHORT_PREAMBLE 128
#define CHANNEL 1
#define PAYLOAD_LENGTH 1

/* Challenge parameters */
#define N_TOTAL_FRAMES 2000
#define SIGNATURE_LENGTH (N_TOTAL_FRAMES / AVERAGE_LENGTH)
#define T23 38000000 //21000000
#define GUARD_TIME 3000000
#define LOCALIZE 0

/* distance calculations */
#define DMIN 0
#define DMAX 10

/* skew correction */
#define SKEW_CORRECTION 1
#define T_REF 41.2 /* reference temperature used for calculations */
#define SKEW_CORRECTION_COEFF 0.17 // should be adjusted for every tag



void setup_DB();
void loop_DB();
void send_db_results();


#endif
