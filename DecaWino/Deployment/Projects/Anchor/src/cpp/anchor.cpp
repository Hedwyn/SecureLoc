#include "anchor.h"

DecaDuino decaduino;// = DecaDuino(DW1000_CS0_PIN, DW1000_IRQ0_PIN);
AES aes;
uint8_t rxData[128];
uint16_t rxLen;
float average;
int unsigned iAverage;
char * hex = "0123456789abcdef" ;
int next_target_idx = NB_ROBOTS - 1; //gives the index of the next robot to lcoalize
int state = TWR_ENGINE_STATE_IDLE;
int next_state;
int unsigned iInitialisation=0;
byte succ;
byte key [2*N_BLOCK] = { 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
							 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
							 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
							 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03 };

int i;
int rxFrames;

byte nbrand [8];     //nb aléa à crypter et son identifiant
byte nbrand_et_id [N_BLOCK];
byte rxIdentifiant[8];  // /!\ identifiant de l'émetteur robot
byte identifiant[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, ANCHOR}; // identifiant de l'ancre
byte IdAncre[8];
byte identifiantAncreRx[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idNextAncreTx[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 1 + (ANCHOR % NB_ANCHORS)};
byte idNextAncreRx[8] ={0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idTarget[][8]= { {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x01},// bots
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x02},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01}, //anchors
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x06},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08},
                     {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09}};
byte IdRobotRx[8];
byte nextTarget[8];
byte cipher [N_BLOCK] ; //données encryptées
byte check [N_BLOCK] ;  //contient le msg décrypté


uint64_t t1, t2, t3, t4;
int32_t tof,tof_skew;
float distance, distance_skew;
uint64_t mask = 0xFFFFFFFFFF;
String a;
uint8_t txData[128];


int timeout;
int timeoutWait;
boolean warning;
char serial_command, target_id;
bool is_target_anchor;
int aloha_delay;


int main(){
	setup();
	while (1) {
		loop();
		yield();
	}

	return(0);
}

void getID() {
	char id;
	#ifdef ANCHOR
		/* setting up anchor id */
		identifiant[7] = ANCHOR;

		/* setting up next anchor ID */
		#ifdef NB_ANCHORS
		/* checking if this anchors has the highest ID */
			if (ANCHOR == NB_ANCHORS) {
				/* the next anchor is the first one */
				idNextAncreTx[7] = 1;
			}
			else {
				idNextAncreTx[7] = ANCHOR + 1;
			}
		#else
			idNextAncreTx[7] = ANCHOR + 1;
		#endif
	#else
		DPRINTFLN("ANCHOR id has not been defined during compilation. Default ID : 0 \n");
	#endif
}


int byte_array_cmp(byte b1[8], byte b2[8]) {
	int i = 0, ret = 1;
	for (i = 0; i <8; i++) {
		if (b1[i] != b2[i]) {
			ret = 0;
			break;
		}
	}
	return(ret);
}


void setup() {
  byte error=0;
  bool success;
  delay(1000);
  DPRINTFLN("decaduino init start");
  pinMode(13, OUTPUT);
  //pinMode(14, OUTPUT);
  SPI.setSCK(14);
  //SPI.setSCK(14)-
  //set for anchors C and D
  //use pin 14 for A and B by uncommenting code lines above
  success = decaduino.init();

  if ( !success )  {
    while(1) {
      digitalWrite(13, HIGH);
      delay(50);
      digitalWrite(13, LOW);
      delay(50);
    }
  }
  getID();

  // Set RX buffer
  decaduino.setRxBuffer(rxData, &rxLen);
  if(!decaduino.setChannel(5)) {
    Serial.println("failed to set Channel 2");
  }
  else {
    Serial.println("succeeded to set Channel 2");
  }


  succ = aes.set_key (key, 32) ;      //initialisation de la clé
      if (succ != SUCCESS)
        DPRINTFLN ("Failure set_key") ;

 average=0;
 iAverage=0;
 decaduino.plmeRxEnableRequest();
 DPRINTFLN("decaduino init finished");

}

void print_value (char * str, byte * a, int bits) //sert à afficher les valeurs
{
  int i;
  DPRINTF (str) ;
  bits >>= 3 ;
  for (i = 0 ; i < bits ; i++)
    {
      byte b = a[i] ;
      DPRINTF (hex [b >> 4]) ;
      DPRINTF (hex [b & 15]) ;
    }
  DPRINTFLN () ;
}


void print_value_raspberry ( byte * a, int bits) //sert à afficher les valeurs
{
  int i;
  bits >>= 3 ;
  for (i = 0 ; i < bits ; i++)
    {
      byte b = a[i] ;
      RPRINTF (hex [b >> 4]) ;
      RPRINTF (hex [b & 15]) ;
    }
}



void check_same (byte * a, byte * b, int bits) {   //vérifie la correspondance entre deux données
  int i;
  bits >>= 3 ;
  for (i = 0 ; i < bits ; i++)
    if (a[i] != b[i])
      {
        DPRINTFLN ("Failure plain != check") ;
        return ;
      }
}




void loop() {
  int new_msg = 0;
  switch (state) {

/**
 * Etat TWR_ENGINE_STATE_INIT :
 * On initialise notre machine à état du robot
 */

    case TWR_ENGINE_STATE_INIT:
      decaduino.plmeRxDisableRequest();
      state = TWR_ENGINE_STATE_WAIT_NEW_CYCLE;
      break;


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
              next_target_idx = (int) (NB_ROBOTS + target_id - ASCII_NUMBERS_OFFSET) ;
              is_target_anchor = true;
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

    case TWR_ENGINE_STATE_WAIT_NEW_CYCLE:
      iInitialisation=0;
      //delay(30); //increase resfresh rate here
      delay(aloha_delay);
      if (Serial.available() > 0) {
        state = TWR_ENGINE_STATE_SERIAL;
        next_state = TWR_ENGINE_STATE_SEND_START;
      }
      else {
      	state = TWR_ENGINE_STATE_SEND_START;
      }
      // getting the index of the next robot to localize


      if (!is_target_anchor) { // not switching target id if the target is an anchor
        next_target_idx = (next_target_idx + 1) % NB_ROBOTS;
      }
      DPRINTFLN(next_target_idx);
      break;

    case TWR_ENGINE_STATE_SEND_START:     //on définie la trame de start
      txData[0] = TWR_MSG_TYPE_START;     // Trame émise : idRobot | idAncreTx | idNextAncre

      // getting temperature




      for(int i=0; i<8; i++){
        txData[1+i]=idTarget[next_target_idx][i];

        txData[9+i]=identifiant[i];
        txData[17+i]=idNextAncreTx[i];
      }


      txData[25]=0;



      if( decaduino.pdDataRequest(txData, 26) ){

      }else{
        DPRINTFLN("pb with pDataRequest");
      }
      if(is_target_anchor) {

        is_target_anchor = false;
        next_target_idx = 0; // going back to the beginning of the cycle
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
      t1 = decaduino.getLastTxTimestamp();
      state = TWR_ENGINE_STATE_WATCHDOG_FOR_ACK;
      break;

    case TWR_ENGINE_STATE_WATCHDOG_FOR_ACK:
      timeout = millis() + TIMEOUT;
      state = TWR_ENGINE_STATE_RX_ON_FOR_ACK;
      break;

    case TWR_ENGINE_STATE_RX_ON_FOR_ACK:
      /* testing FP power */

      decaduino.plmeRxEnableRequest();
      state = TWR_ENGINE_STATE_WAIT_ACK;
      break;

    case TWR_ENGINE_STATE_WAIT_ACK:

      if ( millis() > timeout ) {
        state = TWR_ENGINE_STATE_IDLE;    //pb ici
        DPRINTFLN("timeout");
      } else {
        if ( decaduino.rxFrameAvailable() ) {   // Si on a reçu le ack on mémorise l'heure de réception

          if ( rxData[0] == TWR_MSG_TYPE_ACK ) {    //On regarde ici si la donnée nous est destiné ou non -
            for ( i=0; i<8; i++){

                rxIdentifiant[i]=rxData[i+1]; //On récupère l'identifiant
            }

            if( (*(uint64_t*) rxIdentifiant) == (*(uint64_t*) identifiant) ){//si c'est le bon id on passe à l'étape suivante

              state = TWR_ENGINE_STATE_MEMORISE_T4;   //
            }else{

                print_value("RX ID = ", rxIdentifiant, 64 );
                print_value("MY ID = ", identifiant, 64 );
            }
          } else {
            state = TWR_ENGINE_STATE_RX_ON_FOR_ACK;
            t4 = decaduino.getSystemTimeCounter();

            } // - sinon on retourne dans cet état
        }
      }
      break;

    case TWR_ENGINE_STATE_MEMORISE_T4:            //Heure de réception du ack
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
          if ( rxData[0] == TWR_MSG_TYPE_DATA_REPLY ) { //Si le message est de type data, on passe à l'étape de récup sinon on att
            for ( i=0; i<8; i++){
                rxIdentifiant[i]=rxData[42+i]; //On récupère l'identifiant
            }

            //if( (*(uint64_t*) rxIdentifiant) == (*(uint64_t*) identifiant) ){
						if (byte_array_cmp(rxIdentifiant, identifiant) ) {
                state = TWR_ENGINE_STATE_EXTRACT_T2_T3;
            } else {
								//Serial.println("$Not my DATA frame. Waiting for mine");
								state = TWR_ENGINE_STATE_RX_ON_FOR_DATA_REPLY;
            }
          } else state = TWR_ENGINE_STATE_RX_ON_FOR_DATA_REPLY;
        }
      }
      break;

    case TWR_ENGINE_STATE_EXTRACT_T2_T3: //Etat d'extraction des distances. Décryptage et id
      for ( i=0; i<16; i++){    //on extrait la donnée cryptée
        cipher[i]=rxData[17+i];
      }

      succ = aes.decrypt (cipher, check) ;    //on décrypte
      if (succ != SUCCESS)
        DPRINTFLN ("$Failure decrypt") ;

      for ( i=0; i<8; i++){
        nbrand[i]=rxData[33+i];   //On récupère le nb aléatoire en clair
        rxIdentifiant[i]=check[i+8]; //On récupère l'identifiant
      }

      succ = SUCCESS;

      check_same (nbrand, check, 16) ;    //on vérifie que nb rand décodé est le bon
      print_value ("$Nb alea = ", nbrand, 64) ;
      DPRINTFLN();
      print_value ("$CHECK = ", check, 128) ;
      DPRINTFLN();


      if (succ == SUCCESS){
        t2 = decaduino.decodeUint64(&rxData[1]);  //Data 1 contient l'heure de reception de B.
        t3 = decaduino.decodeUint64(&rxData[9]);  //Data 9 continent l'heure de réémission de B
        tof = (t4 - t1 - (t3 - t2))/2;            //On calcule le temps de voyage puis la distance.
        tof_skew = (((t4 - t1) & mask) - (1+1.0E-6*decaduino.getLastRxSkew())*((t3 - t2) & mask))/2;

        distance = tof*COEFF*X_CORRECTION + Y_CORRECTION;
        distance_skew = tof_skew*COEFF*X_CORRECTION + Y_CORRECTION;

				if (ALOHA) {
					// checking for collisions
					if ( (distance_skew < 0) || (distance_skew > DMAX) ) {
						aloha_delay = SLOT + ANCHOR * ALOHA_COLLISION_DELAY;
					}
					else {
						aloha_delay = SLOT;
					}
				}
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
        DPRINTF("Failed decoding / unidentified transmission");
        DPRINTFLN();
        state = TWR_ENGINE_STATE_IDLE;
      }
      break;

 /**
 * Etat TWR_ENGINE_STATE_SEND_DATA_PI :
 * Dans cet état on transmet la trame de l'ancre à la RasPI.
 * la trame est composé comme suit :
 * Trame : *IdAncre|idRobot#
 *
 * le caractère * sert de "balise" de démarrage, le caractère | sépare les deux Id et
 * le caractère # indique la fin de la trame
 */

    case TWR_ENGINE_STATE_SEND_DATA_PI :
      RPRINTF("*");
      //Trame * idAncre | idRobot| distance #
      print_value_raspberry(identifiant,64);
      RPRINTF("|");
      print_value_raspberry(idTarget[next_target_idx],64);
      RPRINTF("|");
      RPRINTF(distance_skew);
      RPRINTF("|");
      /* timestamps */
      RPRINTF((int) t1);
      RPRINTF("|");

      RPRINTF((int) t2);
      RPRINTF("|");

      RPRINTF( (int) t3);
      RPRINTF("|");

      RPRINTF( (int) t4);
      RPRINTF("|");
      /* RSSI */
      RPRINTF(decaduino.getRSSI() );
      RPRINTF("#\n");
      decaduino.plmeRxEnableRequest();

      state= TWR_ENGINE_STATE_IDLE;
      break;

/**
 * Etat TWR_ENGINE_STATE_IDLE :
 * On  attends de recevoir une trame. On regarde si elle nous est adressée.
 * Si oui on reprépare la communication.
 */

    case TWR_ENGINE_STATE_IDLE :
      if (ALOHA) {
        state = TWR_ENGINE_STATE_INIT;
      }else{
        if ( decaduino.rxFrameAvailable() ) {
					if ( rxData[0] == TWR_MSG_TYPE_DATA_REPLY ) {    //trame ancre = dest | idAnchor | idNextAchor
            for (int i=0; i<8; i++){
              idNextAncreRx[i] = rxData[i+42];
            }
						idNextAncreRx[7] = (idNextAncreRx[7] + 1 % NB_ANCHORS) + 1;
						Serial.println("$ID received:");
						Serial.println((int) idNextAncreRx[7] );
						Serial.println("$My ID");
						Serial.println((int) identifiant[7]);
            //if  ( (*(uint64_t*) idNextAncreRx) == (*(uint64_t*) identifiant) )   //On regarde si l'ancre est la prochaine à parlé
						if (byte_array_cmp(idNextAncreRx, identifiant))
						{
              Serial.println("$It's my turn");
              state = TWR_ENGINE_STATE_INIT;
              //timeoutWait = millis() + TIMEOUT;
            }
            if ( (*(uint64_t*) nextTarget) == (*(uint64_t*) identifiant )) {
              Serial.println("$anchor ranging request received !");
              //IdAncre[i] = rxData[i+9];
              IdAncre[i] = rxData[i+1];
              state = TWR_ENGINE_STATE_MEMORISE_T2;
            }
          }
          decaduino.plmeRxEnableRequest();
        } else {
            // no frame received, possibility than nobody speak
            iInitialisation++;
            //if (iInitialisation> WAITTIME + ANCHOR * SLOT) { //To SET
						if (identifiant[7] == 1) {
							timeout = TIMEOUT_INIT;
						}
						else {
							timeout = TIMEOUT;
						}
						if (iInitialisation> timeout) {
                state = TWR_ENGINE_STATE_PREPARE_LOC;
								Serial.println("Timeout ! ");
								iInitialisation = 0;
            } else {
              delay(1);
            }
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


    case TWR_ENGINE_STATE_MEMORISE_T2:
      t2 = decaduino.getLastRxTimestamp();           //On enregistre l'heure de réception
      state = TWR_ENGINE_STATE_SEND_ACK;
      break;

/**
 * State handling replies for anchor ranging
 */


    case TWR_ENGINE_STATE_SEND_ACK:
      decaduino.plmeRxDisableRequest();
      txData[0] = TWR_MSG_TYPE_ACK;           //On acquite le message (champs 0 du mesage)
      for( int i =0; i<8 ; i++){
        txData[1+i] = IdAncre[i];
        txData[9+i] = identifiant[i];
      }
      decaduino.pdDataRequest(txData, 18);
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
      Serial.println("$anchor data reply sent !");
      txData[0] = TWR_MSG_TYPE_DATA_REPLY;
      for( int i=0; i<8;i++){
        txData[33+i] = nbrand_et_id[i];
        txData[42+i] = IdAncre[i];
      }
      decaduino.encodeUint64(t2, &txData[1]);
      decaduino.encodeUint64(t3, &txData[9]);
      decaduino.pdDataRequest(txData, 50);  //message de 49 octets
      state = TWR_ENGINE_STATE_IDLE;
      break;

    default:
      state = TWR_ENGINE_STATE_INIT;
      break;
  }
}
