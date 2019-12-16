#include "PKCE.h"


int main(){
	setup_PKCE();
	while (1) {
		loop_PKCE();
		yield();
	}
	return(0);
}
