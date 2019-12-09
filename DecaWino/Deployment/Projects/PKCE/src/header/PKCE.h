#include <AES_config.h>
#include <printf.h>
#include "WProgram.h"
#include <AES.h>
#include <SPI.h>



//#define ANCHOR
#include <DecaDuino.h>
#define MY_ID 1

//#define _DEBUG_
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

#define ASCII_NUMBERS_OFFSET 48

#define AIR_SPEED_OF_LIGHT 299700000.0
#define DW1000_TIMEBASE 15.65E-12
#define COEFF AIR_SPEED_OF_LIGHT*DW1000_TIMEBASE

#define DELAY 5
#define DELAY_SLOW 500
#define DELAY_FAST 5

/* signature-related data */
#define MES_FOR_AVERAGE 32
#define N_CHUNKS 100
#define N_CHARACTERS 8 *  N_CHUNKS //each chunk is made of 8 characters

#define SLOW 0
#define FAST 1

#define SKEW_CORRECTION // comment to disable skew adjustement
#define REF_TEMPERATURE 45
#define SKEW_FACTOR 0.159


#define STATE_SERIAL 0
#define STATE_PING 1
#define STATE_PONG 2

byte quantize(float skew);
void set_n_chunks(int n);
uint16_t quantize_16(float skew);

void setup();
void print_value (char * str, byte * a, int bits);
void check_same (byte * a, byte * b, int bits);
void loop();
void boil(int target_temp);
void reset();
void switch_mode(int sp);
void send_last_frame_data();
void send_signature() ;
float getSkew();
int main();
