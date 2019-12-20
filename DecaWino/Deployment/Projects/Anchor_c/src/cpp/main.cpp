#include "anchor_c.h"

int main(){
	anchor_setup();
	while (1) {
		anchor_loop();
		yield();
	}
	return(0);
}
