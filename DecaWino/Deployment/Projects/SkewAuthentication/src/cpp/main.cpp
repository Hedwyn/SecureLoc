/****************************************************************************
* Copyright (C) 2019 LCIS Laboratory - Baptiste Pestourie
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, in version 3.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program. If not, see <http://www.gnu.org/licenses/>.
*
* This program is part of the SecureLoc Project @https://github.com/Hedwyn/SecureLoc
 ****************************************************************************/

/**
 * @file main.cpp
 * @author Baptiste Pestourie
 * @date 2020 February 1st
 * @brief Main file for the Skew Authentication firmware. This firrmware has 2 modes, prover(P) and verifier(V).
 * The prover is authenticated based on its skew signature. Send '0' to both nodes to start the authentication process.
 * The two nodes will exchange frames at maximum speed such as inducing a fast temperature gradient on P.
 * V characterizes P's skew throughout the protocol. The signature is sentto the host laptop or RPI on the serial port.
 * When authentication processes are not running this firmware is similar to Boiler.
 * See the platform documentation and related papers for details.
 * @see https://github.com/Hedwyn/SecureLoc
 */

#include "SkewAuthentication.h"

int main(){
	setup_DB();
	while (1) {
		loop_DB();
		yield();
	}
	return(0);
}
