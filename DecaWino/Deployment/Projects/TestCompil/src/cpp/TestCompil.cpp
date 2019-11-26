#include<main.h>



/**
 * Les trois fonctions ci dessous permettent d'afficher des messages.  
 * En commentant les bonnes lignes on affiche les messages du Debug ou du fonctionnement normal
 */





/**
 * Dans la boucle "setup" on initialise l'antenne UWB, on génère la clé privé  
 * et on initialise le buffer de reception. Si l'initialisation de l'antenne ne 
 * marche pas on fait clignoter la lED. Print value nous permet d'afficher la valeur de string en numérique
 * La fonction check_same vérifie la correspondance entre le message décrypter
 * et le message en clair
 */
DecaDuino decaduino;// = DecaDuino(DW1000_CS0_PIN, DW1000_IRQ0_PIN);
AES aes;
uint8_t rxData[128];
uint16_t rxLen;
float average;
int unsigned iAverage;
char * hex = "0123456789abcdef" ;
int next_bot_idx = NB_ROBOTS - 1; //gives the index of the next robot to lcoalize 
int state = TWR_ENGINE_STATE_IDLE;
int unsigned iInitialisation=0;
byte succ;
byte key [2*N_BLOCK] = { 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
							 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
							 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03,
							 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03 };

int i;
int rxFrames;

byte nbrand [8];     //nb aléa à crypter et son identifiant
byte rxIdentifiant[8];  // /!\ identifiant de l'émetteur robot
byte identifiant[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}; // identifiant de l'ancre
byte identifiantAncreRx[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idNextAncreTx[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idNextAncreRx[8] ={0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idRobotTx[NB_ROBOTS][8]= { {0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x02},
					 {0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03} };                        
byte IdRobotRx[8];

byte cipher [N_BLOCK] ; //données encryptées
byte check [N_BLOCK] ;  //contient le msg décrypté


uint64_t t1, t2, t3, t4;
int32_t tof;
float distance;
uint64_t mask = 0xFFFFFFFFFF;




uint8_t txData[128];


int timeout;
int timeoutWait;
boolean warning;							 


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
  
  if ( !success )  {                    //En cas d'erreur on fait clignoter la LED
    
    
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

	

  
  
  switch (state) {
  
/**
 * Etat TWR_ENGINE_STATE_INIT : 
 * On initialise notre machine à état du robot
 */   
  
    case TWR_ENGINE_STATE_INIT:
	#ifdef ANCHOR
		DPRINTFLN(ANCHOR);
		DPRINTFLN("ANCHOR defined");
	#endif
      decaduino.plmeRxDisableRequest();
      state = TWR_ENGINE_STATE_WAIT_NEW_CYCLE; 
      break;
      
    case TWR_ENGINE_STATE_WAIT_NEW_CYCLE:
	
      iInitialisation=0;
      // delay(30); //increase resfresh rate here
      // delay(200);
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

    case TWR_ENGINE_STATE_SEND_START:     //on définie la trame de start
	
      txData[0] = TWR_MSG_TYPE_START;     // Trame émise : idRobot | idAncreTx | idNextAncre

      // getting temperature
      /*
      DPRINTFLN("temperature:\n");
      DPRINTFLN(decaduino.getTemperature());
      DPRINTFLN("\n");

      DPRINTFLN("voltage:\n");
      DPRINTFLN(decaduino.getVoltage());
      DPRINTFLN("\n");
      */

     
      
      for(i=0; i<8; i++){
        txData[1+i]=idRobotTx[next_bot_idx][i];
        
        txData[9+i]=identifiant[i];
        txData[17+i]=idNextAncreTx[i];   
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
        if ( decaduino.rxFrameAvailable() ) {   // Si on a reçu le ack on mémorise l'heure de réception
          if ( rxData[0] == TWR_MSG_TYPE_ACK ) {    //On regarde ici si la donnée nous est destiné ou non -
            for (i=0; i<8; i++){
                rxIdentifiant[i]=rxData[i+1]; //On récupère l'identifiant
            }
            if( (*(uint64_t*) rxIdentifiant) == (*(uint64_t*) identifiant) ){//si c'est le bon id on passe à l'étape suivante
              state = TWR_ENGINE_STATE_MEMORISE_T4;   //
            }else{
                DPRINTFLN("bad robot id");
                print_value("RX ID = ", rxIdentifiant, 64 );
                print_value("MY ID = ", identifiant, 64 );
            }
          } else state = TWR_ENGINE_STATE_RX_ON_FOR_ACK; // - sinon on retourne dans cet état 
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
            for (i=0; i<8; i++){
                rxIdentifiant[i]=rxData[42+i]; //On récupère l'identifiant
            }
            if( (*(uint64_t*) rxIdentifiant) == (*(uint64_t*) identifiant) ){//si c'est le bon id on passe à l'étape suivante
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

    case TWR_ENGINE_STATE_EXTRACT_T2_T3: //Etat d'extraction des distances. Décryptage et id 
      for (i=0; i<16; i++){    //on extrait la donnée cryptée
        cipher[i]=rxData[17+i];     
      }
      
      succ = aes.decrypt (cipher, check) ;    //on décrypte
      if (succ != SUCCESS)
        DPRINTFLN ("Failure decrypt") ;
        
      for (i=0; i<8; i++){
        nbrand[i]=rxData[33+i];   //On récupère le nb aléatoire en clair
        rxIdentifiant[i]=check[i+8]; //On récupère l'identifiant
      }
      
      succ = SUCCESS;
      
      check_same (nbrand, check, 16) ;    //on vérifie que nb rand décodé est le bon
      print_value ("Nb alea = ", nbrand, 64) ;
      DPRINTFLN();
      print_value ("CHECK = ", check, 128) ;
      DPRINTFLN();

     
      if (succ == SUCCESS){
        t2 = decaduino.decodeUint64(&rxData[1]);  //Data 1 contient l'heure de reception de B.  
        t3 = decaduino.decodeUint64(&rxData[9]);  //Data 9 continent l'heure de réémission de B
        //tof = (t4 - t1 - (t3 - t2))/2;            //On calcule le temps de voyage puis la distance. 
        tof = (((t4 - t1) & mask) - (1+1.0E-6*decaduino.getLastRxSkew())*((t3 - t2) & mask))/2;
		distance = tof*COEFF*X_CORRECTION + Y_CORRECTION;
  
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
        DPRINTF("Echec du décodage/ transmission non identifiée");
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
      /* if the speed exceed 12km.h-1, send a warning message*/
      if (average-distance>=1.0 || average-distance<=-1.0)
      {
        warning=true;
      } else {
        warning=false;
      }
      
     
      
     
      if (warning)
      {
        // RPRINTF("*W : speed exceed 12km.h-1#\n");
      }
      RPRINTF("*");                   //RPRINTF correspont à la communication avec la RasPI
      // Trame * idAncre | idRobot| distance #
      print_value_raspberry(identifiant,64);
     
      RPRINTF("|"); 

      // print_value_raspberry(rxIdentifiant,64);
      print_value_raspberry(idRobotTx[next_bot_idx],64);
      RPRINTF("|"); 
      // RPRINTF(average);
      RPRINTF(distance);
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
	
      if ( (*(uint64_t*) idNextAncreTx) == (*(uint64_t*) identifiant) ) //On regarde si l'ancre est la prochaine à parlé
      {
        state = TWR_ENGINE_STATE_PREPARE_LOC;
      }else{
        if ( decaduino.rxFrameAvailable() ) {  
      
        if ( rxData[0] == TWR_MSG_TYPE_START ) {    //trame ancre = dest | idAnchor | idNextAchor
          for (i=0; i<8; i++){
            idNextAncreRx[i] = rxData[i+17];
          }
          decaduino.plmeRxEnableRequest();
            if ( (*(uint64_t*) idNextAncreRx) == (*(uint64_t*) identifiant) ) //On regarde si l'ancre est la prochaine à parlé
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


