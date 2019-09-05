#include <AES.h>
#include <SPI.h>
#include <DecaDuino.h>

AES aes ;

#define ANCHOR 5

#define TIMEOUT 5000
#define _DEBUG_  
#define SERIAL_DEBUG
#ifdef SERIAL_DEBUG
  #define DPRINTFLN  Serial.println
#else
  #define DPRINTFLN(format, args...) ((void)0)
  
#endif

#ifdef SERIAL_DEBUG
  #define DPRINTF  Serial.print
#else
  #define DPRINTF(format, args...) ((void)0)
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
#define TWR_ENGINE_STATE_WAIT_POLL 3
#define TWR_ENGINE_STATE_MEMORISE_TIMESTAMP 4
#define TWR_ENGINE_STATE_SEND_ACK 5
#define TWR_ENGINE_STATE_WAIT_SENT 6
#define TWR_ENGINE_STATE_MEMORISE_T3 7
#define TWR_ENGINE_STATE_WAIT_BEFORE_SEND_DATA_REPLY 8
#define TWR_ENGINE_STATE_SEND_DATA_REPLY 9 
#define TWR_ENGINE_STATE_ENCRYPTION 10
#define TWR_ENGINE_STATE_SERIAL 11
#define TWR_ENGINE_STATE_SWITCH_RX_PARAMETERS 12
#define TWR_ENGINE_STATE_ANSWER 13
#define TWR_ENGINE_STATE_WAIT_FINAL 14
#define TWR_ENGINE_STATE_REPORT 15

#define TWR_MSG_TYPE_UNKNOWN 0
#define TWR_MSG_TYPE_START 1
#define TWR_MSG_TYPE_ACK 2
#define TWR_MSG_TYPE_DATA_REPLY 3

#define TIME_SHIFT 500
#define MAX_STACK_SIZE 20



#define PLENGTH_SWITCH_DELAY 4000
#define PREAMBLE_SWITCH_DELAY 2000
#define CHANNEL_SWITCH_DELAY 5000

#define MIN_PLENGTH 64
#define MAX_PLENGTH 4096

#define PCODE_LIST_SIZE 20

#define CHANNEL_LIST_SIZE 5
#define TWR_POLL 0x01
#define TWR_ANSWER 0x02
#define TWR_FINAL 0x03
#define TWR_REPORT 0x04

#define DEFAULT_PRESSURE 1013
#define DEFAULT_TEMP 25
#define DEFAULT_ASL 0

// LPP  packets
#define LPP_SHORT 0xF0
#define LPP_IDS_ANCHOR_POSITION 0x01
#define POS_REFRESH 50



// Anchor position structure
typedef struct AnchorPosition {
  float x;
  float y;
  float z;
} __attribute__((packed))AnchorPosition;

// Report struct
typedef struct report_payload{
  uint8_t pollRx[5];      // R1 timestamp
  uint8_t answerTx[5];    // T2 timestamp
  uint8_t finalRx[5];     // R3 timestamp
 
  float pressure;         // Pressure measurement at the anchor
  float temperature;      // Temperature of the pressure sensor
  float asl;              // Above Sea Level altitude
  uint8_t pressure_ok;    // Not 0 if the pressure information is correct
}__attribute__((packed)) report_payload;

typedef struct stack{
  uint64_t val[MAX_STACK_SIZE];
  int top;
}stack;


// initializing anchor position
AnchorPosition anchor_pos;



// initializing report payload
report_payload report;


// initializing timestamps stack 
stack timestamps;

float anchors_x[6] = {0,0,1.5,1.5,0.75,0.75};
float anchors_y[6] = {0,1.5,1.5,0,1.5,0};
float anchors_z[6] = {0,0,0,0,0,0};
int frames_counter = 0;

uint64_t R1,T2,R3,picoclk_marker;


DecaDuino decaduino;
uint8_t txData[128];
uint8_t rxData[128],pollData[128],finalData[128];
uint8_t mac_header[5] = {65,220,0,207,188};
uint16_t rxLen;
byte IdRobotRx [8]; //Id robot reçue
byte IdAncre [8];   //Id de l'ancre émettrice 
int state,serialFlag,pollFlag,finalFlag;
int plengthClk,pcodeClk,channelClk,currentPLength = MIN_PLENGTH,currentPcode = 1,currentChannel = 0,marker,teensy_clk,seq;
bool received =  false;

long convertClk(uint64_t  clk1, uint64_t  clk2) {
  return((clk2 - clk1)* 1565 / 1E8);
   
}

void encodeUint64On5Bytes(uint64_t from, uint8_t *to) {
  int check_val = 0;
  int pwr = 1;
  
  for (int i = 0; i <5; i++) {
    to[4 - i] = (uint8_t) ( (from >> (32 - 8 * i))& 0x00000000000000FF );
  }
  


  

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
   
    while(1) {
      digitalWrite(13, HIGH); 
      delay(50);    
      digitalWrite(13, LOW); 
      delay(50);    
    }
  
  }
  decaduino.setPreambleLength(128);
  decaduino.setRxPcode(9);
  
  decaduino.setTxPcode(9);
  
  decaduino.setTxPrf(64);
  decaduino.setRxPrf(64);
  
 
  
  //decaduino.setSfdTimeout(1200);
  decaduino.setPACSize(16);
  decaduino.setTBR(6800);
  
      // header
      for (int i =0; i <5; i++) {
        txData[i] = mac_header[i];
      }  



  // Set RX buffer
  decaduino.setRxBuffer(rxData, &rxLen);

  if(!decaduino.setChannel(2)) {
    DPRINTFLN("failed to set Channel");
  }
  else {
    DPRINTFLN("succeeded to set Channel");
  } 
  decaduino.displayRxTxConfig();
  plengthClk = millis();
  pcodeClk = plengthClk;
  channelClk = plengthClk;
  // tx header
  for (int i =0; i <5; i++) {
    txData[i] = mac_header[i];
  }
  /*
  if (!decaduino.setSmartTxPower(0) ) {
    DPRINTFLN("wrong argument for set STP");
  }

  if (decaduino.getSmartTxPower() != 0) {
    DPRINTFLN("STP failed");
  }

  decaduino.setPhrPower(18,15.5);
  decaduino.setSdPower(18,15.5);
 */


  //decaduino.setDrxTune(64);
  //state = TWR_ENGINE_STATE_INIT;
  state = TWR_ENGINE_STATE_RX_ON;
  randomSeed(decaduino.getSystemTimeCounter());
  anchor_pos.x = anchors_x[ANCHOR];
  anchor_pos.y = anchors_y[ANCHOR];
  anchor_pos.z = anchors_z[ANCHOR];
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

      state = TWR_ENGINE_STATE_WAIT_POLL;
      
        

      break;



      
/**
 * Etat TWR_ENGINE_STATE_WAIT_POLL : 
 * on attends un message start de la part d'une ancre. Si on en reçoit un,
 * on récupère l'Id de l'ancre éméttrice, Id du robot destinataire et on le compare au notre
 * La trame start se décompose comme ci dessous :
 * 
 * Type du message (1octet) | idRobotDestinataire(8 Octets) | idAnchor (8 octets) | iDNextAnchor(8 octets)
 */

      
    case TWR_ENGINE_STATE_WAIT_POLL:           //On regardera ici si la donnée nous est destiné ou non 
      //DPRINTFLN(millis() - plengthClk);
      
      if ( decaduino.rxFrameAvailable() ) {
        
        if ((rxData[21] = TWR_POLL) ){//  && (rxData[5] == ANCHOR)) {
          seq = rxData[22]; 
          state = TWR_ENGINE_STATE_MEMORISE_TIMESTAMP;
        }
       else {
        //state = TWR_ENGINE_STATE_RX_ON;
        decaduino.plmeRxEnableRequest();

       }
           
      }
      else {
        state = TWR_ENGINE_STATE_WAIT_POLL;       
      }
      
      
      
      break;
/**
 * Etat : TWR_ENGINE_STATE_MEMORISE_TIMESTAMP
 * On enregistre l'heure de réception du message start
 */
    case TWR_ENGINE_STATE_MEMORISE_TIMESTAMP:
      
      R1 = decaduino.getLastRxTimestamp();           //On enregistre l'heure de réception
      state = TWR_ENGINE_STATE_ANSWER;
      //state = TWR_ENGINE_STATE_RX_ON;
      break;

    case TWR_ENGINE_STATE_ANSWER:
      //delay(1);
      // dest addr
      for (int i = 0; i < 8; i++) {
        txData[5 + i] = rxData[13 + i];
        txData[13 + i] = rxData[5 + i];
      }
      txData[21] = TWR_ANSWER;
      txData[22] = rxData[22];

      /* appending LPP short packet */
      if (frames_counter == POS_REFRESH) {
        frames_counter = 0;
        txData[23] = LPP_SHORT;
        txData[24] = LPP_IDS_ANCHOR_POSITION;
        memcpy((void *)txData + 25,(void *) &anchor_pos, 12);
        decaduino.pdDataRequest(txData,37);
      }
      else {
        frames_counter++;
        decaduino.pdDataRequest(txData,23);
      }
      
      
      
      marker = millis();
      while (!decaduino.hasTxSucceeded() && (millis() -  marker < TIMEOUT));

      T2 = decaduino.getLastTxTimestamp(); 

      state = TWR_ENGINE_STATE_WAIT_FINAL;
      


      
      
      break;

    case TWR_ENGINE_STATE_WAIT_FINAL:
      decaduino.plmeRxEnableRequest();
      
      // back to waiting for a poll if timeout
      state = TWR_ENGINE_STATE_RX_ON;

      // waiting for a final frame
      received = false;
      while ((millis() -  marker < TIMEOUT) && !received)  {
        if (decaduino.rxFrameAvailable()) {    
          if ( (rxData[21] = TWR_FINAL) && (seq == rxData[22]) ) {
            
            received = true;
            for (int i = 0; i < 128; i++) {  
              finalData[i] = rxData[i];
              finalFlag = 1;
              serialFlag |= finalFlag;
              state = TWR_ENGINE_STATE_REPORT;           
            }
          }
          else {
            // not a final frame. Back to Rx ON
            DPRINTFLN("Missed final frame OR wrong SEQ number");
            state =  TWR_ENGINE_STATE_RX_ON;
            received = true;         
          }
        }
      }
      break;
    
    case TWR_ENGINE_STATE_REPORT:
      // header

      // dest addr
      for (int i = 0; i < 8; i++) {
        txData[5 + i] = rxData[13 + i];
        txData[13 + i] = rxData[5 + i];
      }
      txData[21] = TWR_REPORT;
      txData[22] = rxData[22];
      // Payload
      report.pressure = DEFAULT_PRESSURE;
      report.temperature = DEFAULT_TEMP;
      report.asl = DEFAULT_ASL;
      report.pressure_ok = 0;

      // memorizing timestamp
   
      R3 = decaduino.getLastRxTimestamp(); 

      
      encodeUint64On5Bytes(R1,report.pollRx);      
      encodeUint64On5Bytes(T2,report.answerTx);
      encodeUint64On5Bytes(R3,report.finalRx );
      // writing the payload to rxData
      memcpy((void *) txData + 23,(void *) &report,28);
     




      // 21 bytes header + 2 bytes (TYPE + SEQ) + 28 bytes payload = 51 bytes
      decaduino.pdDataRequest(txData,51);
      marker = millis();
      while (!decaduino.hasTxSucceeded() && (millis() -  marker < TIMEOUT));


      state = TWR_ENGINE_STATE_RX_ON;

      break;    
      
      

      
      

    default:
       state = TWR_ENGINE_STATE_INIT;
       break;
  }
}
 
