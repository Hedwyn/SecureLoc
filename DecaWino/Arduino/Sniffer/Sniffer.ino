#include <AES.h>
#include <SPI.h>
#include <DecaDuino.h>

AES aes ;


#define DISPLAY_TIMESTAMPS 1
#define TIMEOUT 6
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

//control parameters for Swtich RX
#define SWITCH_PLENGTH 0
#define SWITCH_CHANNEL 1
#define SWITCH_PCODE 0
#define SWITCH_RX 0//(SWITCH_PLENGTH ||SWITCH_CHANNEL || SWITCH_PCODE)

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

// initializing report payload
report_payload report;


// initializing timestamps stack 
stack timestamps;



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
  // 

  // check
  /*
  Serial.println("Encoding check:");
  Serial.println((int) from);
  for (int i = 0;i <5; i++) {
   
    check_val += (int) (to[4 - i] * pwr);
    pwr *= 256;  
  }
  Serial.println(check_val);
  */
  

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
  decaduino.setRxPrf(64);
  decaduino.setTxPcode(9);
  decaduino.setTxPrf(64);
 
  //decaduino.setSfdTimeout(128);
  //decaduino.setPACSize(64);
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
  //state = TWR_ENGINE_STATE_INIT;
  state = TWR_ENGINE_STATE_RX_ON;
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
      decaduino.plmeRxDisableRequest();
      decaduino.plmeRxEnableRequest();
      
      if (serialFlag) {
        state = TWR_ENGINE_STATE_SERIAL;
        Serial.println("\nRX ON time:");
        Serial.println(convertClk(picoclk_marker, decaduino.getSystemTimeCounter()));
      }
      else {
        if (SWITCH_RX) {
          state = TWR_ENGINE_STATE_SWITCH_RX_PARAMETERS;
        }
        else {
          state = TWR_ENGINE_STATE_WAIT_POLL;
        }
       
      }
      break;

    case TWR_ENGINE_STATE_SERIAL:
      Serial.println("New UWB frame received:");

      if (pollFlag) {
        for (int i = 0; i < 45; i++) {
          Serial.print((int) pollData[i]);
          Serial.print("|");
          
        }
        Serial.println();
        pollFlag = 0;
      }

      if (finalFlag) {
        for (int i = 0; i < 45; i++) {
          Serial.print((int) finalData[i]);
          Serial.print("|");
          
        }
        Serial.println();
        finalFlag = 0;
      }


   
      // printing timestamps in s
      /*
      Serial.println("Timestamps stack [raw]:");
      Serial.print("{");
      for (int i = 0; i < timestamps.top;i ++) {       
        Serial.print((double) (15.65 * 10E-12 * timestamps.val[i]) );
        Serial.print(";");       
      }
      Serial.println("}");
      */
      
      // printing timestamps (raw clock value)
      if (DISPLAY_TIMESTAMPS) {
        Serial.println("Timestamps stack [raw]:");
        Serial.print("{");
        for (int i = 1; i < timestamps.top;i ++) {       
          //Serial.print(convertClk(timestamps.val[i - 1], timestamps.val[i])) ;
          Serial.print((long) (timestamps.val[i - 1], timestamps.val[i])) ;
          Serial.print(";");       
        }
        Serial.println("}");
      }
     
      if (SWITCH_RX) {
        state = TWR_ENGINE_STATE_SWITCH_RX_PARAMETERS;
      }
      else {
        state = TWR_ENGINE_STATE_WAIT_POLL;
        Serial.println("Serial time:");
        Serial.println(convertClk(picoclk_marker, decaduino.getSystemTimeCounter()));
        
      }
      break;
      
/**
 * Etat TWR_ENGINE_STATE_WAIT_POLL : 
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
      state = TWR_ENGINE_STATE_WAIT_POLL;
      break;
      
    case TWR_ENGINE_STATE_WAIT_POLL:           //On regardera ici si la donnée nous est destiné ou non 
      //Serial.println(millis() - plengthClk);
      
      if ( decaduino.rxFrameAvailable() ) {
      
        //if (true) {
        if ((rxData[5] == 1) && (rxData[21] == TWR_POLL)) {
        
            Serial.println("Period time:");
            Serial.println(convertClk(picoclk_marker, decaduino.getSystemTimeCounter()));
         
            Serial.println("Period time [Duino]:");
            Serial.println(millis() - teensy_clk);          
            Serial.print("SEQ number:");
            Serial.println(seq);
            picoclk_marker = decaduino.getSystemTimeCounter();
            teensy_clk = millis();
            
            for (int i = 0; i < 128; i++) {  
              pollData[i] = rxData[i];
              pollFlag = 1;
              serialFlag |= pollFlag;
            }
          
  
          state = TWR_ENGINE_STATE_MEMORISE_TIMESTAMP;
        }
        
       else {
        //state = TWR_ENGINE_STATE_RX_ON;
        decaduino.plmeRxEnableRequest();

       }
           
      }
      else {
        if (SWITCH_RX) {
          state = TWR_ENGINE_STATE_SWITCH_RX_PARAMETERS;
        }
        else {
          state = TWR_ENGINE_STATE_WAIT_POLL;
        }
      }
      
      
      
      break;
/**
 * Etat : TWR_ENGINE_STATE_MEMORISE_TIMESTAMP
 * On enregistre l'heure de réception du message start
 */
    case TWR_ENGINE_STATE_MEMORISE_TIMESTAMP:
      switch (rxData[21]) {
        case TWR_POLL:
          R1 = decaduino.getLastRxTimestamp();
          Serial.println("POLL");
          break;
        case TWR_ANSWER:
          T2 = decaduino.getLastRxTimestamp();
          Serial.println("ANSWER");
          Serial.println("Elapsed time (T2 - R1):");
          Serial.print("$");
          Serial.println((long) (T2 - R1));          
          break;
        case TWR_FINAL:
          Serial.println("FINAL");
          R3 = decaduino.getLastRxTimestamp();
          Serial.println("Elapsed time (R3 - T2):");
          Serial.print("#");
          Serial.println((long) (R3 - T2));
          
          break;
        case TWR_REPORT:        
          Serial.println("REPORT");
          break;          
        default:
          Serial.println("Unknown frame type received");
          break;
      }         

      if (DISPLAY_TIMESTAMPS) {
        timestamps.val[timestamps.top] = decaduino.getLastRxTimestamp();
        if ( (timestamps.top == MAX_STACK_SIZE) || (timestamps.val[timestamps.top] < timestamps.val[0]) ) {
          timestamps.top = 0;
        }
        else {
          timestamps.top++;
        }
      }




      //state = TWR_ENGINE_STATE_ANSWER;
      state = TWR_ENGINE_STATE_RX_ON;
      break;

    case TWR_ENGINE_STATE_ANSWER:
      // header
      for (int i =0; i <5; i++) {
        txData[i] = mac_header[i];
      }
      // dest addr
      for (int i = 0; i < 8; i++) {
        txData[5 + i] = rxData[13 + i];
        txData[13 + i] = rxData[5 + i];
      }
      txData[21] = TWR_ANSWER;
      txData[22] = rxData[22];
      Serial.println("Sending ANSWER...");
      //decaduino.pdDataRequest(txData,23,1,R1 + 30000000);
      decaduino.pdDataRequest(txData,23);
      marker = millis();
      while (!decaduino.hasTxSucceeded() && (millis() -  marker < TIMEOUT));
 
      Serial.println("ANSWER success !");
      T2 = decaduino.getLastTxTimestamp(); 

      state = TWR_ENGINE_STATE_WAIT_FINAL;
      marker = millis();
      
      break;

    case TWR_ENGINE_STATE_WAIT_FINAL:
      decaduino.plmeRxEnableRequest();
      
      // back to waiting for a poll if timeout
      state = TWR_ENGINE_STATE_RX_ON;

      // waiting for a final frame
      received = false;
      while ((millis() -  marker < TIMEOUT) && !received)  {
        if (decaduino.rxFrameAvailable()) {
          Serial.println("FINAL received !");
          Serial.print("SEQ number:");
          Serial.println(rxData[22]);       
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
            Serial.println("Missed final frame OR wrong SEQ number");
            state =  TWR_ENGINE_STATE_RX_ON;
            received = true;         
          }
        }
      }
      break;
    
    case TWR_ENGINE_STATE_REPORT:
      // header
      for (int i =0; i <5; i++) {
        //txData[i] = mac_header[i];
        txData[i] = rxData[i];
      }
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
      Serial.println("Elapsed time (T2 - R1)");
      Serial.print("$");      
      Serial.println((long)(T2- R1)); 
      if (DISPLAY_TIMESTAMPS) {
        timestamps.val[timestamps.top] = R3;
        if ( (timestamps.top == MAX_STACK_SIZE) || (timestamps.val[timestamps.top] < timestamps.val[0]) ) {
          timestamps.top = 0;
        }
        else {
          timestamps.top++;
        }
      }
      
      encodeUint64On5Bytes(R1,report.pollRx);      
      encodeUint64On5Bytes(T2,report.answerTx);
      encodeUint64On5Bytes(R3,report.finalRx );
      // writing the payload to rxData
      memcpy((void *) txData + 23,(void *) &report,28);
     


      Serial.println("Sending REPORT...");
      Serial.println("Total time:");
      Serial.println((double) ((decaduino.getSystemTimeCounter() - picoclk_marker) * 15.65E-6));
      // 21 bytes header + 2 bytes (TYPE + SEQ) + 28 bytes payload = 51 bytes
      decaduino.pdDataRequest(txData,51);
      marker = millis();
      while (!decaduino.hasTxSucceeded() && (millis() -  marker < TIMEOUT));
      Serial.println("REPORT success !");

      state = TWR_ENGINE_STATE_RX_ON;

      break;    
      
      

      
      

    default:
       state = TWR_ENGINE_STATE_INIT;
       break;
  }
}
 
