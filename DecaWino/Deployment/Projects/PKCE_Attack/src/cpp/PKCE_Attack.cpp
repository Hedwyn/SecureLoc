#include "PKCE_Attack.h"



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
int state = STATE_PING;
int next_state;
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
int target_temp;
int ctr;


double last_skew_0 = DEFAULT_SKEW;
double last_skew_1;

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

void boil(int target_temp) {

	int i = 0,j,temp;
	int reached = 0;
	Serial.print("Starting at temperature: ");
	Serial.println(decaduino.getTemperature());
	while (!reached) {
		reached = 1;
		for (j = 0; j < 5; j++) {
			reached = reached && (decaduino.getTemperature() > target_temp);
		}
		if (i == 20000) {
			i = 0;
			Serial.print("Current temperature ");
			Serial.println(decaduino.getTemperature());
		}
		i++;
	}
	Serial.print("Temperature reached: ");
	Serial.println(decaduino.getTemperature());
}

void setup() {
  byte error=0;
  bool success;
  delay(4000);
  DPRINTFLN("decaduino init start");
  pinMode(13, OUTPUT);
  SPI.setSCK(14);


  success = decaduino.init();
	state = STATE_PONG;


  if ( !success )  {
    while(1) {
      digitalWrite(13, HIGH);
      delay(50);
      digitalWrite(13, LOW);
      delay(50);
    }
  }


  // Set RX buffer
  decaduino.setRxBuffer(rxData, &rxLen);

	for (int i = 0; i < 10; i++) {
		txData[i] = 0;
	}

 decaduino.plmeRxEnableRequest();
 DPRINTFLN("decaduino init finished");

 decaduino.setSmartTxPower(0);
 decaduino.plmeRxEnableRequest();

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
            Serial.println("$ Starting boiling");
						target_temp = Serial.parseInt();
						boil(target_temp);
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

    case STATE_PONG:


			if (Serial.available() > 0) {
				state = STATE_SERIAL;
				next_state = STATE_PONG;
				break;
			}

      if (decaduino.rxFrameAvailable() ) {
				decaduino.plmeRxEnableRequest();

				if (rxData[0] == 0) {
					last_skew_0 = decaduino.getLastRxSkew();
					DPRINTFLN("$Received frame from Anchor 0");
				}
				else {
					last_skew_1 = decaduino.getLastRxSkew();
					DPRINTFLN("$Received frame from Anchor 1");
					if (last_skew_0 != DEFAULT_SKEW) {
						Serial.print(last_skew_0 - last_skew_1);
						Serial.print("|");
						Serial.print(decaduino.getTemperature());
						Serial.println("|");
						last_skew_0 = DEFAULT_SKEW;
					}
				}




      }
			break;

     default:
      state = STATE_PONG;
      break;
  }
}
