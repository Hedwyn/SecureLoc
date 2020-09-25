#include "aes.h"
#include "anchor_c.h"



int main(){
	delay(1000);
	anchor_setup();
	while (1) {
		delay(1);
		yield();
	}
	return(0);
}