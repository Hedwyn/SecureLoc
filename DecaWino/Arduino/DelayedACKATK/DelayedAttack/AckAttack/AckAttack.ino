
#include <AES.h>
#include <SPI.h>
#include <DecaDuino.h>

AES aes ;

/**
 * Les trois fonctions ci dessous permettent d'afficher des messages.  
 * En commentant les bonnes lignes on affiche les messages du Debug ou du fonctionnement normal
 */

//#define _DEBUG_   //commenter cette ligne pour "supprimer" les print de test
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
#define TIMESHIFT -2000

#define FRAME_LEN 64

#define TWR_ENGINE_STATE_INIT 1
#define TWR_ENGINE_STATE_RX_ON 2
#define TWR_ENGINE_STATE_WAIT_START 3
#define TWR_ENGINE_STATE_MEMORISE_T2 4
#define TWR_ENGINE_STATE_SEND_ACK 5
#define TWR_ENGINE_STATE_WAIT_SENT 6
#define TWR_ENGINE_STATE_MEMORISE_T3 7
#define TWR_ENGINE_STATE_SERIAL 8

#define TWR_MSG_TYPE_UNKNOWN 0
#define TWR_MSG_TYPE_START 1
#define TWR_MSG_TYPE_ACK 2
#define TWR_MSG_TYPE_DATA_REPLY 3


#define ASCII_NUMBERS_OFFSET 48
int time;


int nb_targets = 4;
int rxFrames;
byte succ;
byte nbrand_et_id [N_BLOCK];     //nb aléa à crypter et son identifiant

byte identifiant[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x01};
byte ID_1[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01};
byte ID_2[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02};
byte ID_3[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03};
byte ID_4[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04};

byte *ID_TARGETS[10]= {ID_2,ID_1,ID_3,ID_4};
//uint64_t timeshifts[] = {3000,8000,3000,3000};
uint64_t timeshifts[] = {0,0,0,0};


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
byte IdRobotRx [8]; //Id robot reçue
byte IdAncre [8];   //Id de l'ancre émettrice 
int state,next_state;
int isTarget,target_idx;
char serial_command,target_id;


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
  if(!decaduino.setChannel(5)) {
    Serial.println("failed to set Channel");
  }
  else {
    Serial.println("succeeded to set Channel");
  } 

    
  if (!decaduino.setSmartTxPower(0) ) {
    Serial.println("$wrong argument for set STP");
  }

  if (decaduino.getSmartTxPower() != 0) {
    Serial.println("$STP failed");
  }

  decaduino.setPhrPower(18,15.5);
  decaduino.setSdPower(18,15.5);


   /* setting up Pulse Repetition Frequency */
//  decaduino.setTxPrf(1);
//  decaduino.setRxPrf(1);
//  //decaduino.setDrxTune(64);
//
// if (!decaduino.setPreambleLength(128)) {
//  DPRINTFLN("Failed to set Rx PRF to 64");
// }
  decaduino.setPreambleLength(256);
 
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
      DPRINTFLN("State rx on");
      if (Serial.available() > 0) {
        state = TWR_ENGINE_STATE_SERIAL;
        next_state = TWR_ENGINE_STATE_WAIT_START;
      }
      else {
      state = TWR_ENGINE_STATE_WAIT_START;
      }     

      break;
/**
 * Etat TWR_ENGINE_STATE_WAIT_START : 
 * on attends un message start de la part d'une ancre. Si on en reçoit un,
 * on récupère l'Id de l'ancre éméttrice, Id du robot destinataire et on le compare au notre
 * La trame start se décompose comme ci dessous :
 * 
 * Type du message (1octet) | idRobotDestinataire(8 Octets) | idAnchor (8 octets) | iDNextAnchor(8 octets)
 */


    case TWR_ENGINE_STATE_SERIAL:
       // reading serial command
       serial_command = Serial.read(); // { used as termination character
       while ((serial_command == '\r') || (serial_command == '\n')) {
        // skipping
        serial_command = Serial.read();
        
       }

       if (serial_command == (char) -1) {
        // Nothing was available
        state = next_state;
       }
       else {
         switch(serial_command - ASCII_NUMBERS_OFFSET) {        
          case 0:          
            Serial.println("$ [Serial command]: anchor ranging request");
            // reading anchor ID
            target_id = Serial.read();
            if ((target_id == -1) || (target_id == '\r') || (target_id == '\n') ){
              Serial.println("$ Dismissing command: no ID received");
            }
            else if ( (serial_command < ASCII_NUMBERS_OFFSET) || (serial_command > ASCII_NUMBERS_OFFSET + 9)){
              Serial.println("$ Dismissing command: invalid ID received");
            }
            else {
              Serial.print("$ Target ID: ");
              Serial.println(target_id);
              // Reading timeshift value
              int timeshift = Serial.parseInt();

              for (int i = 0; i < nb_targets; i++) {
                Serial.println((ID_TARGETS[i])[7]);
                if ( (ID_TARGETS[i])[7] == (byte) (target_id - ASCII_NUMBERS_OFFSET) ) {
                  timeshifts[i] = timeshift;
                  Serial.print("Updating timeshift of target: ");
                  Serial.println(target_id);
                }
              }

              

            }
            
            
            break;
          case 1:
            Serial.println("$ command #2 received");
            break;
          default:
            Serial.println("$ unknown command received:");
            Serial.println(serial_command);
            break;
         }

         // Staying in Serial state if bytes are still available in buffer
         if (Serial.available() > 0) {
          state = TWR_ENGINE_STATE_SERIAL;
         }
         else {
          state = next_state;
         }
       }      
      break;
      
    case TWR_ENGINE_STATE_WAIT_START:           //On regardera ici si la donnée nous est destiné ou non 
      //RPRINTF(decaduino.getTemperature());

      if ( decaduino.rxFrameAvailable() ) {  
            
        if ( rxData[0] == TWR_MSG_TYPE_START ) {    //trame ancre = dest | idAnchor | idNextAchor
          //Serial.println("$Start received");
          for (int i=0; i<8; i++){
           IdRobotRx [i] = rxData[i+1];         //On récupère l'id du robot destinataire
           
           IdAncre [i] = rxData[i+9];               //On récupère l'id de l'ancre émettrice
          }

          // finding out if the anchor ID is a target
          
          isTarget = 0;
          target_idx = -1;
         
          while (!isTarget && (target_idx++ < nb_targets) ) {
            if (  *(uint64_t*)IdAncre == *(uint64_t *)(ID_TARGETS[target_idx]) ) {
              isTarget = 1;
              //Serial.println("$Target found");
              
            }
          }
          
          
          
          
          if ( ( (*(uint64_t*) IdRobotRx) == (*(uint64_t*) identifiant) ) && isTarget)//( (*(uint64_t*) IdAncre) == (*(uint64_t*) ID_1) ) || ( (*(uint64_t*) IdAncre) == (*(uint64_t*) ID_2) ) )//On regarde si le msg nous est destiné
          {
            state = TWR_ENGINE_STATE_MEMORISE_T2;            
          }else{

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
      
      if (timeshifts[target_idx] != 0) {
        Serial.println("$Sending ACK");
        decaduino.pdDataRequest(txData, 18,1, t2 + 100000000 + timeshifts[target_idx]);
        state = TWR_ENGINE_STATE_WAIT_SENT;
      }
      else {
        state = TWR_ENGINE_STATE_INIT;
        time = millis();
      }  
      
      break;

/**
 * Etat : TWR_ENGINE_STATE_WAIT_SENT
 * On vérifie que l'Ack est bien envoyé
 */

    case TWR_ENGINE_STATE_WAIT_SENT:
      if (millis() - time > 200) {
        Serial.println("$Timeout !\n");
        state = TWR_ENGINE_STATE_INIT;
      }
      if ( decaduino.hasTxSucceeded() )
        state = TWR_ENGINE_STATE_MEMORISE_T3;  //si l'état précédent est réussi on continue
      break;


/**
 * Etat : TWR_ENGINE_STATE_MEMORISE_T3
 * Sauvegarde de l'heure d'envoie de la réponse
 */
    case TWR_ENGINE_STATE_MEMORISE_T3:
      t3 = decaduino.getLastTxTimestamp();       // on sauvegarde l'heure d'envoie de la réponse
      state = TWR_ENGINE_STATE_INIT;
      break;

    default:
      state = TWR_ENGINE_STATE_INIT;
      break;

  }
}

