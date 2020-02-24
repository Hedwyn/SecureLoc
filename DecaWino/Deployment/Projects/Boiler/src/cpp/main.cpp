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
 * @brief Main file the boiler firmware. The boiler firrmware is intended for temperature characterizations.
 * 2 modes are possible, verifier(V) and prover(P).
 * The verifier is sending continously frames, and the prover turns on reception intermittently according to a given Duty Cycle.
 * The Duty Cycle can be set by changing the sleep_time variable (= sleep time between two receptions) of the device.
 * The default sleep_time when the device is turned on is defined in SLEEP_TIME. Otherwise this parameter can be changed though the serial port.
 * Send '1[new_sleep_time]' to modify the value.
 * Send '0' to both P and V to start a boiling process; the prover will switch to a duty cyle of 100% for a maiximum temeprature gradient.
 * See the platform documentation and related papers for details.
 * @see https://github.com/Hedwyn/SecureLoc
 */


#include "Boiler.h"

int main(){
	setup_DB();
	while (1) {
		loop_DB();
		yield();
	}
	return(0);
}
