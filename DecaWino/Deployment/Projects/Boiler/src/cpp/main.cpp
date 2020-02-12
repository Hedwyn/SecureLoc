#include "Boiler.h"

int main(){
	setup_DB();
	while (1) {
		loop_DB();
		yield();
	}
	return(0);
}
