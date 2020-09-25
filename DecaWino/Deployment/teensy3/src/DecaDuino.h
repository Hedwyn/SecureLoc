// DecaDuino.h
//
// Another DecaWave DW1000 driver for Arduino
// See the README file in this directory for documentation
//
/// \mainpage DecaDuino library for Arduino
///
/// Get the latest version of this documentation here: https://www.irit.fr/~Adrien.Van-Den-Bossche/decaduino/
///
/// DecaDuino is an Arduino library which provides a driver for the DecaWave DW1000 transceiver and modules based on this transceiver, such as DecaWave DWM1000. Since the DW1000 is based on a Ultra Wide Band (UWB) Physical layer, in addition to wireless communication, DecaDuino supports Time-of-Flight (ToF) ranging and can be used as an open framework for protocol evaluation.
///
/// DecaDuino supports the PJRC Teensy 3.2/3.1/3.0. Others Arduino boards have not been tested yet. User feedback on the topic will be greatly appreciated. For this purpose, please use the contact address indicated in the "Contact, feedback and users forum" section of this documentation.
///
/// DecaDuino is a <i>Physical-layer Service Access Point (PHY-SAP)</i>. It provides the two conventional <i>Physical-Data</i> (PD) and <i>Physical Layer Management Entity</i> (PLME) SAPs which enable MAC-level protocols to send/receive data and configure the transceiver (channel, transmission rate, preamble parameters...). Since this framework was designed to aid in the implementation of Time-of-Flight based ranging protocols, DecaDuino also provides access to the DW1000's Physical-level high precision timer (64GHz/40bit) which enables precise message timestamping at both transmission (t_TX) and reception (t_RX). Finally, DecaDuino implements DW1000's advanced synchronization/timestamping functionalities such as delayed transmission and receiver skew evaluation, which are required for efficient centimetre-level ranging protocols using Time-of-Flight.
///
/// DecaDuino comes with several Arduino examples implementing the most popular ranging protocols such as <i>Two-Way Ranging</i> (TWR) and <i>Symetrical Double-Sided Two-Way Ranging</i> (SDS-TWR).
///
/// \image html DecaDuinoStack.png
///
/// DecaDuino has been written by Adrien van den Bossche and Réjane Dalcé at the <a href='http://www.irit.fr'>Institut de Recherche en Informatique de Toulouse</a> (IRIT), France. Thanks to Thierry Val, François Despaux, Laurent Guerby, Ibrahim Fofana and Robert Try for their contributions to DecaDuino.
///
/// \par Download
///
/// Get the <a href='https://github.com/irit-irt/DecaDuino'>current release of the library on github.com</a>. Previous versions (before github.com hosting) are also available in the "Revision History" section of this documentation.
///
/// \par Installation
///
/// To use DecaDuino on a PJRC Teensy 3.2/3.1/3.0, install the <a href='http://www.pjrc.com/teensy/teensyduino.html'>Teensyduino add-on</a> first. Then, download DecaDuino, unzip the files into the libraries sub-directory and relaunch the Arduino environment; you should see the library in the Sketch->Import Library menu, and example sketches in File->Examples->DecaDuino.
///
/// \par Usage
///
/// Remember to import the SPI and Decaduino libraries in your sketches:
/// \code
/// #include <SPI.h>
/// #include <DecaDuino.h>
/// \endcode
/// For more details, please checkout the examples in the File->Examples->DecaDuino menu in the Arduino IDE. The sketches include both frame send/receive examples and ranging protocols implementation examples.
///
/// \par Contact, feedback and users forum
///
/// Please contact <a href='mailto:vandenbo_nospam@irit.fr?subject=[DecaDuino] '>Adrien van den Bossche</a> (remove _nospam) for any question concerning DecaDuino.
///
/// \par Demonstrations
///
/// <a href='https://www.irit.fr/~Adrien.Van-Den-Bossche/DecaWiNo/20150914-DecaWiNo-SDS-TWR-RGB-strip-low_res.mp4'>In this video</a>, a fixed node running DecaDuino executes a ranging session every 100ms with another node, using the TWR protocol. Once the distance to the other node is estimated, the fixed node represents the distance by driving an RGB LED strip: the LED corresponding to the estimated distance is powered up in blue. Note that the strip used in the video is 1m-long and the leds are spaced by 1.65cm. Using a LED strip gives a direct and real-time feedback of the ranging precision and accuracy using DecaDuino.
/// \htmlonly <a href='https://www.irit.fr/~Adrien.Van-Den-Bossche/DecaWiNo/20150914-DecaWiNo-SDS-TWR-RGB-strip-low_res.mp4'> \endhtmlonly
/// \image html TWR_led_strip.jpg
/// \htmlonly </a> \endhtmlonly
///
/// \par Revision History
///
/// - <a href='https://github.com/irit-irt/DecaDuino'>Current release on github.com</a>
///
/// - <a href='https://www.irit.fr/~Adrien.Van-Den-Bossche/decaduino/download/decaduino-1.0.zip'>1.0 (19/03/2016) Initial release</a>
///
/// \par Academic Publications
///
/// DecaDuino has been presented in this academic publication: <a target='_blank' href='https://www.irit.fr/~Adrien.Van-Den-Bossche/papers/WD2016_AVDB_RD_IF_TV_OpenWiNo.pdf'>Adrien Van den Bossche, Rejane Dalce, Nezo Ibrahim Fofana, Thierry Val, <i>DecaDuino: An Open Framework for Wireless Time-of-Flight Ranging Systems</i></a>, IFIP Wireless Days (WD 2016) conference, Toulouse, 23/03/2016-25/03/2016.
///
/// Academic Publications that references DecaDuino <a href='https://www.irit.fr/~Adrien.Van-Den-Bossche/projets_decaduino.php'>are listed here</a>. Please contact <a href='mailto:vandenbo_nospam@irit.fr?subject=[DecaDuino] '>Adrien van den Bossche</a> (remove _nospam) if you want to add your work to this list.
///
/// \par Licence
///
/// DecaDuino's use is subject to licensing, GPL_V3 (http://www.gnu.org/copyleft/gpl.html) or Commercial. Please contact <a href='mailto:vandenbo_nospam@irit.fr?subject=[DecaDuino] '>Adrien van den Bossche</a> (remove _nospam) for Commercial Licensing.
///
/// \page Hardware
///
/// \par Supported Hardware
///
/// DecaDuino supports PJRC Teensy 3.2/3.1/3.0 MCU and DecaWave DM1000 chip and DWM1000 module.
///
/// Please report any successfull operation on others Arduino boards by using the contact address indicated in the "Contact, feedback and users forum" section of this documentation.
///
/// \par Wiring
///
/// A wiring example between Teensy 3.2 and DWM1000 module is given here.
///
/// \image html Wiring.png
///
/// Notes:
/// - In the reception state, the DWM1000 consumes 110mA+ which is more than the Teensy 3.1 can provide. You may add a DC-DC converter on the board to supply VDD 3.3V to the DWM1000. The Teensy 3.2 solves this issue as it embeds an DC-DC converter that can provide 250mA+ on the 3.3V pin.
/// - On the Teensy 3.2/3.1, the default SPI clock pin (SCK) is the pin 13, which the same pin than the onboard LED. We recommend using an alternative SPI clock pin (SCK_, pin 14) on the Teensy. This configuration can be achieved using the following instruction:
/// \code
/// SPI.setSCK(14);
/// \endcode
///
/// \par Hardware examples
///
/// - <a target='_blank' href='http://wino.cc/decawino'>DecaWiNo: <i>Deca-Wireless Node</i></a>. The <a target='_blank' href='http://wino.cc/decawino'>DecaWiNo</a> is the first DecaDuino-compliant hardware built in our facility (IRIT). It includes a PJRC Teensy 3.1, a DecaWave DWM1000 module, a MCP1825 3.3V DC-DC converter and a 5mm RGB LED.
///
/// \image html DecaWiNo.jpg

#ifndef DecaDuino_h
#define DecaDuino_h

#include "Arduino.h"
#include <math.h>

//#define DECADUINO_DEBUG
#define ENABLE_PREAMBLE_DETECTION_IRQ 0
#define ENABLE_SFD_TIMEOUT_IRQ 0

#define DW1000_IRQ0_PIN 9
#define DW1000_IRQ1_PIN 0
#define DW1000_IRQ2_PIN 1
#define DW1000_CS0_PIN 10
#define DW1000_CS1_PIN 10 ///@todo Check Teensy3.1 other SlaveSelect pins
#define DW1000_CS2_PIN 10 ///@todo Check Teensy3.1 other SlaveSelect pins
#define MAX_NB_DW1000_FOR_INTERRUPTS 32
#define DEBUG_STR_LEN 256

#define RANGING_ERROR 0x00

#define DW1000_TIMEBASE 15.65E-12
#define AIR_SPEED_OF_LIGHT 282622876.092008 // @brief Unofficial celerity value, prototype based, by Adrien van den Bossche <vandenbo at univ-tlse2.fr>
#define RANGING_UNIT AIR_SPEED_OF_LIGHT*DW1000_TIMEBASE

#define DWM1000_DEFAULT_ANTENNA_DELAY_VALUE 32847 //@brief Calibration value for DWM1000 on IRIT's DecaWiNo, by Adrien van den Bossche <vandenbo at univ-tlse2.fr>
#define DWM1000_PRF_16MHZ_CIRE_CONSTANT 113.77   //@brief Required for CIRE noise estimation
#define DWM1000_PRF_64MHZ_CIRE_CONSTANT 121.74	//@brief Required for CIRE noise estimation

#define DW1000_TRX_STATUS_IDLE 0
#define DW1000_TRX_STATUS_TX 1
#define DW1000_TRX_STATUS_RX 2
#define DW1000_TRX_STATUS_SLEEP 3


// DW1000 register map

#define DW1000_REGISTER_DEV_ID 				0x00

#define DW1000_REGISTER_EUI 				0x01

#define DW1000_REGISTER_PANADR				0x03
#define DW1000_REGISTER_PANADR_SHORT_ADDRESS_OFFSET	0x00
#define DW1000_REGISTER_PANADR_PANID_OFFSET 		0x02

#define DW1000_REGISTER_SYS_CFG				0x04
#define DW1000_REGISTER_SYS_CFG_RXAUTR_MASK 		0x20000000
#define DW1000_REGISTER_SYS_CFG_PHR_MODE_MASK 		0x00030000
#define DW1000_REGISTER_SYS_CFG_DIS_STXP_MASK 		0x00040000
#define DW1000_REGISTER_SYS_CFG_RXM110K_MASK 		0X00400000
#define DW1000_REGISTER_SYS_CFG_PHR_MODE_SHIFT 		16
#define DW1000_REGISTER_SYS_CFG_DIS_STXP_SHIFT 		18
#define DW1000_REGISTER_SYS_CFG_RXM110K_SHIFT		22


#define DW1000_REGISTER_SYS_TIME			0x06

#define DW1000_REGISTER_TX_FCTRL			0x08
#define DW1000_REGISTER_TX_FCTRL_TXPRF_MASK 0x00030000
#define DW1000_REGISTER_TX_FCTRL_FRAME_LENGTH_MASK	0x000003FF
#define DW1000_REGISTER_TX_FCTRL_TXBR_MASK	0x00006000
#define DW1000_REGISTER_TX_FCTRL_TXBR_SHIFT 13

#define DW1000_REGISTER_OFFSET_DRX_TUNE1A 0x04
#define DW1000_REGISTER_OFFSET_DRX_TUNE1B 0x06
#define DW1000_REGISTER_OFFSET_DRX_TUNE4H 0x26
#define DW1000_REGISTER_OFFSET_DRX_TUNE2 0x08
#define DW1000_REGISTER_DRX_TUNE_PRF16 0x0087
#define DW1000_REGISTER_DRX_TUNE_PRF64 0x008D

#define DW1000_REGISTER_TX_BUFFER			0x09

#define DW1000_REGISTER_DX_TIME				0x0A

#define DW1000_REGISTER_SYS_CTRL			0x0D
#define DW1000_REGISTER_SYS_CTRL_TXSTRT_MASK		0x00000002
#define DW1000_REGISTER_SYS_CTRL_TXDLYS_MASK		0x00000004
#define DW1000_REGISTER_SYS_CTRL_TRXOFF_MASK		0x00000040
#define DW1000_REGISTER_SYS_CTRL_RXENAB_MASK		0x00000100

#define DW1000_REGISTER_SYS_MASK			0x0E
#define DW1000_REGISTER_SYS_MASK_MTXFRS_MASK		0x00000080
#define DW1000_REGISTER_SYS_MASK_MRXDFR_MASK		0x00002000
#define DW1000_REGISTER_SYS_MASK_MRXFCG_MASK		0x00004000
#define DW1000_REGISTER_SYS_MASK_MRXPRD_MASK		0x00000100
#define DW1000_REGISTER_SYS_MASK_MRXSFDD_MASK		0x00000200
#define DW1000_REGISTER_SYS_MASK_MRXSFDTO_MASK		0x04000000

#define DW1000_REGISTER_SYS_STATUS			0x0F
#define DW1000_REGISTER_SYS_STATUS_IRQS_MASK		0x00000001
#define DW1000_REGISTER_SYS_STATUS_TXFRS_MASK		0x00000080
#define DW1000_REGISTER_SYS_STATUS_LDEDONE_MASK 	0x00000400
#define DW1000_REGISTER_SYS_STATUS_RXDFR_MASK		0x00002000
#define DW1000_REGISTER_SYS_STATUS_RXFCG_MASK		0x00004000
#define DW1000_REGISTER_SYS_STATUS_RXFCE_MASK		0x00008000
#define DW1000_REGISTER_SYS_STATUS_RXPRD_MASK		0x00000100
#define DW1000_REGISTER_SYS_STATUS_RXSFDTO_MASK		0x04000000



#define DW1000_REGISTER_RX_FINFO			0x10
#define DW1000_REGISTER_RX_FINFO_RXFLEN_MASK		0x000003FF
#define DW1000_REGISTER_RX_FINFO_RXPACC_MASK		0xFFF00000


#define DW1000_REGISTER_RX_BUFFER			0x11

#define DW1000_REGISTER_RX_RFQUAL					0x12
#define DW1000_REGISTER_RX_RFQUAL_FPAMPL2_MASK 		0XFFFF0000
#define DW1000_REGISTER_RX_RFQUAL_CIRE_MASK 		0X0000FFFF
#define DW1000_REGISTER_OFFSET_FPINDEX				0x05
#define DW1000_REGISTER_OFFSET_FPAMPL1 				0x07
#define DW1000_REGISTER_OFFSET_FPAMPL3 				0x04
#define DW1000_REGISTER_OFFSET_CIRP 				0x04



#define DW1000_REGISTER_RX_TTCKI			0x13

#define DW1000_REGISTER_RX_TTCKO			0x14

#define DW1000_REGISTER_RX_TIME				0x15



#define DW1000_REGISTER_TX_TIME				0x17

#define DW1000_REGISTER_TX_ANTD				0x18

#define DW1000_REGISTER_CHAN_CTRL			0x1F
#define DW1000_REGISTER_CHAN_CTRL_TX_CHAN_MASK		0x0000000F
#define DW1000_REGISTER_CHAN_CTRL_RX_CHAN_MASK		0x000000F0
#define DW1000_REGISTER_CHAN_CTRL_RXPRF_MASK		0x000C0000
#define DW1000_REGISTER_CHAN_CTRL_TX_PCODE_MASK		0x07C00000
#define DW1000_REGISTER_CHAN_CTRL_RX_PCODE_MASK		0xF8000000

#define DW1000_REGISTER_TRANSMIT_POWER_CONTROL 0x1E

#define DW1000_REGISTER_TRANSMIT_POWER_CONTROL_TXPOWSD_MASK 0X00FF0000
#define DW1000_REGISTER_TRANSMIT_POWER_CONTROL_TXPOWPHR_MASK 0x0000FF00

#define DW1000_REGISTER_TRANSMIT_POWER_CONTROL_TXPOWSD_SHIFT 16
#define DW1000_REGISTER_TRANSMIT_POWER_CONTROL_TXPOWPHR_SHIFT 8

#define DWM1000_REGISTER_ACC_MEM 0x25
#define DWM1000_ACCUMULATOR_LENGTH 1016


#define DW1000_REGISTER_DIGITAL_TRANSCEIVER_CONFIGURATION 	0x27
#define DWM1000_REGISTER_OFFSET_RXPACC_NOSAT 				0x2C
#define DWM1000_REGISTER_OFFSET_DRX_SFDTOC					0x20
#define DWM1000_REGISTER_OFFSET_DRX_CAR_INT 				0x28

#define CRI_CHANNEL_2_COEFFICIENT -0.9313E-3
#define FC_1 3494.4
#define N_SAMPLES 1024

#define DW1000_REGISTER_ANALOG_RF_CONFIGURATION 		  	0x28
#define DW1000_REGISTER_OFFSET_RF_RXCTRL					0x0B
#define DW1000_REGISTER_OFFSET_RF_TXCTRL					0x0C

#define DW1000_REGISTER_TRANSMITTER_CALIBRATION_BLOCK		0x2A
#define DW1000_REGISTER_OFFSET_TC_PGDELAY					0x0B

#define DW1000_REGISTER_FREQUENCY_SYNTHESISER_BLOCK_CONTROL	0x2B
#define DW1000_REGISTER_OFFSET_FS_PLLCFG					0x07
#define DW1000_REGISTER_OFFSET_FS_PLLTUNE					0x0B

#define DW1000_REGISTER_AON_CTRL			0x2C
#define DW1000_REGISTER_OFFSET_AON_CTRL			0x02
#define DW1000_REGISTER_AON_CTRL_UPL_CFG_MASK		0x04

#define DW1000_REGISTER_AON_CFG0			0x2C
#define DW1000_REGISTER_OFFSET_AON_CFG0			0x06
#define DW1000_REGISTER_AON_CFG0_SLEEP_EN_MASK		0x01
#define DW1000_REGISTER_AON_CFG0_WAKE_PIN_MASK		0x02
#define DW1000_REGISTER_AON_CFG0_WAKE_SPI_MASK		0x04
#define DW1000_REGISTER_AON_CFG0_WAKE_CNT_MASK		0x08
#define DW1000_REGISTER_AON_CFG0_LPDIV_EN_MASK		0x10


#define DW1000_REGISTER_OFFSET_AON_WCFG		0x00
#define DW1000_REGISTER_AON_WCFG_PRES_SLEEP_MASK	0x01
#define DW1000_REGISTER_AON_WCFG_ONW_LDC_MASK			0x40
#define DW1000_REGISTER_AON_WCFG_WAKE_SPI_MASK		0x04
#define DW1000_REGISTER_AON_WCFG_WAKE_CNT_MASK		0x08
#define DW1000_REGISTER_AON_WCFG_LPDIV_EN_MASK		0x10

#define DWM1000_REGISTER_DIGITAL_DIAGNOSTICS_INTERFACE 0x2F
#define DWM1000_REGISTER_OFFSET_EVC_STO 			0x10
#define DWM1000_REGISTER_OFFSET_EVC_EN 				0x00
#define DWM1000_REGISTER_EVC_EN_MASK 				0x01

#define DW1000_REGISTER_PMSC_CTRL0			0x36
#define DW1000_REGISTER_OFFSET_PMSC_CTRL0		0x00
#define DW1000_REGISTER_FACE_MASK 0x00000040
#define DW1000_REGISTER_AMCE_MASK 0x00008000
#define DW1000_REGISTER_TXCLKS_XTI_MASK 0x00000030

#define DW1000_REGISTER_PMSC_CTRL1			0x36
#define DW1000_REGISTER_OFFSET_PMSC_CTRL1		0x04
#define DW1000_REGISTER_ATXSLP_MASK 0x08


#define DWM1000_REGISTER_OTP 					0x2D
#define DWM1000_REGISTER_OFFSET_OTP_ADDR		0x04
#define DWM1000_REGISTER_OFFSET_OTP_CTRL		0x06
#define DWM1000_REGISTER_OFFSET_OTP_RDAT		0x0A

// some useful addresses in the one-time-programmable memory (DWM1000 user manual page 59)

#define DWM1000_OTP_ADDR_TEMP					0x09
#define DWM1000_OTP_OFFSET_TEMP23				0x00
#define DWM1000_OTP_OFFSET_TEMP_ANT_CAl			0x01
#define DWM1000_OTP_ADDR_V						0x08
#define DWM1000_OTP_OFFSET_V33					0x00
#define DWM1000_OTP_OFFSET_V37					0x01

// values to write for channel control settings (User Manual p154 / 160)

#define DWM1000_RF_RXCTRL_C1235	0xD8
#define DWM1000_RF_RXCTRL_C47	0xBC

#define DWM1000_RF_TXCTRL_C1	0x00005C40
#define DWM1000_RF_TXCTRL_C2	0x00045CA0
#define DWM1000_RF_TXCTRL_C3	0x00086CC0
#define DWM1000_RF_TXCTRL_C4	0x00045C80
#define DWM1000_RF_TXCTRL_C5	0x001E3FE0
#define DWM1000_RF_TXCTRL_C7	0x001E7DE0



#define DWM1000_TC_PGDELAY_C1 	0xC9
#define DWM1000_TC_PGDELAY_C2 	0xC2
#define DWM1000_TC_PGDELAY_C3 	0xC5
#define DWM1000_TC_PGDELAY_C4 	0x95
#define DWM1000_TC_PGDELAY_C5 	0xC0
#define DWM1000_TC_PGDELAY_C7 	0x93

#define DWM1000_FS_PLLCFG_C1 	0x09000407
#define DWM1000_FS_PLLCFG_C24 	0x08400508
#define DWM1000_FS_PLLCFG_C3 	0x08401009
#define DWM1000_FS_PLLCFG_C57 	0x0800041D

#define DWM1000_FS_PLLTUNE_C1 	0x1E
#define DWM1000_FS_PLLTUNE_C24 	0x26
#define DWM1000_FS_PLLTUNE_C3 	0x56
#define DWM1000_FS_PLLTUNE_C57 	0xBE




class DecaDuino {

	public:
		/**
		* @brief DecaDuino Constructor
		* @param slaveSelectPin The slaveSelect pin number
		* @param interruptPin The interrupt pin number
		* @author Adrien van den Bossche
		* @date 20140701
		*/
		DecaDuino(uint8_t slaveSelectPin = DW1000_CS0_PIN, uint8_t interruptPin = DW1000_IRQ0_PIN);

		/**
		* @brief Initializes DecaDuino and DWM1000 without addressing fields filtering (Promiscuous mode)
		* @return true if both DecaDuino and DWM1000 have been successfully initialized
		* @author Adrien van den Bossche
		* @date 20140701
		*/
		boolean init();

		/**
		* @brief Initializes DecaDuino and DWM1000 with given Short Address and Pan Id
		* @param shortAddrAndPanId The 16-bit short address and 16-bit Pan Id as a 32-bit integer where short address in on the LSB.
		* @return true if both DecaDuino and DWM1000 have been successfully initialized
		* @author Adrien van den Bossche
		* @date 20150905
		*/
		boolean init(uint32_t shortAddrAndPanId);

		/**
		* @brief Reset the DW1000 chip
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void resetDW1000();

		/**
		* @brief Set PHR Mode
		* @param mode 0 for standard 127 bytes frame, 3 for extended 1023 bytes frame
		* @return No return
		* @author Laurent GUERBY
		* @date 20170329
		*/
		void setPHRMode(uint8_t mode);

		/**
		* @brief Returns the PHR Mode
		* @return PHR Mode
		* @author Laurent GUERBY
		* @date 20170329
		*/
		uint8_t getPHRMode(void);

		/**
		* @brief Stores the System Time Counter value in the variable referenced by the pointer passed as an input parameter
		* @param p The address of the uint64_t variable
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void getSystemTimeCounter(uint64_t *p);

		/**
		* @brief Returns the System Time Counter value
		* @return The System Time Counter value as a uint64_t
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint64_t getSystemTimeCounter(void);

		/**
		* @brief Gets the PanId (Personnal Area Network Identifier) stored in the DW1000's RAM
		* @return The PanId as an uint16_t value
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint16_t getPanId();

		/**
		* @brief Gets the ShortAddress (16-bit network address, aka IEEE short address) stored in the DW1000's RAM
		* @return The Short Address as an uint16_t value
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint16_t getShortAddress();

		/**
		* @brief Gets the Euid (Extended Unique IDentifier) stored in the DW1000's ROM
		* @return The Identifier as an uint64_t value
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint64_t getEuid();

		/**
		* @brief Sets the PanId (Personnal Area Network Identifier) in the DW1000's RAM
		* @param panId The 16-bit PANID (PAN Identifier)
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void setPanId(uint16_t panId);

		/**
		* @brief Sets the ShortAddress (16-bit network address, aka IEEE short address) in the DW1000's RAM
		* @param shortAddress The 16-bit short address
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void setShortAddress(uint16_t shortAddress);

		/**
		* @brief Sets both the ShortAddress and the PanId in the DW1000's RAM
		* @param shortAddress The 16-bit short address
		* @param panId The 16-bit PANID (PAN Identifier)
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void setShortAddressAndPanId(uint16_t shortAddress, uint16_t panId);

		/**
		* @brief Sets both the ShortAddress and the PanId in the DW1000's RAM
		* @param shortAddressPanId The 16-bit short address and 16-bit Pan Id as a 32-bit integer where short address in on the LSB.
		* @return true if success, false otherwise
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		int setShortAddressAndPanId(uint32_t shortAddressPanId);

		/**
		* @brief Returns the currently configured radio channels
		* @return A byte which MSB is the X channel and the LSB is the X channel
		* @author Réjane Dalce
		* @date 20160109
		*/
 		uint8_t getChannelRaw(void);

		/**
		* @brief Returns the currently configured radio channel
		* @return The channel value as an unsigned byte
		* @author Réjane Dalce
		* @date 20160109
		*/
 		uint8_t getChannel(void);


		/**
		* @brief Returns the currently configured Tx Pulse Repetition Frequency
		* @return The PRF value as an int
		* @author Baptiste Pestourie
		* @date 20190624
		*/
		int getTxPrf(void);

		/**
		* @brief Returns the currently configured Rx Pulse Repetition Frequency
		* @return The PRF value as an int
		* @author Réjane Dalce
		* @date 20161003
		*/
		int getRxPrf(void);


		/**
		* @brief Returns first path index
		* @return fp index an uint16
		* @author Baptiste Pestourie
		* @date 20190503
		*/

		uint16_t getFpIndex(void);

		/**
		* @brief Returns the currently configured Tx Preamble Code
		* @return The Preamble Code value as an unsigned byte
		* @author Réjane Dalce
		* @date 20161003
		*/

		uint8_t getTxPcode(void);


		/**
		* @brief Returns first path amplitude point 1
		* @return the amplitude as an uint8
		* @author Baptiste Pestourie
		* @date 20180614
		*/

		uint16_t getFpAmpl1(void);

		/**
		* @param idx_start index of the first value to report in the CIR accumulator
		* @param idx_end index of the last value to report in the CIR accumulator
		* @param re pointer to the array in which the real part of the samples should be written
		* @param im pointer to the array in which the imaginary part of the samples should be written
		* @brief Gets the real and imaginaries part of the CIR samples accumulated between the two index provided
		* @author Baptiste Pestourie
		* @date 20200701
		*/

		void getAccumulatedCIR(int idx_start, int idx_end, uint16_t *re, uint16_t *im);

		/**
		* @brief Returns first path amplitude point 2
		* @return the amplitude as an uint16
		* @author Baptiste Pestourie
		* @date 20180614
		*/
		uint16_t getFpAmpl2(void);



		/**
		* @brief Returns first path amplitude point 3
		* @return the amplitude as an uint16
		* @author Baptiste Pestourie
		* @date 20180614
		*/
		uint16_t getFpAmpl3(void);


		/**
		* @brief Returns preamble accumulation count
		* @return preamble accumulation count as an uint16
		* @author Baptiste Pestourie
		* @date 20180614
		*/
		uint16_t getRxPacc(void);


		/**
		* @brief Returns first path amplitude power
		* @return first path amplitude power as a double (dBm)
		* @author Baptiste Pestourie
		* @date 20180614
		*/
		double getFpPower(void);


		/**
		* @brief Returns Channel Impulse Response Power
		* @return CIRP as uint16
		* @author Baptiste Pestourie
		* @date 20180614
		*/
		uint16_t getCirp(void);


		/**
		* @brief Returns Standard Deviation of Channel Impulse Response Estimation
		* @return CIRE as uint16
		* @author Baptiste Pestourie
		* @date 20180614
		*/
		uint16_t getCire(void);


		/**
		* @brief Returns received signal power
		* @return RSSI as double (dBm)
		* @author Baptiste Pestourie
		* @date 20180614
		*/
		double getRSSI(void);



		/**
		* @brief Returns signal to noise ratio
		* @return SNR as float
		* @author Baptiste Pestourie
		* @date 20180614
		*/
		float getSNR(void);


		/**
		* @brief Returns the currently configured Rx Preamble Code
		* @return The Preamble Code value as an unsigned byte
		* @author Réjane Dalce
		* @date 20161003
		*/
		uint8_t getRxPcode(void);

		/**
		* @brief returns the current data rate
		* @return Transmit Bit Rate in bbps. Three data rate are available 110 kps, 850 kps and 6.8 Mbps (6800 kbps).
		* @author Baptiste Pestourie
		* @date 20190424
		*/

		int getTBR();

		/**
		* @brief Sets the data rate
		* @param Transmit Bit Rate in bbps. Three data rate are available 110 kps, 850 kps and 6.8 Mbps. Only 110, 850 and 6800 are valid arguments.
		* @return False if an unvalid argument is given, false otherwise.
		* @author Baptiste Pestourie
		* @date 20190424
		*/


		bool setTBR(int bitRate);

		/**
		* @brief Configures transceiver for 110 kps reception
		* @param 1 to enable 0 to disable.
		* @return False if an unvalid argument is given, false otherwise.
		* @author Baptiste Pestourie
		* @date 20190424
		*/

		bool setRx110k(bool enable);


		/**
		* @brief Sets both SD and PHR amplification power at the same vlaue
		* @param coarse and fine grain. Valid values are: -3,0,3,6,...,18 for coarse grain; 0.5,1,...,15.5 for fine grain. Use -3 for coarse grain to disable output.
		* @return True if the configuration was successful, false otherwise
		* @author Baptiste Pestourie
		* @date 20190424
		*/




		bool setTxPower(int coarse,float fine);

		/**
		* @brief Sets SD Tx Power
		* @param coarse and fine grain. Valid values are: -3,0,3,6,...,18 for coarse grain; 0.5,1,...,15.5 for fine grain. Use -3 for coarse grain to disable output.
		* @return False if a wrong argument is given OR if Smart Power Transmit is not disabled, false otherwise
		* @author Baptiste Pestourie
		* @date 20190424
		*/



		bool setSdPower(int coarse,float fine);

		/**
		* @brief Sets PHR Tx Power
		* @param coarse and fine grain. Valid values are: -3,0,3,6,...,18 for coarse grain; 0.5,1,...,15.5 for fine grain. Use -3 for coarse grain to disable output.
		* @return False if a wrong argument is given OR if Smart Power Transmit is not disabled, false otherwise
		* @author Baptiste Pestourie
		* @date 20190424
		*/

		bool setPhrPower(int coarse,float fine);

		/**
		* @brief Returns TX POWSD amplification value
		* @return TX POWSD register value as uint8_t
		* @author Baptiste Pestourie
		* @date 20190425
		*/


		uint8_t readTxPowsd();

		/**
		* @brief Returns TX POWPHR amplification value
		* @return TX POWPHR register value as uint8_t
		* @author Baptiste Pestourie
		* @date 20190425
		*/


		uint8_t readTxPowphr();

		/**
		* @brief Returns Smart Tx Power State
		* @return True if STP is enabled, false otherwise
		* @author Baptiste Pestourie
		* @date 20190425
		*/

		bool getSmartTxPower();

		/**
		* @brief Enables/Disables Smart Transmit Power function. Should be disabled to exceed regulations.
		* @param 0 to disable, 1 to enable
		* @return True if the configuration was successful, false otherwise
		* @author Baptiste Pestourie
		* @date 20190425
		*/

		bool setSmartTxPower(bool enable);
 		/**
		* @brief Sets the Rx & TX radio channels
		* @param the channel to set. Valid values are 1, 2, 3, 4, 5, 7, cf DWM1000 User Manual
		* @return True if the configuration was successful, false otherwise
		* @author Baptiste Pestourie
		* @date 20190329
		*/
 		bool setChannel(uint8_t channel);




 		/**
		* @brief Sets the radio RX channel; changing only the RX channel will
		* @param channel The channel number to set. Valid values are 1, 2, 3, 4, 5, 7.
		* @return True if the channel has been sucessfully set, false otherwise
		* @author Baptiste Pestourie
		* @date 20190329
		*/


		bool setRxChannel(uint8_t channel);

 		/**
		* @brief Sets the radio TX channel
		* @param channel The channel number to set. Valid values are 1, 2, 3, 4, 5, 7.
		* @return True if the channel has been sucessfully set, false otherwise
		* @author Baptiste Pestourie
		* @date 20190329
		*/


		bool setTxChannel(uint8_t channel);

 		/**
		* @brief Sets the Pulse Repetition Frequency
		* @param prf The PRF value to set. Valid values are: 1, 2.
		* @return Indicates whether configuration went well or not
		* @author Réjane Dalce
		* @date 20160310
		*/


		bool setRxPrf(int prf);


 		/**
		* @brief Sets the TX Pulse Repetition Frequency
		* @param The PRF value to set. Valid values are: 1, 2.
		* @return True if success otherwise false
		* @author Baptiste Pestourie
		* @date 20180412
		*/
		bool setTxPrf(int prf);

 		/**
		* @brief Sets the Tx Preamble Code
		* @param pcode The Preamble Code to set. Valid values are: 1-20.
		* @return Indicates whether configuration went well or not
		* @author Réjane Dalce
		* @date 20160310
		*/
		bool setTxPcode(uint8_t pcode);

 		/**
		* @brief Sets the Rx Preamble Code
		* @param pcode The Preamble Code to set. Valid values are: 1-20.
		* @return Indicates whether configuration went well or not
		* @author Réjane Dalce
		* @date 20160310
		*/
		bool setRxPcode(uint8_t pcode);

		/**
		* @brief Returns the preamble length
		* @return A byte representing the preamble length
		* @author François Despaux
		* @date 20160217
		*/
		int getPreambleLength(void);

		/**
		* @brief Sets the preamble length
		* @param plength The preamble length to set. Valid values are: 64, 128, 256, 512, 1024, 1536, 2048, 4096.
		* @return Indicates whether configuration went well or not
		* @author François Despaux
		* @date 20160217
		*/
		bool setPreambleLength(int plength);

		/**
		* @brief displays the full Rx Tx config for quick check/debug
		* @author Baptiste Pestourie
		* @date 20190624
		*/
		void displayRxTxConfig();

		/**
		* @brief Get PAC size
		* @return PAC size (8,16,32 or 64)
		* @author Baptiste Pestourie
		* @date 20190624
		*/
		int getPACSize();

		/**
		* @brief Sets PAC size
		* @param PAC size (8,16,32 or 64)
		* @return False if a wrong argument is given, true otherwise
		* @author Baptiste Pestourie
		* @date 20190430
		*/
		bool setPACSize(int pac_size);


		/**
		* @brief Returns an aligned timestamp to use with pdDataRequest() in case of delayed transmissions
		* @param wantedDelay The required delay to align the delayed transmission
		* @return the aligned timestamp
		* @author Adrien van den Bossche
		* @date 20151028
		*/
		uint64_t alignDelayedTransmission ( uint64_t wantedDelay );

		/**
		* @brief Sends a len-byte frame from buf
		* @param buf The address of the buffer
		* @param len The message length
		* @return true if success, false otherwise
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t pdDataRequest(uint8_t* buf, uint16_t len);

		/**
		* @brief Sends a len-byte frame from buf with an optionnal delay
		* @param buf The address of the buffer
		* @param len The message length
		* @param delayed The delayed flag (true or false)
		* @param time The time to send, based on the DWM1000 System Time Counter at 64GHz
		* @return true if success, false otherwise
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t pdDataRequest(uint8_t* buf, uint16_t len, uint8_t delayed, uint64_t time);

		/**
		* @brief Sends a len-byte frame from buf
		* @param buf The address of the buffer
		* @param len The message length
		* @return true if success, false otherwise
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t send(uint8_t* buf, uint16_t len);

		/**
		* @brief Sends a len-byte frame from buf with an optionnal delay
		* @param buf The address of the buffer
		* @param len The message length
		* @param delayed The delayed flag (true or false)
		* @param time The time to send, based on the DWM1000 System Time Counter at 64GHz
		* @return true if success, false otherwise
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t send(uint8_t* buf, uint16_t len, uint8_t delayed, uint64_t time);


		/**
		* @brief Quick send function that repeats the previous frame
		* @author Baptiste Pestourie
		* @date 20190501
		*/

		void resend();

		/**
		* @brief Sets the RX buffer for future frame reception. Received bytes will be stored at the beginning of the buffer.
		* @param buf The address of the buffer
		* @param len The address of the message length
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void setRxBuffer(uint8_t* buf, uint16_t *len);

		/**
		* @brief Sets the RX buffer for future frame reception. Received bytes will be stored at the end of the buffer of max size.
		* @param buf The address of the buffer
		* @param len The address of the message length
		* @param max The buffer size
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void setRxBuffer(uint8_t* buf, uint16_t *len, uint16_t max);

		/**
		* @brief Sets transceiver mode to receive mode
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void plmeRxEnableRequest(void);

		/**
		* @brief Sets transceiver mode to receive mode. Received bytes will be stored at the end of the buffer of max size.
		* @param max The buffer size
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void plmeRxEnableRequest(uint16_t max);

		/**
		* @brief Sets transceiver mode to receive mode and set the RX buffer for future frame reception.
		* @param buf The address of the buffer
		* @param len The address of the message length
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void plmeRxEnableRequest(uint8_t* buf, uint16_t *len);

		/**
		* @brief Sets transceiver mode to receive mode and set the RX buffer for future frame reception. Received bytes will be stored at the end of the buffer of max size.
		* @param buf The address of the buffer
		* @param len The address of the message length
		* @param max The buffer size
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void plmeRxEnableRequest(uint8_t* buf, uint16_t *len, uint16_t max);

		/**
		* @brief Sets transceiver mode to idle mode.
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void plmeRxDisableRequest(void);

		/**
		* @brief Sets transceiver mode to sleep mode.
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void sleepRequest(void);

		int wakeupConfig();
		/**
		* @brief Indicates if ATXSLP is enabled
		* @return ATXSLP
		* @author Baptiste Pestourie
		* @date 20191124
		*/

		int isAtxslpEnabled();
		/**
		* @brief Sets transceiver mode to sleep mode after TX
		* @return No return
		* @author Baptiste Pestourie
		* @date 20191124
		*/

		void sleepAfterTx(void);



		/**
		* @brief Sets transceiver mode to sleep mode with SPI wkeup
		* @return No return
		* @author Baptiste Pestourie
		* @date 20191124
		*/
		void sleepUntilSpic(void);

		/**
		* @brief Returns true if a frame has been received.
		* @return true if a frame has been received, false otherwise.
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t rxFrameAvailable(void);

		/**
		* @brief Returns true if a frame has been received, copy received bytes in buf and store message length in len.
		* @param buf The address of the buffer
		* @param len The address of the message length
		* @return true if a frame has been received, false otherwise.
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t rxFrameAvailable(uint8_t* buf, uint16_t *len);

		/**
		* @brief Returns true if a frame has been received, copy received bytes in buf and store message length in len. The received bytes shall be copied toward the end of the buffer of size max.
		* @param buf The address of the buffer
		* @param len The address of the message length
		* @param max The buffer size
		* @return true if a frame has been received, false otherwise.
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t rxFrameAvailable(uint8_t* buf, uint16_t *len, uint16_t max);

		/**
		* @brief Returns true if the last transmission request has been succefully completed
		* @return true if the last transmission request has been succefully completed
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		bool hasTxSucceeded(void);

		/**
		* @brief Gets the DecaDuino transceiver status
		* @return the DecaDuino transceiver status
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t getTrxStatus(void);

		/**
		* @brief Gets the raw value from the DW1000's embedded temperature sensor
		* @return The temperature raw value
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t getTemperatureRaw(void);

		/**
		* @brief Gets the temperature value in celsius degrees from the DW1000's embedded temperature sensor
		* @return The temperature value in celsius degrees
		* @author Baptiste Pestourie
		* @date 20180501
		*/
		float getTemperature(void);

		/**
		* @brief Gets the raw value from the DW1000's embedded voltage sensor
		* @return The voltage raw value
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint8_t getVoltageRaw(void);

		/**
		* @brief Gets the voltage value in volts from the DW1000's embedded voltage sensor
		* @return The voltage value in volts
		* @author Baptiste Pestourie
		* @date 20180501

		*/
		float getVoltage(void);

		/**
		* @brief Builds an uint16 value from two uint8 values
		* @param data The address of the uint8_t buffer
		* @return The decoded uint16_t
		* @author Adrien van den Bossche
		* @date 20111123
		*/
		uint16_t decodeUint16 ( uint8_t *data );

		/**
		* @brief Formats an uint16 value as a list of uint8 values
		* @param from The uint16_t value
		* @param to The address of the uint8_t buffer
		* @return No return
		* @author Adrien van den Bossche
		* @date 20111011
		*/
		void encodeUint16 ( uint16_t from, uint8_t *to );

		/**
		* @brief Builds an uint32 value from four uint8 values
		* @param data The address of the uint8_t buffer
		* @return The decoded uint32_t
		* @author Adrien van den Bossche
		* @date 20111123
		*/
		uint32_t decodeUint32 ( uint8_t *data );

		/**
		* @brief Formats an uint32 value as a list of uint8 values
		* @param from The uint32_t value
		* @param to The address of the uint8_t buffer
		* @return No return
		* @author Adrien van den Bossche
		* @date 20111011
		*/
		void encodeUint32 ( uint32_t from, uint8_t *to );

		/**
		* @brief Builds an uint64 value from five uint8 values
		* @param data The address of the uint8_t buffer
		* @return The decoded uint64_t
		*/
		uint64_t decodeUint40 ( uint8_t *data );

		/**
		* @brief Formats an uint64 value with only 5 LSbytes as a list of uint8 values
		* @param from The uint64_t value
		* @param to The address of the uint8_t buffer
		*/
		void encodeUint40 ( uint64_t from, uint8_t *to );

		/**
		* @brief Builds an uint64 value from eight uint8 values
		* @param data The address of the uint8_t buffer
		* @return The decoded uint64_t
		* @author Adrien van den Bossche
		* @date 20140804
		*/
		uint64_t decodeUint64 ( uint8_t *data );

		/**
		* @brief Formats an uint64 value as a list of uint8 values
		* @param from The uint64_t value
		* @param to The address of the uint8_t buffer
		* @return No return
		* @author Adrien van den Bossche
		* @date 20111011
		*/
		void encodeUint64 ( uint64_t from, uint8_t *to );

		/**
		* @brief Builds a float value from four uint8 values
		* @param data The address of the uint8_t buffer
		* @return The decoded float
		* @author Adrien van den Bossche
		* @date 20171020
		*/
		float decodeFloat ( uint8_t *data );

		/**
		* @brief Formats an float value as a list of uint8 values
		* @param from The float value
		* @param to The address of the uint8_t buffer
		* @return No return
		* @author Adrien van den Bossche
		* @date 20171020
		*/
		void encodeFloat ( float from, uint8_t *to );

		/**
		* @brief Prints an uint64_t value on console
		* @param ui64 The uint64_t value
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void printUint64 ( uint64_t ui64 );

		/**
		* @brief Returns the uncorrected timestamp for the beginning of the preamble
		* @return timestamp for the beginning of the last preamble
		* @author Baptiste Pestourie
		* @date 20190430
		*/

		uint64_t getPreambleTimestamp();

		/**
		* @brief gets SFD timeout
		* @return timeout in PAC units
		* @author Baptiste Pestourie
		* @date 20190430
		*/


		uint16_t getSfdTimeout();
		/**
		* @brief Sets SFD timeout
		* @param timeout in PAC units
		* @author Baptiste Pestourie
		* @date 20190430
		*/

		void setSfdTimeout(uint16_t to);


		/**
		* @brief reads SFD timeout counter
		* @return SFD timeout counter as uint16_t
		* @author Baptiste Pestourie
		* @date 20190430
		*/
		uint16_t readSfdTimeoutCounter();

		/**
		* @brief enable events counter
		* @param True to enable, false otherwise
		* @author Baptiste Pestourie
		* @date 20190430
		*/
		void enableCounters(bool enable);

		/**
		* @brief Returns the uncorrected timestamp for the SFD timeout
		* @return timestamp for the SFD timeout
		* @author Baptiste Pestourie
		* @date 20190430
		*/

		uint64_t getSfdtoTimestamp();

		/**
		* @brief Returns preamble flag state
		* @return True if a preamble is being received, false otherwise
		* @author Baptiste Pestourie
		* @date 20190430
		*/

		bool getPreambleFlag();

		/**
		* @brief wait for a new preamble or until timeout
		* @param timeout in micros
		* @return true if a preamble has been received, false if it's a timeout
		* @author Baptiste Pestourie
		* @date 20190430
		*/

		bool waitPreamble(int timeout);

		/**
		* @brief Returns last transmitted frame timestamp based on the DWM1000 System Time Counter at 64GHz
		* @return Last transmitted frame timestamp
		* @author Adrien van den Bossche
		* @date 20140905
		*/
		uint64_t getLastTxTimestamp();

		/**
		* @brief Returns last received frame timestamp based on the DWM1000 System Time Counter at 64GHz
		* @return Last received frame timestamp
		* @author Adrien van den Bossche
		* @date 20140905
		*/
		uint64_t getLastRxTimestamp();

		/**
		* @brief Returns last received frame's clock skew, also designated as clock offset in the Decawave documentation
		* @return Last received frame's clock skew
		* @author Adrien van den Bossche
		* @date 20150905
		*/
		double getLastRxSkew();


		/**
		* @brief Returns last received frame's clock skew using the Carrier Recovery Integrator method (p 148)
		* @return Last received frame's clock skew
		* @author Baptiste Pestourie
		* @date 20190201
		*/
		double getLastRxSkewCRI();

		/**
		* @brief Returns current antenna delay value
		* @return The current antenna delay value
		* @author Adrien van den Bossche
		* @date 20160915
		*/
		uint16_t getAntennaDelay();

		/**
		* @brief Sets the current antenna delay value
		* @param antennaDelay The antenna delay value
		* @return No return
		* @author Adrien van den Bossche
		* @date 20160915
		*/
		void setAntennaDelay(uint16_t newAntennaDelay);


	private:

		/**
		* @brief Reads len bytes on SPI at given address, and store data in buf
		* @param address The source address
		* @param buf The address of the buffer
		* @param len The message length
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void readSpi(uint8_t address, uint8_t* buf, uint16_t len);

		/**
		* @brief Reads len bytes on SPI at given address/subaddress, and store data in buf
		* @param address The source address
		* @param subAddress The source subAddress
		* @param buf The address of the buffer
		* @param len The message length
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void readSpiSubAddress(uint8_t address, uint16_t subAddress, uint8_t* buf, uint16_t len);

		/**
		* @brief Reads a 4-byte word on SPI at given address
		* @param address The source address
		* @return The 4 bytes
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		uint32_t readSpiUint32(uint8_t address);

		/**
		* @brief Writes len bytes on SPI at given address from buf
		* @param address The destination address
		* @param buf The address of the buffer
		* @param len The message length
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void writeSpi(uint8_t address, uint8_t* buf, uint16_t len);

		/**
		* @brief Writes len bytes on SPI at given address/subaddress from buf
		* @param address The destination address
		* @param address The destination sub-address
		* @param buf The address of the buffer
		* @param len The message length
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void writeSpiSubAddress(uint8_t address, uint16_t subAddress, uint8_t* buf, uint16_t len);

		/**
		* @brief Writes a 4-byte word on SPI at given address
		* @param address The destination address
		* @param ui32t The 4-byte word to write on SPI
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void writeSpiUint32(uint8_t address, uint32_t ui32t);


		/**
		* @brief Returns the antenna delay value in the DW1000 register
		* @return The antenna delay value in the register
		* @author Adrien van den Bossche
		* @date 20160915
		*/
		uint16_t getAntennaDelayReg();





		/**
		* @brief Sets the antenna delay value in the DW1000 register
		* @param antennaDelay The antenna delay value
		* @return No return
		* @author Adrien van den Bossche
		* @date 20160915
		*/
		void setAntennaDelayReg(uint16_t newAntennaDelay);



		/**
		* @brief Reads the value in preamble symbol accumalator (unsaturated)
		* @return preamble accumulation count (unsaturated)
		* @author Baptiste Pestourie
		* @date 20190430
		*/
		uint16_t getRxPaccNoSat();



		uint8_t debugStr[DEBUG_STR_LEN];
		void spi_send ( uint8_t u8 );
		void spi_send ( uint16_t u16 );
		void spi_send ( uint8_t* buf, uint16_t len );
		void spi_receive ( uint8_t* buf, uint16_t len );




		uint16_t antennaDelay;

	protected:

		/**
		* @brief The first interrupt function
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		static void isr0();

		/**
		* @brief The second interrupt function
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		static void isr1();

		/**
		* @brief The third interrupt function
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		static void isr2();

		/**
		* @brief The global interrupt function
		* @return No return
		* @author Adrien van den Bossche
		* @date 20141115
		*/
		void handleInterrupt();

		/**
		* @brief Current SPI-bus settings
		*/
		SPISettings currentSPISettings;

		/**
		* @brief Current EUID (Extended Unique IDentifier)
		*/
		uint64_t euid;

		/**
		* @brief The current (or last) PPDU
		*/
		uint8_t *rxData;

		/**
		* @brief The current PPDU length
		*/
		uint16_t *rxDataLen;
		/**
		* @brief The max PPDU length
		*/
		uint16_t rxDataLenMax;

		/**
		* @brief Flag indicating if last reception has data
		*/
		uint8_t rxDataAvailable;

		/**
		* @brief Transceiver status
		*/
		uint8_t trxStatus;

		/**
		* @brief Flag indicating that a new preamble is being received
		*/
		bool preambleFlag = false;

		/**
		* @brief Flag for a SFD timeout
		*/
		bool sfdtoFlag = false;

		/**
		* @brief Timestamp for the start of the preamble
		*/
		uint64_t preambleTimestamp;

		/**
		* @brief Timestamp for sfd timeout
		*/
		uint64_t sfdtoTimestamp;


		/**
		* @brief Timestamp for interruptions
		*/
		uint64_t irqTimestamp;

		/**
		* @brief Flag indicating if last transmission is done
		*/
		bool lastTxOK;

		/**
		* @brief Timestamp of last transmitted frame
		*/
		uint64_t lastTxTimestamp;

		/**
		* @brief Timestamp of last received frame
		*/
		uint64_t lastRxTimestamp;

		/**
		* @brief Last clock offset (aka clock skew)
		*/
		double clkOffset;
		uint8_t _slaveSelectPin;
		uint8_t _interruptPin;
		static DecaDuino* _DecaDuinoInterrupt[];
};

#endif
