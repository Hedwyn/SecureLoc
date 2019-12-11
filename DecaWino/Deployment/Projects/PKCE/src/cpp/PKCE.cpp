#include "PKCE.h"



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

uint8_t rxData[128];
uint16_t rxLen;


int state = STATE_PING;
int next_state;







uint8_t txData[128];
int timeout;
byte success;

char serial_command;
int target_temp;
int ctr;
int frame_ctr= MY_ID?0:128, global_frame_ctr = 0, chunk_idx = 0, block_idx = 0;
int speed,t_delay = DELAY_SLOW;
double skew_acc = 0;
float last_skew;
//byte signature[N_CHUNKS * 8];
uint16_t signature[N_CHUNKS * 8];
double signature_float[N_CHUNKS * 8];
float mean_temp = 0;
int max_chunks = N_CHUNKS;


int main(){
	setup();
	while (1) {
		loop();
		yield();
	}
	return(0);
}


byte quantize(float skew) {
	float pow_2 = 16; //skew < 32 ppm so we quantize integer part on 5 bits
	int bit;
	byte quantized = 0;
	DPRINTF("$Starting quantization, skew val...");
	DPRINTFLN(skew);
	if (skew < 0) {
		skew = -skew;
	}
	while (pow_2 != 1./8.) {
		bit = (skew > pow_2);
		// Serial.print("$bit value:");
		// Serial.println(bit);
		// Serial.print("$Skew value:");
		// Serial.println(skew);
		skew -= pow_2 * bit;
		quantized = (quantized << 1) + bit;
		pow_2 = pow_2 / 2;
	}
	if (skew > 1./16.) {
		// rounding to the superior value
		quantized += 1;
	}
	DPRINTF("$Quantization: ");
	DPRINTFLN(quantized);
	return(quantized);
}

void set_n_chunks(int n) {
	max_chunks = n;
}

uint16_t quantize_16(float skew) {
	float pow_2 = 1024; //skew < 32 ppm so we quantize integer part on 5 bits
	int bit;
	uint16_t quantized = 0;
	Serial.print("$Starting quantization, skew val...");
	Serial.println(skew);
	skew += 32.;
	if (skew < 0) {
		skew = -skew;
	}
	while (pow_2 != 1./64.) {
		bit = (skew > pow_2);
		// Serial.print("$bit value:");
		// Serial.println(bit);
		// Serial.print("$Skew value:");
		// Serial.println(skew);
		skew -= pow_2 * bit;
		quantized = (quantized << 1) + bit;
		pow_2 = pow_2 / 2;
	}

	Serial.print("$Quantization: ");
	Serial.println(quantized);
	return(quantized);
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

void reset() {
	chunk_idx = 0;
	block_idx = 0;
	frame_ctr = MY_ID?0:128;
	global_frame_ctr = 0;
}

void switch_mode(int sp) {
	t_delay = sp;
	reset();
}

void send_last_frame_data() {
	float los;
	decaduino.plmeRxEnableRequest();
	/* Calculating LoS indicator */
	los = decaduino.getRSSI() - decaduino.getFpPower();
	DPRINTF("$LoS: ");
	DPRINTFLN(los);

	Serial.print(decaduino.getLastRxSkew());
	Serial.print("|");
	Serial.print(decaduino.getTemperature());
	Serial.print("|");
	Serial.print(los);
	/*
	Serial.print("|");
	Serial.print(decaduino.getRSSI());
	Serial.print("|");
	Serial.print(decaduino.getFpPower());
	*/
	Serial.println("|");
}

float getSkew() {
	float skew = decaduino.getLastRxSkew();
	#ifdef SKEW_CORRECTION
	/* returns a skew value corrected to match the reference temperature */
		float temp = decaduino.getTemperature();
		while ((temp < 15) || (temp > 60)) {
			// sensor reading failed
			temp = decaduino.getTemperature();
		}
		skew += (REF_TEMPERATURE - temp) * SKEW_FACTOR;
	#endif
		return(skew);
}

void send_signature() {
	int i;
	Serial.println("$Signature = ");
	Serial.print("#");
	for (i = 0; i < N_CHARACTERS; i++) {
		//Serial.print((int) signature[i]);
		Serial.print(signature_float[i]);
		Serial.print("|");
	}
	Serial.println();
}

void setup() {
  byte error=0;
  bool success;
  delay(4000);
  DPRINTFLN("decaduino init start");
  pinMode(13, OUTPUT);
  SPI.setSCK(14);


  success = decaduino.init();
	state = STATE_PING;
	//decaduino.wakeupConfig();

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
	decaduino.setPreambleLength(64);


 decaduino.plmeRxEnableRequest();
 DPRINTFLN("decaduino init finished");
 decaduino.plmeRxDisableRequest();
 timeout = millis();
 txData[0] = MY_ID;
 rxData[1] = 128;

}

void compute_average() {
	if ( (frame_ctr + 1) % 32 == 0) {
		DPRINTF("$Average for chunk: ");
		DPRINTFLN((skew_acc / 32));
		//quantize(skew_acc / 32);

		//signature[8 * chunk_idx + block_idx] = quantize(skew_acc / 32);
		signature[8 * chunk_idx + block_idx] = quantize_16(skew_acc / 32);
		signature_float[8 * chunk_idx + block_idx] = (skew_acc / 32);
		skew_acc = 0;
		block_idx++;
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
            Serial.println("$ Starting boiling");
						target_temp = Serial.parseInt();
						boil(target_temp);
            break;
          case 1:
            Serial.println("$ Switching speed");
						switch_mode(Serial.parseInt()); // 0 or 1
            break;
					case 2:
						Serial.println("$ Setting number of chunks");
						set_n_chunks(Serial.parseInt());
						break;
					case 3:
						Serial.print("$ Temperature:");
						Serial.println(decaduino.getTemperature());
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
			decaduino.plmeRxDisableRequest();
			DPRINTF("$Ping ");
			DPRINTFLN(frame_ctr);
			txData[1] = frame_ctr;
			DPRINTF("$Temperature: ");
			DPRINTFLN(decaduino.getTemperature());
			//decaduino.sleepAfterTx();
      if (!decaduino.pdDataRequest(txData, 2)) {
				Serial.println("$Could not send");
			}

			if ( (MY_ID == 1) && (chunk_idx == max_chunks) ){
				// We're done
				Serial.println("$Done");
				send_signature();
				reset();
			}


			if ((!AS_FAST_AS_I_CAN) && (t_delay != 1)) {
				delay(t_delay);
			}
			decaduino.plmeRxEnableRequest();
			timeout = millis();
			state = STATE_PONG;

      break;

    case STATE_PONG:

			if (Serial.available() > 0) {
				state = STATE_SERIAL;
				next_state = STATE_PONG;
				break;
			}
			if  ((millis() - timeout) > 2 * t_delay ) {
				DPRINTFLN("$Timeout");
				timeout = millis();
				state = STATE_PING;
				break;
			}
      if (decaduino.rxFrameAvailable() ) {
				DPRINTF("$Pong ");
				DPRINTFLN(rxData[1]);



				if (MY_ID == 0) {
					/* Node 0 is following */
					if (rxData[1] != frame_ctr) {
						/* if frame ctr has been incremented, the previous frame has been properly received*/
						global_frame_ctr++;
						last_skew = decaduino.getLastRxSkew();
						skew_acc += last_skew;
						compute_average();
						send_last_frame_data();
						if ((rxData[1]== 0) && (frame_ctr == 255)) {
							// New chunk
							chunk_idx++;
							Serial.print("$Going to next chunk:");
							Serial.println(chunk_idx);
							block_idx = 0;
						}
					}
					else {
						/* correcting last skew value */
						if (skew_acc > 0) {
							skew_acc += decaduino.getLastRxSkew() - last_skew;
							last_skew = decaduino.getLastRxSkew();
						}
					}

					frame_ctr = rxData[1];
					if (chunk_idx == max_chunks) {
						// We're done
						Serial.println("Done");
						send_signature();
						reset();
						delay(30000);
						decaduino.plmeRxEnableRequest();

					}

				}

				if (MY_ID == 1) {
					/* Node 1 is initiating the protocol */
					if (frame_ctr == rxData[1] ) {
						compute_average();
						send_last_frame_data();
						if (frame_ctr == 255) {
							// New chunk
							chunk_idx++;
							block_idx = 0;
							Serial.print("$Going to next chunk:");
							Serial.println(chunk_idx);
						}
						frame_ctr = (frame_ctr + 1) % 256;


						global_frame_ctr++;
						last_skew = decaduino.getLastRxSkew();
						skew_acc += last_skew;
					}
				}




				timeout = millis();

				delay(t_delay);

        state = STATE_PING;
      }
			//delay(10);
			break;

     default:
      state = STATE_PING;
      break;
  }
}
