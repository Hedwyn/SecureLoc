#include <AES_config.h>
#include <printf.h>



#include <AES.h>
#include <SPI.h>
#include<DW1000.h>

#include <DecaDuino.h>

AES aes ;

/**
 * Les trois fonctions ci dessous permettent d'afficher des messages.  
 * En commentant les bonnes lignes on affiche les messages du Debug ou du fonctionnement normal
 */


#define WAITTIME 200 // set frequency here 
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

#define TIMEOUT 200
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
#define NB_ROBOTS 1

int i;
unsigned long time;
float rssi;
int rxFrames;
byte succ;
byte nbrand [8];     //nb alÃƒÂ©a ÃƒÂ  crypter et son identifiant
byte rxIdentifiant[8];  // /!\ identifiant de l'ÃƒÂ©metteur robot
byte identifiant[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0A}; // identifiant de l'ancre
byte identifiantAncreRx[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idNextAncreTx[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B};
byte idNextAncreRx[8] ={0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idRobotTx[NB_ROBOTS][8]= { {0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03}};
                                                                  
byte IdRobotRx[8];
byte key [2*N_BLOCK] = { 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
                         0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
                         0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
                         0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03 };   //clÃƒÂ©
byte cipher [N_BLOCK] ; //donnÃƒÂ©es encryptÃƒÂ©es
byte check [N_BLOCK] ;  //contient le msg dÃƒÂ©cryptÃƒÂ©
char * hex = "0123456789abcdef" ;

uint64_t t1, t2, t3, t4;
uint64_t  mask = 0xFFFFFFFFFF;
int32_t tof;
int32_t tof_skew;
double distance;
double distance_skew;
float average;
int unsigned iAverage;
int unsigned iInitialisation=0;
double processTime;
DecaDuino decaduino;
DW1000Class dw1000;
uint8_t txData[128];
uint8_t rxData[128];
uint16_t rxLen;
int state;
int timeout;

int timeoutWait;
boolean warning;
int print_time = 0;


/**
 * Dans la boucle "setup" on initialise l'antenne UWB, on gÃƒÂ©nÃƒÂ¨re la clÃƒÂ© privÃƒÂ©  
 * et on initialise le buffer de reception. Si l'initialisation de l'antenne ne 
 * marche pas on fait clignoter la lED. Print value nous permet d'afficher la valeur de string en numÃƒÂ©rique
 * La fonction check_same vÃƒÂ©rifie la correspondance entre le message dÃƒÂ©crypter
 * et le message en clair
 */


void setup() {
  byte error=0;
  delay(1000);
  DPRINTFLN("decaduino init start");
  pinMode(13, OUTPUT);
  //pinMode(14, OUTPUT);
  SPI.setSCK(14);
  

  //SPI.beginTransaction(SPISettings(14000000, MSBFIRST, SPI_MODE0));
  //SPI.setSCK(14)-
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
  
  
  // Set RX buffer
  decaduino.setRxBuffer(rxData, &rxLen);

  /* setting up Pulse Repetition Frequency */
  decaduino.setTxPrf(1);
  decaduino.setRxPrf(1);
  //decaduino.setDrxTune(64);
  decaduino.setTxPcode(4);
  decaduino.setRxPcode(4);
  
  state = TWR_ENGINE_STATE_IDLE;

  succ = aes.set_key (key, 32) ;      //initialisation de la clÃƒÂ©
      if (succ != SUCCESS)
        DPRINTFLN ("Failure set_key") ; 

 average=0;
 iAverage=0;
 
 /*
 if (!decaduino.setTxPrf(1)) {
  DPRINTFLN("Failed to st Tx PRF to 64");
 }
 if (!decaduino.setRxPrf(1)) {
  DPRINTFLN("Failed to set Rx PRF to 64");
 }
 
 if (!decaduino.setTxPcode(1)) {
  DPRINTFLN("Failed to st Tx PRF to 64");
 }
 if (!decaduino.setRxPcode(1)) {
  DPRINTFLN("Failed to set Rx PRF to 64");
 }

 if (!decaduino.setChannel(1)) {
  DPRINTFLN("Failed to set Rx PRF to 64");
 }
 
*/

 if (!decaduino.setPreambleLength(256)) {
  DPRINTFLN("Failed to set Rx PRF to 64");
 }




 
 decaduino.plmeRxEnableRequest();
 

 DPRINTFLN("decaduino init finished");
 RPRINTF(decaduino.getPreambleLength());
  
}


void print_value (char * str, byte * a, int bits) //sert ÃƒÂ  afficher les valeurs
{
  DPRINTF (str) ;
  bits >>= 3 ;
  for (int i = 0 ; i < bits ; i++)
    {
      byte b = a[i] ;
      DPRINTF (hex [b >> 4]) ;
      DPRINTF (hex [b & 15]) ;
    }
  DPRINTFLN () ;
}


void print_value_raspberry ( byte * a, int bits) //sert ÃƒÂ  afficher les valeurs
{
  bits >>= 3 ;
  for (int i = 0 ; i < bits ; i++)
    {
      byte b = a[i] ;
      RPRINTF (hex [b >> 4]) ;
      RPRINTF (hex [b & 15]) ;
    }
}



void check_same (byte * a, byte * b, int bits) {   //vÃƒÂ©rifie la correspondance entre deux donnÃƒÂ©es
  bits >>= 3 ;
  for (byte i = 0 ; i < bits ; i++)
    if (a[i] != b[i])
      {
        DPRINTFLN ("Failure plain != check") ;
        return ;
      }
}

int next_bot_idx = NB_ROBOTS - 1; //gives the index of the next robot to lcoalize 
void loop() {
 

  
  
  switch (state) {
  
/**
 * Etat TWR_ENGINE_STATE_INIT : 
 * On initialise notre machine ÃƒÂ  ÃƒÂ©tat du robot
 */   
  
    case TWR_ENGINE_STATE_INIT:
      decaduino.plmeRxDisableRequest();
      state = TWR_ENGINE_STATE_WAIT_NEW_CYCLE; 
      break;
      
    case TWR_ENGINE_STATE_WAIT_NEW_CYCLE:
      iInitialisation=0;
      delay(500); //increase resfresh rate here
      //delay(200);
      DPRINTFLN("New TWR");
      state = TWR_ENGINE_STATE_SEND_START;
      // getting the index of the next robot to localize
      if (next_bot_idx == NB_ROBOTS - 1) {
        next_bot_idx =0;
      }
      else {
        next_bot_idx++;       
      }
      DPRINTFLN(next_bot_idx);
      break;

    case TWR_ENGINE_STATE_SEND_START:     //on dÃƒÂ©finie la trame de start
      txData[0] = TWR_MSG_TYPE_START;     // Trame ÃƒÂ©mise : idRobot | idAncreTx | idNextAncre

      // getting temperature
      /*
      DPRINTFLN("temperature:\n");
      DPRINTFLN(decaduino.getTemperature());
      DPRINTFLN("\n");

      DPRINTFLN("voltage:\n");
      DPRINTFLN(decaduino.getVoltage());
      DPRINTFLN("\n");
      */

     
      
      for(int i=0; i<8; i++){
        txData[1+i]=idRobotTx[next_bot_idx][i];
        
        txData[9+i]=identifiant[i];
        txData[17+i]=idNextAncreTx[i];   
      }
      for (i=26;i <127;i++) {
        txData[i] = 0;
      }
      
      
      txData[25]=0;
      
      if( decaduino.pdDataRequest(txData, 26) ){
        
       
        

        
      }else{
        DPRINTFLN("pb with pDataRequest");
      }

      state = TWR_ENGINE_STATE_WAIT_SEND_START;
      break;

    case TWR_ENGINE_STATE_WAIT_SEND_START:
      
      if ( decaduino.hasTxSucceeded() ){
        
        state = TWR_ENGINE_STATE_MEMORISE_T1;
      }else{
        // DPRINTFLN("Tx has failed");
      }
      break;

    case TWR_ENGINE_STATE_MEMORISE_T1:    //on enregistre l'heure d'envoie
      time = micros();
      t1 = decaduino.getLastTxTimestamp();
      state = TWR_ENGINE_STATE_WATCHDOG_FOR_ACK;
      break;

    case TWR_ENGINE_STATE_WATCHDOG_FOR_ACK:
      timeout = millis() + TIMEOUT;
      state = TWR_ENGINE_STATE_RX_ON_FOR_ACK;
      break;     

    case TWR_ENGINE_STATE_RX_ON_FOR_ACK:
      decaduino.plmeRxEnableRequest();
      state = TWR_ENGINE_STATE_WAIT_ACK;
      break;

    case TWR_ENGINE_STATE_WAIT_ACK:
      if ( millis() > timeout ) {
        state = TWR_ENGINE_STATE_IDLE;    //pb ici
        DPRINTFLN("timeout");
      } else {
  
        if ( decaduino.rxFrameAvailable() ) {   // Si on a reÃƒÂ§u le ack on mÃƒÂ©morise l'heure de rÃƒÂ©ception
          rssi = decaduino.getRSSI();
     
           
          if ( rxData[0] == TWR_MSG_TYPE_ACK ) {    //On regarde ici si la donnÃƒÂ©e nous est destinÃƒÂ© ou non -
            for ( i=0; i<8; i++){
                rxIdentifiant[i]=rxData[i+1]; //On rÃƒÂ©cupÃƒÂ¨re l'identifiant
            }
            if( (*(uint64_t*) rxIdentifiant) == (*(uint64_t*) identifiant) ){//si c'est le bon id on passe ÃƒÂ  l'ÃƒÂ©tape suivante
              state = TWR_ENGINE_STATE_MEMORISE_T4;   //
            }else{
                DPRINTFLN("bad robot id");
                print_value("RX ID = ", rxIdentifiant, 64 );
                print_value("MY ID = ", identifiant, 64 );
            }
          } else state = TWR_ENGINE_STATE_RX_ON_FOR_ACK; // - sinon on retourne dans cet ÃƒÂ©tat 
        }
        /*else if (print_time) {
          DPRINTFLN("pTime if no ack:\n");
          DPRINTFLN((int) micros() - p_time);
          p_time = micros();
          print_time = 0;
        }*/
        

      }
      break;

    case TWR_ENGINE_STATE_MEMORISE_T4:            //Heure de rÃƒÂ©ception du ack
      t4 = decaduino.getLastRxTimestamp();
      state = TWR_ENGINE_STATE_WATCHDOG_FOR_DATA_REPLY;
      break;

    case TWR_ENGINE_STATE_WATCHDOG_FOR_DATA_REPLY:
      timeout = millis() + TIMEOUT;
      state = TWR_ENGINE_STATE_RX_ON_FOR_DATA_REPLY;
      break;     

    case TWR_ENGINE_STATE_RX_ON_FOR_DATA_REPLY:
      decaduino.plmeRxEnableRequest();
      state = TWR_ENGINE_STATE_WAIT_DATA_REPLY;
      break;

    case TWR_ENGINE_STATE_WAIT_DATA_REPLY://on attends la rep
      if ( millis() > timeout ) {
        state = TWR_ENGINE_STATE_IDLE;
      } else {
        if ( decaduino.rxFrameAvailable() ) {
          RPRINTF("Total processing time : ");
          RPRINTF((int)(micros() - time) );
          RPRINTF("\n");
          
    
          if ( rxData[0] == TWR_MSG_TYPE_DATA_REPLY ) { //Si le message est de type data, on passe ÃƒÂ  l'ÃƒÂ©tape de rÃƒÂ©cup sinon on att
            for ( i=0; i<8; i++){
                
                rxIdentifiant[i]=rxData[42+i]; //On rÃƒÂ©cupÃƒÂ¨re l'identifiant
            }
            if( (*(uint64_t*) rxIdentifiant) == (*(uint64_t*) identifiant) ){//si c'est le bon id on passe ÃƒÂ  l'ÃƒÂ©tape suivante
                state = TWR_ENGINE_STATE_EXTRACT_T2_T3;
            } else {
              DPRINTFLN("bad robot id");
              print_value("RX ID = ", rxIdentifiant, 64 );
              print_value("MY ID = ", identifiant, 64 );
              print_value("content buffer = ", rxData, 392 );
            }
          } else state = TWR_ENGINE_STATE_RX_ON_FOR_DATA_REPLY;
        }
      }
      break;

    case TWR_ENGINE_STATE_EXTRACT_T2_T3: //Etat d'extraction des distances. DÃƒÂ©cryptage et id 
      for ( i=0; i<16; i++){    //on extrait la donnÃƒÂ©e cryptÃƒÂ©e
        cipher[i]=rxData[17+i];     
      }
      
      succ = aes.decrypt (cipher, check) ;    //on dÃƒÂ©crypte
      if (succ != SUCCESS)
        DPRINTFLN ("Failure decrypt") ;
        
      for ( i=0; i<8; i++){
        nbrand[i]=rxData[33+i];   //On rÃƒÂ©cupÃƒÂ¨re le nb alÃƒÂ©atoire en clair
        rxIdentifiant[i]=check[i+8]; //On rÃƒÂ©cupÃƒÂ¨re l'identifiant
      }
      
      succ = SUCCESS;
      
      check_same (nbrand, check, 16) ;    //on vÃƒÂ©rifie que nb rand dÃƒÂ©codÃƒÂ© est le bon
      print_value ("Nb alea = ", nbrand, 64) ;
      DPRINTFLN();
      print_value ("CHECK = ", check, 128) ;
      DPRINTFLN();

     
      if (succ == SUCCESS){
        t2 = decaduino.decodeUint64(&rxData[1]);  //Data 1 contient l'heure de reception de B.  
        t3 = decaduino.decodeUint64(&rxData[9]);  //Data 9 continent l'heure de rÃƒÂ©ÃƒÂ©mission de B
        tof = (t4 - t1 - (t3 - t2))/2;            //On calcule le temps de voyage puis la distance. 
        tof_skew = (((t4 - t1) & mask) - (1+1.0E-6*decaduino.getLastRxSkew())*((t3 - t2) & mask))/2;
        
        distance = tof*COEFF*X_CORRECTION + Y_CORRECTION;
        distance_skew = tof_skew*COEFF*X_CORRECTION + Y_CORRECTION;
        print_value("ROBOT = ", rxIdentifiant, 64);
       
        DPRINTFLN();
        DPRINTF("ToF=");                 //On affiche le ToF
        DPRINTF(tof, HEX);
        DPRINTF(" d=");                  //On affiche la distance entre l'ancre et le robot
        DPRINTF(distance);
        DPRINTFLN();
        
        state = TWR_ENGINE_STATE_SEND_DATA_PI;
      }
      else
      {
        DPRINTF("Echec du dÃƒÂ©codage/ transmission non identifiÃƒÂ©e");
        DPRINTFLN();
        state = TWR_ENGINE_STATE_IDLE;
      }      
      break;
      
 /**
 * Etat TWR_ENGINE_STATE_SEND_DATA_PI : 
 * Dans cet ÃƒÂ©tat on transmet la trame de l'ancre ÃƒÂ  la RasPI.
 * la trame est composÃƒÂ© comme suit :
 * Trame : *IdAncre|idRobot#
 * 
 * le caractÃƒÂ¨re * sert de "balise" de dÃƒÂ©marrage, le caractÃƒÂ¨re | sÃƒÂ©pare les deux Id et 
 * le caractÃƒÂ¨re # indique la fin de la trame
 */
    
    case TWR_ENGINE_STATE_SEND_DATA_PI :
      /* if the speed exceed 12km.h-1, send a warning message*/
      if (average-distance>=1.0 || average-distance<=-1.0)
      {
        warning=true;
      } else {
        warning=false;
      }
      
     
      
     
      if (warning)
      {
        //RPRINTF("*W : speed exceed 12km.h-1#\n");
      }
      RPRINTF("*");                   //RPRINTF correspont ÃƒÂ  la communication avec la RasPI
      //Trame * idAncre | idRobot| distance #
      print_value_raspberry(identifiant,64);
     
      RPRINTF("|"); 

      //print_value_raspberry(rxIdentifiant,64);
      print_value_raspberry(idRobotTx[next_bot_idx],64);
      RPRINTF("|"); 
      //RPRINTF(average);
      RPRINTF(distance_skew);
      RPRINTF("|");

      /*RPRINTF("|"); 
      //RPRINTF(average);
      RPRINTF(distance_skew);
      RPRINTF("|");*/
      /* timestamps */
      RPRINTF((int) t1);
      RPRINTF("|");

      RPRINTF((int) t2);
      RPRINTF("|");

      RPRINTF( (int) t3);
      RPRINTF("|");

      RPRINTF( (int) t4);
      RPRINTF("|");

      processTime = (double) (tof_skew * 15.65E-6);
      RPRINTF( (int) (t4 - t1));
      //RPRINTF(processTime);
      RPRINTF("|");


     
      RPRINTF( (int) (t3 - t2));
      RPRINTF("|");

      



      RPRINTF( (int) ( tof) );
      RPRINTF("|");
      RPRINTF( (int) ( tof_skew) );
      RPRINTF("|");
      RPRINTF(decaduino.getLastRxSkew());
      RPRINTF("|");
      RPRINTF(decaduino.getTemperature());
      RPRINTF("|");
      

      /* RSSI */
      
      RPRINTF(rssi );
      
      RPRINTF("#\n");
      decaduino.plmeRxEnableRequest();
      state= TWR_ENGINE_STATE_IDLE;
      break;

/**
 * Etat TWR_ENGINE_STATE_IDLE : 
 * On  attends de recevoir une trame. On regarde si elle nous est adressÃƒÂ©e.
 * Si oui on reprÃƒÂ©pare la communication.
 */

    case TWR_ENGINE_STATE_IDLE :
      
      if ( (*(uint64_t*) idNextAncreTx) == (*(uint64_t*) identifiant) ) //On regarde si l'ancre est la prochaine ÃƒÂ  parlÃƒÂ©
      {
        state = TWR_ENGINE_STATE_PREPARE_LOC;
      }else{
        if ( decaduino.rxFrameAvailable() ) {  
      
        if ( rxData[0] == TWR_MSG_TYPE_START ) {    //trame ancre = dest | idAnchor | idNextAchor
          for (int i=0; i<8; i++){
            idNextAncreRx[i] = rxData[i+17];
          }
          decaduino.plmeRxEnableRequest();
            if ( (*(uint64_t*) idNextAncreRx) == (*(uint64_t*) identifiant) ) //On regarde si l'ancre est la prochaine ÃƒÂ  parlÃƒÂ©
            {
              state = TWR_ENGINE_STATE_PREPARE_LOC;
              timeoutWait = millis() + TIMEOUT;
            }
          }
            decaduino.plmeRxEnableRequest();
          } else {
            // no frame received, possibility than nobody speak 
            iInitialisation++;
             if (iInitialisation> WAITTIME) { //To SET
                state = TWR_ENGINE_STATE_PREPARE_LOC;
            } else {
              delay(1);  
            }
            state = TWR_ENGINE_STATE_PREPARE_LOC;
          }
        }
      break;
/**
 * Etat TWR_ENGINE_STATE_PREPARE_LOC : 
 * 
 */
    case TWR_ENGINE_STATE_PREPARE_LOC:
      if ( decaduino.rxFrameAvailable() ) {       
        if ( rxData[0] == TWR_MSG_TYPE_DATA_REPLY ) {    //previous communication has finished
            state = TWR_ENGINE_STATE_INIT;
        } 
      }else{
        if( millis() > timeoutWait ){  // previous communication has timedOut
            state = TWR_ENGINE_STATE_INIT;            
          }
      }
      break;

     default:
      state = TWR_ENGINE_STATE_INIT;
      break;
  }
}





