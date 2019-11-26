#include "PingPong.h"



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
int next_target_idx = NB_ROBOTS - 1; //gives the index of the next robot to lcoalize
int state = STATE_PING;
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
byte rxIdentifiant[8];  // /!\ identifiant de l'émetteur robot
byte identifiant[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}; // identifiant de l'ancre
byte identifiantAncreRx[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idNextAncreTx[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idNextAncreRx[8] ={0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
byte idRobotTx[NB_ROBOTS][8]= { {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x01},
					 {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x02}};
byte IdRobotRx[8];

byte cipher [N_BLOCK] ; //données encryptées
byte check [N_BLOCK] ;  //contient le msg décrypté


uint64_t t1, t2, t3, t4;
int32_t tof;
float distance;
uint64_t mask = 0xFFFFFFFFFF;
String a;




uint8_t txData[128];


int timeout;
int timeoutWait;
boolean warning;
char serial_command;


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





  switch (state) {


    case STATE_SERIAL:
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
            Serial.println("$ command #1 received");
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
          state = STATE_SERIAL;
         }
         else {
          state = next_state;
         }
       }
      break;
    case STATE_PING:
      txData[0] = 0;
      decaduino.pdDataRequest(txData, 1);
      state = STATE_PONG;
      decaduino.plmeRxEnableRequest();
      timeout = micros();

      break;

    case STATE_PONG:
      if ( (decaduino.rxFrameAvailable()) || (micros() - timeout) > TIMEOUT)) {
        Serial.print("RSSI:");
        Serial.println(decaduino.getRSSI());

        Serial.print("FP Ampl1:");
        Serial.println(decaduino.getFpAmpl1());

        Serial.print("FP Ampl2:");
        Serial.println(decaduino.getFpAmpl2());

        Serial.print("FP ampl3:");
        Serial.println(decaduino.getFpAmpl3());

        Serial.print("FP power:");
        Serial.println(decaduino.getFpPower());

        Serial.print("SNR:");
        Serial.println(decaduino.getSNR());

        state = STATE_PING;
        delay(1);

      }



     default:
      state = STATE_PING;
      break;
  }
}
