#include <AES.h>
#include <SPI.h>
#include <DecaDuino.h>

AES aes ;

/**
 * Les trois fonctions ci dessous permettent d'afficher des messages.  
 * En commentant les bonnes lignes on affiche les messages du Debug ou du fonctionnement normal
 */

#define _DEBUG_   //commenter cette ligne pour "supprimer" les print de test
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


#define FRAME_LEN 64

#define TWR_ENGINE_STATE_INIT 1
#define TWR_ENGINE_STATE_RX_ON 2
#define TWR_ENGINE_STATE_WAIT_START 3
#define TWR_ENGINE_STATE_MEMORISE_T2 4
#define TWR_ENGINE_STATE_SEND_ACK 5
#define TWR_ENGINE_STATE_WAIT_SENT 6
#define TWR_ENGINE_STATE_MEMORISE_T3 7
#define TWR_ENGINE_STATE_WAIT_BEFORE_SEND_DATA_REPLY 8
#define TWR_ENGINE_STATE_SEND_DATA_REPLY 9 
#define TWR_ENGINE_STATE_ENCRYPTION 10

#define TWR_MSG_TYPE_UNKNOWN 0
#define TWR_MSG_TYPE_START 1
#define TWR_MSG_TYPE_ACK 2
#define TWR_MSG_TYPE_DATA_REPLY 3
#define START_LENGTH 26
#define DATA_LENGTH 50


int rxFrames;
byte succ;
byte nbrand_et_id [N_BLOCK];     //nb aléa à crypter et son identifiant

byte identifiant[8] = {0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03};

byte key [2*N_BLOCK] = { 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
                         0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
                         0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
                         0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03 };   //clé
                         
byte cipher [N_BLOCK] ; //données encryptées
byte check [N_BLOCK] ;  //contient le msg décrypté

uint64_t t2, t3;      //temps de réception et temps de ré-émission

DecaDuino decaduino;
uint8_t txData[128];
uint8_t rxData[128];
uint16_t rxLen;
byte IdRobotRx [8];//Id robot reçue
byte IdAncre [8];   //Id de l'ancre émettrice 
int state;
int tx_prf;
int rx_prf;



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

/**
 * Dans la boucle "setup" on initialise l'antenne UWB, on génère la clé privé  
 * et on initialise le buffer de reception. Si l'initialisation de l'antenne ne 
 * marche pas on fait clignoter la lED
 */


void  switchTXsettings() {

  if (tx_prf == 1) {
    decaduino.setTxPrf(2);
    decaduino.setDrxTune(64);
    tx_prf = 2;
  }
  else {
    decaduino.setTxPrf(1);
    decaduino.setDrxTune(16);
    tx_prf = 1;
  }
  
  
}

void  switchRXsettings() {

  if (rx_prf == 1) {
    decaduino.setRxPrf(2);
    decaduino.setDrxTune(64);
    rx_prf = 2;
  }
  else {
    decaduino.setRxPrf(1);
    decaduino.setDrxTune(16);
    rx_prf = 1;
  }
  
  
}



void setup() {
  byte error=0;
  delay(1000);
  DPRINTFLN("decaduino init start");
  pinMode(13, OUTPUT);
  pinMode(14, OUTPUT);
  //SPI.setSCK(13);
  SPI.setSCK(14);
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
  

  succ = aes.set_key (key, 32) ;
      if (succ != SUCCESS)
        Serial.println ("Failure set_key") ;



  // Set RX buffer
  decaduino.setRxBuffer(rxData, &rxLen);


   /* setting up Pulse Repetition Frequency */
  decaduino.setTxPrf(1);
  decaduino.setRxPrf(1);
  tx_prf = 1;
  rx_prf = 1;
  //decaduino.setDrxTune(64);


 /*
 if (!decaduino.setTxPrf(1)) {
  DPRINTFLN("Failed to st Tx PRF to 64");
 }
 
 if (!decaduino.setRxPrf(2)) {
  DPRINTFLN("Failed to set Rx PRF to 64");
 }
 decaduino.setDrxTune(64);
 
 
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
 
  state = TWR_ENGINE_STATE_INIT;
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
      DPRINTFLN("State rx on");
      state = TWR_ENGINE_STATE_WAIT_START;
      break;
/**
 * Etat TWR_ENGINE_STATE_WAIT_START : 
 * on attends un message start de la part d'une ancre. Si on en reçoit un,
 * on récupère l'Id de l'ancre éméttrice, Id du robot destinataire et on le compare au notre
 * La trame start se décompose comme ci dessous :
 * 
 * Type du message (1octet) | idRobotDestinataire(8 Octets) | idAnchor (8 octets) | iDNextAnchor(8 octets)
 */
    case TWR_ENGINE_STATE_WAIT_START:           //On regardera ici si la donnée nous est destiné ou non 
      //RPRINTF(decaduino.getTemperature());
      
      if ( decaduino.rxFrameAvailable() ) {  
            
        if ( rxData[0] == TWR_MSG_TYPE_START ) {    //trame ancre = dest | idAnchor | idNextAchor

          for (int i=0; i<8; i++){
           IdRobotRx [i] = rxData[i+1];         //On récupère l'id du robot destinataire
           
           IdAncre [i] = rxData[i+9];               //On récupère l'id de l'ancre émettrice
          }
          //if (true)
          if ( (*(uint64_t*) IdRobotRx) == (*(uint64_t*) identifiant) ) //On regarde si le msg nous est destiné
          {
            state = TWR_ENGINE_STATE_MEMORISE_T2;            
          }else{
              DPRINTFLN(" pb identifiant robot" );
              print_value("ID receive = ", IdRobotRx, 64); 
              print_value("My ID = ", identifiant, 64);
              state = TWR_ENGINE_STATE_RX_ON;                          
          }
        } else {
          state = TWR_ENGINE_STATE_RX_ON;   
         // DPRINTF(" pb no rx frame available" ); 
        }
      }else{
        // DPRINTFLN("");
      }
      
      break;
/**
 * Etat : TWR_ENGINE_STATE_MEMORISE_T2
 * On enregistre l'heure de réception du message start
 */
    case TWR_ENGINE_STATE_MEMORISE_T2:
      t2 = decaduino.getLastRxTimestamp();           //On enregistre l'heure de réception
      state = TWR_ENGINE_STATE_SEND_ACK;
      break;

/**
 * Etat : TWR_ENGINE_STATE_SEND_ACK
 * Dans cet état on envoie un acquittement à l'ancre émettrice contentant les identfiants du robot et de l'ancre émettrice
 * Trame :
 * Type du message (1octet) |  idAnchor (8 octets) | idRobot (8 Octets)
 */

    case TWR_ENGINE_STATE_SEND_ACK:
      txData[0] = TWR_MSG_TYPE_ACK;           //On acquite le message (champs 0 du mesage)
      for( int i =0; i<8 ; i++){
        txData[1+i] = IdAncre[i];
        txData[9+i] = IdRobotRx[i];
      }
      //decaduino.pdDataRequest(txData, 18);
      decaduino.pdDataRequest(txData, 18,1, t2 + 30000000);
      state = TWR_ENGINE_STATE_WAIT_SENT;
      break;

/**
 * Etat : TWR_ENGINE_STATE_WAIT_SENT
 * On vérifie que l'Ack est bien envoyé
 */

    case TWR_ENGINE_STATE_WAIT_SENT:
      if ( decaduino.hasTxSucceeded() )
        state = TWR_ENGINE_STATE_MEMORISE_T3;  //si l'état précédent est réussi on continue
      break;


/**
 * Etat : TWR_ENGINE_STATE_MEMORISE_T3
 * Sauvegarde de l'heure d'envoie de la réponse
 */
    case TWR_ENGINE_STATE_MEMORISE_T3:
      t3 = decaduino.getLastTxTimestamp();       // on sauvegarde l'heure d'envoie de la réponse
      state = TWR_ENGINE_STATE_ENCRYPTION;
      break;
/**
 * Etat : TWR_ENGINE_STATE_ENCRYPTION
 * Dans cet étant on génère un nombre aléatoire pour l'authentification.
 * On encrypte ce dernier avec l'idée à l'aide d'une clé privée
 */

    case TWR_ENGINE_STATE_ENCRYPTION :       //on authentifie et on crypt
      for(int i=0;i<8;i++){
        nbrand_et_id [i] = (byte)random(255);
        nbrand_et_id [i+8] = identifiant[i];
      }     
      succ = aes.encrypt (nbrand_et_id, cipher) ;  //on crypte l'identifiant et le nb aléa
      state = TWR_ENGINE_STATE_SEND_DATA_REPLY;
      
/**
 * Etat : TWR_ENGINE_STATE_SEND_DATA_REPLY
 * On génère la trame de donnée du robot. Cette trame est composée comme il suit 
 * Trame :
 * 
 * Type du message (1octet) |  T2 (8 octets) | T3 (8 Octets) | Cipher (16 octets) |  Nbaléatoire (8 octets) | idAnchor (8 Octets)
 */
 
    case TWR_ENGINE_STATE_SEND_DATA_REPLY:  
      txData[0] = TWR_MSG_TYPE_DATA_REPLY;
      for( int i=0; i<8;i++){
        txData[33+i] = nbrand_et_id[i]; 
        txData[42+i] = IdAncre[i];        
      }
      decaduino.encodeUint64(t2, &txData[1]); 
      decaduino.encodeUint64(t3, &txData[9]);
      delay(1);
      
      //decaduino.pdDataRequest(txData, 50);  //message de 49 octets
      state = TWR_ENGINE_STATE_INIT;        
      break;
 
    default:
      state = TWR_ENGINE_STATE_INIT;
      break;
  }
}


