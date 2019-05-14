#include <AES.h>
#include <SPI.h>
#include <DecaDuino.h>

AES aes ;



//#define _DEBUG_  
#ifdef _DEBUG_
  #define DPRINTFLN  Serial.print
#else
  #define DPRINTFLN(format, args...) ((void)0)
#endif



#define _RUN_   
#ifdef _RUN_
  #define RPRINTF  Serial.print
#else
  #define RPRINTF(format, args...) ((void)0)
#endif


#define DW1000_TIMEBASE 15.65E-12

#define FRAME_LEN 64

#define TWR_ENGINE_STATE_INIT 1
#define TWR_ENGINE_STATE_RX_ON 2
#define TWR_ENGINE_STATE_WAIT_FRAME 3
#define TWR_ENGINE_STATE_MEMORISE_TIMESTAMP 4
#define TWR_ENGINE_STATE_SEND_ACK 5
#define TWR_ENGINE_STATE_WAIT_SENT 6
#define TWR_ENGINE_STATE_MEMORISE_T3 7
#define TWR_ENGINE_STATE_WAIT_BEFORE_SEND_DATA_REPLY 8
#define TWR_ENGINE_STATE_SEND_DATA_REPLY 9 
#define TWR_ENGINE_STATE_ENCRYPTION 10
#define TWR_ENGINE_STATE_SERIAL 11
#define TWR_ENGINE_STATE_SWITCH_RX_PARAMETERS 12

#define TWR_MSG_TYPE_UNKNOWN 0
#define TWR_MSG_TYPE_START 1
#define TWR_MSG_TYPE_ACK 2
#define TWR_MSG_TYPE_DATA_REPLY 3

#define TIME_SHIFT 500
#define MAX_STACK_SIZE 100

//control parameters for Swtich RX
#define SWITCH_PLENGTH 0
#define SWITCH_CHANNEL 0
#define SWITCH_PCODE 0

#define PLENGTH_SWITCH_DELAY 4000
#define PREAMBLE_SWITCH_DELAY 2000
#define CHANNEL_SWITCH_DELAY 5000

#define MIN_PLENGTH 64
#define MAX_PLENGTH 4096

#define PCODE_LIST_SIZE 20

#define CHANNEL_LIST_SIZE 5

typedef struct stack{
  uint64_t val[MAX_STACK_SIZE];
  int top;
}stack;

/* initializing timestamps stack */

stack timestamps;



uint64_t ts;

DecaDuino decaduino;
uint8_t txData[128];
uint8_t rxData[128],serialData[128];

uint16_t rxLen;
byte IdRobotRx [8]; //Id robot reçue
byte IdAncre [8];   //Id de l'ancre émettrice 
int state,serialFlag;
int plengthClk,pcodeClk,channelClk,currentPLength = MIN_PLENGTH,currentPcode = 1,currentChannel = 0;




char * hex = "0123456789abcdef" ;


void print_value (char * str, byte * a, int bits)
{
  Serial.print (str) ;
  bits >>= 3 ;
  for (int i = 0 ; i < bits ; i++)
    {
      byte b = a[i] ;
      Serial.print (hex [b >> 4]) ;
      Serial.print (hex [b & 15]) ;
    }
  Serial.println () ;
}

float return_clk_in_s(uint64_t ts) {
  return((float) ts * DW1000_TIMEBASE);
}


/**
 * Dans la boucle "setup" on initialise l'antenne UWB, on génère la clé privé  
 * et on initialise le buffer de reception. Si l'initialisation de l'antenne ne 
 * marche pas on fait clignoter la lED
 */

void setup() {
  byte error=0;
  delay(1000);
  DPRINTFLN("decaduino init start");
  pinMode(13, OUTPUT);
  pinMode(14, OUTPUT);
  //SPI.setSCK(13);
  SPI.setSCK(14);
  timestamps.top = 0;
  //set for anchors C and D
  //use pin 14 for A and B by uncommenting code lines above
  if ( !decaduino.init() ) {                    //En cas d'erreur on fait clignoter la LED
    error=decaduino.init();
    print_value("ID receive = ", &error, 64); 
    while(1) {
      digitalWrite(13, HIGH); 
      delay(50);    
      digitalWrite(13, LOW); 
      delay(50);    
    }
  
  }
  decaduino.setPreambleLength(2048);
  decaduino.setRxPcode(9);
  decaduino.setRxPrf(2);
  decaduino.setDrxTune(64);
  //ledecaduino.setTBR(110);
  




  // Set RX buffer
  decaduino.setRxBuffer(rxData, &rxLen);

  if(!decaduino.setChannel(2)) {
    Serial.println("failed to set Channel");
  }
  else {
    Serial.println("succeeded to set Channel");
  } 

  plengthClk = millis();
  pcodeClk = plengthClk;
  channelClk = plengthClk;
  


  //decaduino.setDrxTune(64);
  state = TWR_ENGINE_STATE_INIT;
  randomSeed(decaduino.getSystemTimeCounter());
}

void loop() {
  // DPRINTFLN(state);
  switch (state) {

/**
 * Etat TWR_ENGINE_STATE_INIT : 
 * On initialise notre machine à état du robot
 */
    case TWR_ENGINE_STATE_INIT:
      //decaduino.plmeRxDisableRequest();
      state = TWR_ENGINE_STATE_RX_ON;
      DPRINTFLN("Init state");
      break;

/**
 * Etat TWR_ENGINE_STATE_RX_ON : 
 * On active le module UWB en reception
 */

    case TWR_ENGINE_STATE_RX_ON:
      decaduino.plmeRxEnableRequest();
      if (serialFlag) {
        state = TWR_ENGINE_STATE_SERIAL;
      }
      else {
        state = TWR_ENGINE_STATE_SWITCH_RX_PARAMETERS;
      }
      break;

    case TWR_ENGINE_STATE_SERIAL:
      Serial.println("New UWB frame received:");
      for (int i = 0; i < 45; i++) {
        Serial.print((int) serialData[i]);
        Serial.print("|");
        
      }
      Serial.println();
      // printing timestamps in s
      /*
      Serial.println("Timestamps stack [raw]:");
      Serial.print("{");
      for (int i = 0; i < timestamps.top;i ++) {       
        Serial.print(return_clk_in_s(timestamps.val[i]) );
        Serial.print(";");       
      }
      Serial.println("}");
      */
      // printing timestamps (raw clock value)
      Serial.println("Timestamps stack [raw]:");
      Serial.print("{");
      for (int i = 1; i < timestamps.top;i ++) {       
        Serial.print((int) (timestamps.val[i]- timestamps.val[i-1])  );
        Serial.print(";");       
      }
      Serial.println("}");

      state = TWR_ENGINE_STATE_SWITCH_RX_PARAMETERS;
      break;
      
/**
 * Etat TWR_ENGINE_STATE_WAIT_FRAME : 
 * on attends un message start de la part d'une ancre. Si on en reçoit un,
 * on récupère l'Id de l'ancre éméttrice, Id du robot destinataire et on le compare au notre
 * La trame start se décompose comme ci dessous :
 * 
 * Type du message (1octet) | idRobotDestinataire(8 Octets) | idAnchor (8 octets) | iDNextAnchor(8 octets)
 */

    case TWR_ENGINE_STATE_SWITCH_RX_PARAMETERS:
      if (SWITCH_PLENGTH) {
        if (millis() - plengthClk > PLENGTH_SWITCH_DELAY) {
          
          plengthClk = millis();
          currentPLength = 2 * currentPLength;
          if (currentPLength > MAX_PLENGTH) {
            currentPLength = MIN_PLENGTH;
          }
      
          decaduino.setPreambleLength(currentPLength);
          Serial.print("Switching to preamble length :");
          Serial.println(currentPLength);
          state = TWR_ENGINE_STATE_RX_ON;
        }               
      }
      if (SWITCH_PCODE) {
        if (millis() - pcodeClk > PREAMBLE_SWITCH_DELAY) {
          
          pcodeClk = millis();
  
          currentPcode = (currentPcode + 1) % PCODE_LIST_SIZE;        
          decaduino.setRxPcode(currentPcode);
          Serial.print("Switching to preamble code :");
          Serial.println(currentPcode);
          state = TWR_ENGINE_STATE_RX_ON;
        }               
      }
      if (SWITCH_CHANNEL) {
        if (millis() - channelClk > CHANNEL_SWITCH_DELAY) {
          
          channelClk = millis();
  
          currentChannel = (currentChannel % CHANNEL_LIST_SIZE) + 1;        
          decaduino.setRxPcode(currentChannel);
          Serial.print("Switching to channel:");
          Serial.println(currentChannel);
          state = TWR_ENGINE_STATE_RX_ON;
        }               
      }
      state = TWR_ENGINE_STATE_WAIT_FRAME;
      break;
      
    case TWR_ENGINE_STATE_WAIT_FRAME:           //On regardera ici si la donnée nous est destiné ou non 
      //Serial.println(millis() - plengthClk);
      if ( decaduino.rxFrameAvailable() ) {
        for (int i = 0; i < 128; i++) {  
          serialData[i] = rxData[i];
          serialFlag = 1;
        }

        state = TWR_ENGINE_STATE_MEMORISE_TIMESTAMP;
            
      }
      else {
        state = TWR_ENGINE_STATE_SWITCH_RX_PARAMETERS;
      }
      
      
      break;
/**
 * Etat : TWR_ENGINE_STATE_MEMORISE_TIMESTAMP
 * On enregistre l'heure de réception du message start
 */
    case TWR_ENGINE_STATE_MEMORISE_TIMESTAMP:
      ts = decaduino.getLastRxTimestamp();           //On enregistre l'heure de réception
      timestamps.val[timestamps.top] = ts;
      if ( (timestamps.top == MAX_STACK_SIZE) || (timestamps.val[timestamps.top] < timestamps.val[0]) ) {
        timestamps.top = 0;
      }
      else {
        timestamps.top++;
      }

      state = TWR_ENGINE_STATE_RX_ON;
      break;

    default:
       state = TWR_ENGINE_STATE_INIT;
       break;
  }
}
 
