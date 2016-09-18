###################################################################
# Type: SCRIPT                                                     #
#                                                                  #
# Description: This script logs all BRIDGE, IGLOO2, and nGCCM      #
# registers as well as the power supply and time. This script is   #
# to run continuously, logging at a user set period.               #
####################################################################

from hcal_teststand import *
import hcal_teststand.uhtr as uhtr
from hcal_teststand.hcal_teststand import teststand
from hcal_teststand.utilities import *
import sys
import os
from optparse import OptionParser
from time import sleep, time,strftime
import numpy
from commands import getoutput
import monitor_teststand, HEsetup
from teststand_status import TestStandStatus

# CLASSES:
# /CLASSES

# FUNCTIONS:
def log_temp(ts):
	log = ""
	try:
		temps = ts.get_temps()
	except Exception as ex:
		print ex
		temps = False
	log += "%% TEMPERATURES\n"
 	if temps:
		for crate, cratetemps in enumerate(temps):
			# cratetemps is a list of temperatures
			for itemps, temps in enumerate(cratetemps):
				# bit of a hack now
				log += "Crate {0} -> RM {1} -> {2}\n".format(ts.fe_crates[crate],
									     ts.qie_slots[crate][itemps],
									     temps[0])

	return log
def log_prbs(ts, ts_status):
	log = ""

	for crate in ts.fe_crates:
		cmds = [
			"get HE{0}-fec_rx_prbs_error_cnt".format(crate),
			"get HE{0}-mezz_rx_prbs_error_cnt".format(crate),
			"get HE{0}-b2b_rx_prbs_error_cnt".format(crate),		
			"get HE{0}-sb2b_rx_prbs_error_cnt".format(crate),
			"get fec{0}-SinErr_cnt".format(crate),
			"get fec{0}-DbErr_cnt".format(crate),
			"get HE{0}-fec_rxlos_cnt".format(crate),
			"get HE{0}-fec_dv_down_cnt".format(crate),
			]
		output = ngfec.send_commands(ts=ts, cmds=cmds, script=True)
		for result in output:
			# check if it's different:
			if getattr(ts_status.control[crate], result["cmd"].split(" ")[-1].split("-")[-1]) != result["result"]:
				log += "{0} -> {1}\n".format(result["cmd"], result["result"])
				setattr(ts_status.control[crate], result["cmd"].split(" ")[-1].split("-")[-1], result["result"])

#		if output != log_last[-1]:
#			log += output
	return log


def log_humidity(ts):
	log = ""
	try:
		hums = ts.get_hums()
	except Exception as ex:
		print ex
		hums = False
	log += "%% HUMIDITY\n"
 	if hums:
		for crate, cratetemps in enumerate(hums):
			for itemps, temps in enumerate(cratetemps):
				log += "Crate {0} -> RM {1} -> {2}\n".format(ts.fe_crates[crate],
									     ts.qie_slots[crate][itemps],
									     temps)

	return log

def log_power(ts):
	log = "%% POWER\n"
	t0 = time_string()		# Get the time before. I get the time again after everything.
	#power_fe = ts_157.get_power(ts,6)
	power_fe8 = ts_157.get_power(ts,8)
	#log += "HF {0:.2f} V\nHF {1:.2f} A\n".format(power_fe["V"], power_fe["I"])
	log += "HE {0:.2f} V\nHE {1:.2f} A\n".format(power_fe8["V"], power_fe8["I"])
	try:
		power_ngccm = ngccm.get_power(ts).values()[0]		# Take only the crate 1 results (there's only one crate, anyway).
	except Exception as ex:
		print ex
		power_ngccm = []
	for result in power_ngccm:
		log += "{0} -> {1}\n".format(result["cmd"], result["result"])
	return log

def log_registers(ts=False, scale=0):		# Scale 0 is the sparse set of registers, 1 is full.
	log = ""
	log += "%% REGISTERS\n"

	# Will monitor all crates and slots by default
	# Function should be updated to take in an argument that lets you decide which ones to monitor
	# Do everything one crate at a time
	for i, crate in enumerate(ts.fe_crates):
		log += log_registers_crate(ts, crate, scale)
		log += log_igloo2_registers(ts, crate, ts.qie_slots[i], scale)
		log += log_bridge_registers(ts, crate, ts.qie_slots[i], scale)
		log += log_qie_registers(ts, crate, ts.qie_slots[i], scale)
		log += log_pulser_registers(ts, crate, scale)
		if ts.name != "HEoven":
			log += log_control_registers(ts, crate, ts.qie_slots[i], scale)

	return log



# OZGUR: TO BE UPDATED
def log_registers_crate(ts, crate, scale):
	  
	cmds = [
		"get fec1-LHC_clk_freq",		# Check that this is > 400776 and < 400788.
		#"get HE{0}-mezz_ONES".format(crate),		# Check that this is all 1s.
		#"get HE{0}-mezz_ZEROES".format(crate),		# Check that is is all 0s.
		"get HE{0}-bkp_pwr_bad".format(crate),
		"get HE{0}-mezz_scratch".format(crate),
		"get fec1-qie_reset_cnt",
		"get fec1-sfp1_status.RxLOS",
		"get fec1-qie_reset_early_cnt",
		"get fec1-qie_reset_ontime_cnt",
		"get fec1-qie_reset_late_cnt",
		]
			
		#for i in slots:
	#		for j in ts.qiecards[crate,i]:
#				cmds.append("get HE{0}-{1}-{2}-B_RESQIECOUNTER".format(crate,i,j+1))
#				cmds.append("get HE{0}-{1}-{2}-B_RESQIECOUNTER".format(crate,i,j+1))
	if scale == 1:
		cmds1 = [
		"get fec1-fec_firmware_date",
		"get HE{0}-mezz_TMR_ERROR_COUNT".format(crate),
		"get HE{0}-mezz_FPGA_MAJOR_VERSION".format(crate),
		"get HE{0}-mezz_FPGA_MINOR_VERSION".format(crate),
		] # needs updating
		cmds.extend(cmds1)

	output = ngfec.send_commands(ts=ts, cmds=cmds)
	log = ""

	for result in output:
		log += "{0} -> {1}\n".format(result["cmd"], result["result"])
	return log

# Specific HE stuff
def log_qie_registers_per_qie(ts, crate, slot, nqie):
	# We can log all registers every time since the QIEs only contain one big register
	cmds = [ 
		"get HE{0}-{1}-QIE{2}_CapID0pedestal".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_CapID1pedestal".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_CapID2pedestal".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_CapID3pedestal".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_DiscOn".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_Idcset".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_RangeSet".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_TimingIref".format(crate,slot,nqie), 
		"get HE{0}-{1}-QIE{2}_ChargeInjectDAC".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_FixRange".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_Lvds".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_TDCmode".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_TimingThresholdDAC".format(crate,slot,nqie),  
		"get HE{0}-{1}-QIE{2}_CkOutEn".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_Gsel".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_PedestalDAC".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_TGain".format(crate,slot,nqie),
		"get HE{0}-{1}-QIE{2}_Trim".format(crate,slot,nqie)  
		]
	
	output = ngfec.send_commands(ts=ts, cmds=cmds, script=True)
	log = ""
	for result in output:
		log += "{0} -> {1}\n".format(result["cmd"], result["result"])
        return log

def log_qie_registers(ts, crate, slots, scale=0):
	log = [""]
	for i in slots:
		# Potentially only read out one or a couple qies for the very frequent logs
		#if scale == 0:
	#		log.append(log_qie_registers_per_qie(ts, crate, i, 45))
	#	elif scale == 1:
                for j in ts.qiecards[crate,i]:
                        for k in xrange(ts.qies_per_card):
                                log.append(log_qie_registers_per_qie(ts, crate, i, (j-1)*ts.qies_per_card+k+1))

	# also log calibration unit QIE card
	for k in xrange(ts.qies_per_card):
		log.append(log_qie_registers_per_qie(ts, crate, "calib", k+1))

	return "".join(log)



def log_igloo2_registers_per_card(ts, crate, slot, qiecard, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get HE{0}-{1}-{2}-i_FPGA_MINOR_VERSION".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_FPGA_MAJOR_VERSION".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_ZerosRegister".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_OnesRegister".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_FPGA_TopOrBottom".format(crate, slot, qiecard)
		 ]
	cmds2 = ["get HE{0}-{1}-{2}-i_StatusReg_InputSpyFifoEmpty".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_StatusReg_InputSpyFifoFull".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_StatusReg_InputSpyWordNum".format(crate, slot, qiecard), 
		 "get HE{0}-{1}-{2}-i_StatusReg_PLL320MHzLock".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_StatusReg_QieDLLNoLock".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_StatusReg_zero".format(crate, slot, qiecard)
		 ]
	cmds3 = ["get HE{0}-{1}-{2}-i_WTE_count".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_Clk_count".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_RST_QIE_count".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_scratch".format(crate, slot, qiecard)
		 ]
	cmds4 = ["get HE{0}-{1}-{2}-i_CapIdErrLink1_count".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-i_CapIdErrLink2_count".format(crate, slot, qiecard), 
		 "get HE{0}-{1}-{2}-i_CapIdErrLink3_count".format(crate, slot, qiecard)
		 ]

	output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ngfec.send_commands(ts=ts, cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ngfec.send_commands(ts=ts, cmds=cmds3, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ngfec.send_commands(ts=ts, cmds=cmds4, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])


	if scale == 1:
		cmds_extra = ["get HE{0}-{1}-{2}-i_CntrReg_WrEn_InputSpy".format(crate, slot, qiecard),
			      "get HE{0}-{1}-{2}-i_CntrReg_OrbHistoRun".format(crate, slot, qiecard),
			      "get HE{0}-{1}-{2}-i_CntrReg_CImode".format(crate, slot, qiecard),
			      "get HE{0}-{1}-{2}-i_CntrReg_InternalQIER".format(crate, slot, qiecard),  
			      "get HE{0}-{1}-{2}-i_CntrReg_OrbHistoClear".format(crate, slot, qiecard),      
			      "get HE{0}-{1}-{2}-i_StatusReg_BRIDGE_SPARE".format(crate, slot, qiecard),
			      ]

		output = ngfec.send_commands(ts=ts, cmds=cmds_extra, script=True)
		log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	if len(log) > 0:
		return "".join(log)
	else:
		print "No igloo registers found"
		return ""

def log_igloo2_registers_calib(ts, crate, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get HE{0}-calib-i_FPGA_MINOR_VERSION".format(crate),
		 "get HE{0}-calib-i_FPGA_MAJOR_VERSION".format(crate),
		 "get HE{0}-calib-i_ZerosRegister".format(crate),
		 "get HE{0}-calib-i_OnesRegister".format(crate),
		 "get HE{0}-calib-i_FPGA_TopOrBottom".format(crate)
		 ]
	cmds2 = ["get HE{0}-calib-i_StatusReg_InputSpyFifoEmpty".format(crate),
		 "get HE{0}-calib-i_StatusReg_InputSpyFifoFull".format(crate),
		 "get HE{0}-calib-i_StatusReg_InputSpyWordNum".format(crate), 
		 "get HE{0}-calib-i_StatusReg_PLL320MHzLock".format(crate),
		 "get HE{0}-calib-i_StatusReg_QieDLLNoLock".format(crate),
		 "get HE{0}-calib-i_StatusReg_zero".format(crate)
		 ]
	cmds3 = ["get HE{0}-calib-i_WTE_count".format(crate),
		 "get HE{0}-calib-i_Clk_count".format(crate),
		 "get HE{0}-calib-i_RST_QIE_count".format(crate),
		 "get HE{0}-calib-i_scratch".format(crate)
		 ]
	cmds4 = ["get HE{0}-calib-i_CapIdErrLink1_count".format(crate),
		 "get HE{0}-calib-i_CapIdErrLink2_count".format(crate), 
		 "get HE{0}-calib-i_CapIdErrLink3_count".format(crate)
		 ]

	output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ngfec.send_commands(ts=ts, cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ngfec.send_commands(ts=ts, cmds=cmds3, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ngfec.send_commands(ts=ts, cmds=cmds4, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])


	if scale == 1:
		cmds_extra = ["get HE{0}-calib-i_CntrReg_WrEn_InputSpy".format(crate),
			      "get HE{0}-calib-i_CntrReg_OrbHistoRun".format(crate),
			      "get HE{0}-calib-i_CntrReg_CImode".format(crate),
			      "get HE{0}-calib-i_CntrReg_InternalQIER".format(crate),  
			      "get HE{0}-calib-i_CntrReg_OrbHistoClear".format(crate),      
			      "get HE{0}-calib-i_StatusReg_BRIDGE_SPARE".format(crate),
			      ]

		output = ngfec.send_commands(ts=ts, cmds=cmds_extra, script=True)
		log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	if len(log) > 0:
		return "".join(log)
	else:
		print "No igloo registers on CU found"
		return ""

def log_igloo2_registers(ts, crate, slots, scale=0):
	log = []
	for i in slots:
		# QIE clock phases
		cmds = ["get HE{0}-{1}-Qie41_ck_ph".format(crate, i)]
		if scale == 1:
			for j in ts.qiecards[crate,i]:
				cmds.append("wait")
                                cmds.extend(["get HE{0}-{1}-Qie{2}_ck_ph".format(crate, i, (j-1)*ts.qies_per_card+nqie+1) for nqie in xrange(ts.qies_per_card)])
		output = ngfec.send_commands(ts=ts, cmds=cmds, script=True)
		log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])		   
		# Other igloo stuff
		for j in ts.qiecards[crate,i]:
			log.append(log_igloo2_registers_per_card(ts, crate, i, j, scale))

	cmds = ["get HE{0}-calib-Qie{1}_ck_ph".format(crate, nqie+1) for nqie in xrange(ts.qies_per_card)]
	output = ngfec.send_commands(ts=ts, cmds=cmds, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])		   
	log.append(log_igloo2_registers_calib(ts, crate, scale))

	return "".join(log)


def log_bridge_registers_per_card(ts, crate, slot, qiecard, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get HE{0}-{1}-{2}-B_FIRMVERSION_MAJOR".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_FIRMVERSION_MINOR".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_FIRMVERSION_SVN".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_ZEROES".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_ONES".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_ONESZEROES".format(crate, slot, qiecard)
		 ]
	cmds2 = ["get HE{0}-{1}-{2}-B_WTECOUNTER".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_CLOCKCOUNTER".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_RESQIECOUNTER".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_SCRATCH".format(crate, slot, qiecard)
		 ]
	cmds3 = ["get HE{0}-{1}-{2}-B_SHT_temp_f".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_SHT_rh_f".format(crate, slot, qiecard)]

	output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ngfec.send_commands(ts=ts, cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ngfec.send_commands(ts=ts, cmds=cmds3, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	if len(log) > 0:
		return "".join(log)
	else:
		print "No bridge registers found"
		return ""

def log_bridge_registers_calib(ts, crate, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get HE{0}-calib-B_FIRMVERSION_MAJOR".format(crate),
		 "get HE{0}-calib-B_FIRMVERSION_MINOR".format(crate),
		 "get HE{0}-calib-B_FIRMVERSION_SVN".format(crate),
		 "get HE{0}-calib-B_ZEROES".format(crate),
		 "get HE{0}-calib-B_ONES".format(crate),
		 "get HE{0}-calib-B_ONESZEROES".format(crate)
		 ]
	cmds2 = ["get HE{0}-calib-B_WTECOUNTER".format(crate),
		 "get HE{0}-calib-B_CLOCKCOUNTER".format(crate),
		 "get HE{0}-calib-B_RESQIECOUNTER".format(crate),
		 "get HE{0}-calib-B_SCRATCH".format(crate)
		 ]
	cmds3 = ["get HE{0}-calib-B_SHT_temp_f".format(crate),
		 "get HE{0}-calib-B_SHT_rh_f".format(crate)]

	output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ngfec.send_commands(ts=ts, cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ngfec.send_commands(ts=ts, cmds=cmds3, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	if len(log) > 0:
		return "".join(log)
	else:
		print "No bridge registers on CU found"
		return ""


def log_bridge_registers(ts, crate, slots, scale=0):
	log = []
	for i in slots:
		for j in ts.qiecards[crate,i]:
			log.append(log_bridge_registers_per_card(ts, crate, i, j, scale))

	log.append(log_bridge_registers_calib(ts, crate, scale))

	return "".join(log)


def log_control_registers_per_card(ts, crate, slot, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get HE{0}-{1}-peltier_adjustment_f".format(crate, slot),
		 "get HE{0}-{1}-peltier_control".format(crate, slot),
		 "get HE{0}-{1}-peltier_stepseconds".format(crate, slot),
		 "get HE{0}-{1}-peltier_targettemperature_f".format(crate, slot),
		 "get HE{0}-{1}-PeltierVoltage_f".format(crate, slot),
		 "get HE{0}-{1}-PeltierCurrent_f".format(crate, slot)
		 ]
	cmds2 = ["get HE{0}-{1}-BVin_f".format(crate, slot),
		 "get HE{0}-{1}-Vin_f".format(crate, slot),
		 "get HE{0}-{1}-Vt_f".format(crate, slot),
		 "get HE{0}-{1}-Vdd_f".format(crate, slot)
		 ]
	cmds3 = []
	cmds4 = []
	# TODO find a better way to handle this
	if ts.name == "HEcharm":
		#for j in [1,15,39]:
	        #	cmds3.append("put HE{0}-{1}-biasvoltage{2}_f 70.0".format(crate, slot, j))
		#for j in [1,15,39]:
		cmds4.append("get HE{0}-{1}-biasmon[1-48]_f".format(crate, slot))
		cmds4.append("get HE{0}-{1}-LeakageCurrent[1-48]_f".format(crate, slot))
	if ts.name == "HEfnal":
		#for j in xrange(1,49):
		#	cmds3.append("put HE{0}-{1}-biasvoltage{2}_f 70.0".format(crate, slot, j))
		for j in xrange(1,49):
			cmds4.append("get HE{0}-{1}-biasmon{2}_f".format(crate, slot, j))
			cmds4.append("get HE{0}-{1}-LeakageCurrent{2}_f".format(crate, slot, j))

	output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ngfec.send_commands(ts=ts, cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	#output = ngfec.send_commands(ts=ts, cmds=cmds3, script=True)
	#log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ngfec.send_commands(ts=ts, cmds=cmds4, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	if len(log) > 0:
		return "".join(log)
	else:
		print "No control card registers found"
		return ""

def log_control_registers(ts, crate, slots, scale=0):
	# registers on the SiPM control card
	log = []
	for i in slots:
		log.append(log_control_registers_per_card(ts, crate, i, scale))

	return "".join(log)

def log_pulser_registers(ts, crate, scale):
	cmds1 = ["get HE{0}-pulser-ledA-enable".format(crate),
		 "get HE{0}-pulser-ledA-amplitude_f".format(crate),
		 "get HE{0}-pulser-ledA-delay_f".format(crate),
		 "get HE{0}-pulser-ledA-bxdelay".format(crate),
		 "get HE{0}-pulser-ledA-width_f".format(crate),
		 "get HE{0}-pulser-ledB-enable".format(crate),
		 "get HE{0}-pulser-ledB-amplitude_f".format(crate),
		 "get HE{0}-pulser-ledB-delay_f".format(crate),
		 "get HE{0}-pulser-ledB-bxdelay".format(crate),
		 "get HE{0}-pulser-ledB-width_f".format(crate),
		 ]

	output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]

	if len(log) > 0:
		return "".join(log)
	else:
		print "No pulser registers found"
		return ""



def list2f(List):
	return ["{0:.2f}".format(i) for i in List]


#def checklinks(ts):
#	print uhtr.initLinks(ts)
	
def log_links(ts, scale=0, logpath="data/unsorted", logstring="_test"):
	log = "%% LINKS\n"

        # First grab the link status
        link_status = uhtr.linkStatus(ts)
        # Now parse it
        link_status_parsed = []
        for (uhtr_, rawStatus) in link_status:
                statusDict, statusString = uhtr.parseLinkStatus(rawStatus)
                if scale == 1:
                        log += "{0}\n".format(statusString)
                link_status_parsed.append((uhtr_, statusDict))

        # Now also grab some spy data
	link_results = uhtr.get_info_links(ts)
	for cs in link_results.keys():
		active_links = [i for i, active in enumerate(link_results[cs]["active"]) if active]
		log += "crate,slot{0}\tlinks:{1}\n".format(cs,active_links)
		orbits = []
		for link in active_links:
			orbits.append(link_results[cs]["orbit"][link])
		log += "crate,slot{0}\torbit:{1}\n".format(cs,list2f(orbits))
		adc_avg = []
		data_full = ""
		for i in active_links:
			uhtr_read = uhtr.get_raw_spy(ts=ts,crate=cs[0],slot=cs[1],n_bx=50,i_link=i)[cs][i]
			#print uhtr_read
			if scale == 1:
				data_full += uhtr_read
                        parsed_spy = uhtr.parse_spy(uhtr_read)
                        if not parsed_spy:
                                log += "Something wrong with links! Found while parsing spy data. \n"
                        else:
                                adc_avg.append(list2f([numpy.mean([qad.adc for qad in item]) for item in parsed_spy]))
		log += "crate,slot{0}\tmeanADC:{1}\n".format(cs,adc_avg)
		if scale == 1:
			log += data_full
			log += uhtr.get_linkdtc(ts,cs[0],cs[1])

	# Take a histo run every now and then
	# if scale == 1:
	# 	histo_output = uhtr.get_histos(ts, 
	# 				       n_orbits=5000, 
	# 				       sepCapID=0, 
	# 				       file_out_base="{0}/histo_{1}".format(logpath, logstring), 
	# 				       script = False)
	# 	log += "\n Took a histo run, with base name {0}/histo_{1}.\n".format(logpath, logstring)

	return log, link_status_parsed

## -----------------------
## -- put back the setup
## -----------------------

def LEDon(ts, amplitude = "1.0", enableB = False):
	for crate in ts.fe_crates:
		cmds1 = ["put HE{0}-pulser-ledA-enable 1".format(crate),
			 "put HE{0}-pulser-ledA-amplitude_f {1}".format(crate, amplitude),
			 "put HE{0}-pulser-ledA-delay_f 1.0".format(crate),
			 "put HE{0}-pulser-ledA-bxdelay 10".format(crate),
			 "put HE{0}-pulser-ledA-width_f 5.".format(crate),
			 #"wait", 
			 "put HE{0}-pulser-ledB-enable {1}".format(crate, "1" if enableB else "0"),
			 "put HE{0}-pulser-ledB-amplitude_f {1}".format(crate, amplitude),
			 "put HE{0}-pulser-ledB-delay_f 1.0".format(crate),
			 "put HE{0}-pulser-ledB-bxdelay 10".format(crate),
			 "put HE{0}-pulser-ledB-width_f 5.".format(crate),]
		output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
		for out in output:
			print "{0} -> {1}".format(out["cmd"], out["result"])

def LEDoff(ts, amplitude = "1.0"):
	for crate in ts.fe_crates:
		cmds1 = ["put HE{0}-pulser-ledA-enable 0".format(crate),
			 "put HE{0}-pulser-ledA-amplitude_f {1}".format(crate, amplitude),
			 "put HE{0}-pulser-ledA-delay_f 1.0".format(crate),
			 "put HE{0}-pulser-ledA-bxdelay 10".format(crate),
			 "put HE{0}-pulser-ledA-width_f 5.".format(crate),

			 "put HE{0}-pulser-ledB-enable 0".format(crate),
			 "put HE{0}-pulser-ledB-amplitude_f {1}".format(crate, amplitude),
			 "put HE{0}-pulser-ledB-delay_f 1.0".format(crate),
			 "put HE{0}-pulser-ledB-bxdelay 10".format(crate),
			 "put HE{0}-pulser-ledB-width_f 5.".format(crate),]
		output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
		for out in output:
			print "{0} -> {1}".format(out["cmd"], out["result"])


def BVscan(ts, biasVoltages):
	#Scan over bias voltages
	print "Starting biasvoltage scan"
	current_time = time_string()[:-4]
	for bv in biasVoltages:
		for i, crate in enumerate(ts.fe_crates):
			for slot in ts.qie_slots[i]:
				cmds1 = ["put HE{0}-{1}-biasvoltage[1-48]_f 48*{2}".format(crate, slot, bv),]
				output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
				for out in output:
					print "{0} -> {1}".format(out["cmd"], out["result"])
	
		sleep(2)
		uhtr.get_histos(ts,
				n_orbits=50000,
				sepCapID=0,
				file_out_base="{0}/histo_BV{2}_{1}".format("data/BVScan", current_time, str(bv).replace(".", "p")),
				script = False)
		uhtr.get_histos(ts,
				n_orbits=50000,
				sepCapID=1,
				file_out_base="{0}/histo_BV{2}_perCID_{1}".format("data/BVScan", current_time, str(bv).replace(".", "p")),
				script = False)
		LEDon(ts, "0.3", True)
		uhtr.get_histos(ts,
				n_orbits=50000,
				sepCapID=0,
				file_out_base="{0}/histo_BV{2}_LED_{1}".format("data/BVScan", current_time, str(bv).replace(".", "p")),
				script = False)
		
		LEDoff(ts)


	#Return BV to default value 
	HEsetup.HEsetup(ts, "bias")

## -----------------------
## -- Main logging order 
## -----------------------
def record(ts=False, path="data/unsorted", scale=0):
	log = ""
	t_string = time_string()[:-4]
	t0 = time_string()

	# Log basics:
	log += log_power(ts)		# Power
	log += "\n"
#	log += log_version(ts)
	if ts.name != "HEoven":
		log += log_temp(ts)		# Temperature
		log += log_humidity(ts)		# Humidity
	log += "\n"
	log += '%% USERS\n'
	log += getoutput('w')
	log += "\n"
	log += "\n"
	# Log registers:
	log += log_registers(ts=ts, scale=scale)
	log += "\n"
	
	# Log links:
	link_status = {}
	if ts.name != "HEoven":
		link_log, link_status = log_links(ts, scale=scale, logpath=path, logstring=t_string)
		log += link_log
		log += "\n"

	
	# Log other:
#	log += "[!!]%% WHAT?\n(There is an error counter, which I believe is in the I2C register. This only counts GBT errors from GLIB to ngCCM. I doubt that Ozgur has updated the GLIB v3 to also count errors from ngCCM to GLIB. That would be useful to have if the counter exists.\nI also want to add, if there is time, an error counter of TMR errors. For the DFN macro TMR code, I implement an error output that goes high if all three outputs are not the same value. This would monitor only a couple of D F/Fs but I think it would be useful to see if any TMR errors are detected.)\n\n"

	# Time:
	t1 = time_string()
	log = "%% TIMES\n{0}\n{1}\n\n".format(t0, t1) + log

	# Write log:
	path += "/{0}".format(t_string[:-7])
	scale_string = ""
	if scale == 0:
		scale_string = "sparse"
	elif scale == 1:
		scale_string = "full"
	print ">> {0}: Created a {1} log file named \"{2}.log\" in directory \"{3}\"".format(t1[:-4], scale_string, t_string, path)
	if not os.path.exists(path):
		os.makedirs(path)
	with open("{0}/{1}.log".format(path, t_string), "w") as out:
		out.write(log.strip())
	return ("{0}/{1}.log".format(path, t_string), log, link_status)



## ------------------------------
##  -- For PRBS error checking --
## ------------------------------
def record_fast(ts=False, ts_status=False, path="data/unsorted"):
	log = log_prbs(ts, ts_status)
	if log != "":
		t1 = time_string()
		log = "%% TIME\n{0}\n".format(t1) + log 
		t_string = t1[:-4]
		path += "/{0}".format(t_string[:-7])
		if not os.path.exists(path):
			os.makedirs(path)
		with open("{0}/{1}_prbs.log".format(path, t_string), "w") as out:
			out.write(log.strip())
			out.write("\n")


# /FUNCTIONS

# MAIN:
if __name__ == "__main__":
	# Script arguments:
	parser = OptionParser()
	parser.add_option("-t", "--teststand", dest="ts",
		default="HEcharm",
		help="The name of the teststand you want to use (default is \"904\"). Unless you specify the path, the directory will be put in \"data\".",
		metavar="STR"
	)
	parser.add_option("-o", "--fileName", dest="out",
		default="",
		help="The name of the directory you want to output the logs to (default is \"ts_904\").",
		metavar="STR"
	)
	parser.add_option("-p", "--prbs", dest="prbs",
		default=1,
		help="The logging period for prbs errors in seconds (default is 1).",
		metavar="FLOAT"
	)
	parser.add_option("-s", "--sparse", dest="spar",
		default=1,
		help="The sparse logging period in minutes (default is 1).",
		metavar="FLOAT"
	)
	parser.add_option("-f", "--full", dest="full",
		default=0,
		help="The full logging period in minutes (default is 0).",
		metavar="FLOAT"
	)
	parser.add_option("-b", "--bias", dest="bias",
		default=0,
		help="The bias voltage scan period in hours (default is 0).",
		metavar="FLOAT"
	)
	parser.add_option("-T", "--time", dest="ptime",
		default='',
		help="The full logging time in a day (default is empty).",
		metavar="STR"
	)

	(options, args) = parser.parse_args()
	name = options.ts
	period = float(options.spar)
	if not options.out:
		path = "data/ts_{0}".format(name)
	elif "/" in options.out:
		path = options.out
	else:
		path = "data/" + options.out
	period_long = float(options.full)
	period_fast = float(options.prbs)
	period_bias = float(options.bias)

	# Set up teststand:
	ts = teststand(name)
	# Get a status object
        ts_status = TestStandStatus(ts)

	# Print information:
	print ">> The output directory is {0}.".format(path)
	print ">> The logging period is {0} minutes.".format(period)
	print ">> (A full log will be taken every {0} minutes.)".format(period_long)
	
	# Logging loop:
	z = True
	t0 = 0
	t0_fast = 0
	t0_long = 0
	t0_bias = 0
	nfailed_tries = 0
	while z == True:
		dt = time() - t0
		dt_long = time() - t0_long
		dt_bias = time() - t0_bias
		dt_fast = time() - t0_fast
		try:
			if (period_bias!=0) and (dt_bias > period_bias*60*60):
				t0_bias = time()
				# do BV scan
				BVscan(ts, [60., 65., 65.5, 66., 66.5, 67., 67.5, 68., 68.5, 69., 69.5, 70., 70.5, 71.])
				print "End BV scan"
			if (period_long!=0) and (dt_long > period_long*60):
				t0_long = time()
				logpath, log, link_status = record(ts=ts, path=path, scale=1)
				# also parse the log here
				monitor_teststand.monitor_teststand(ts, ts_status, logpath, link_status, 1)
				# take an LED run
####JOE TEMP FINDE ME!!!
				print "Taking LED run"
				LEDon(ts, amplitude = "1.0", enableB = True)
				uhtr.get_histos(ts,
                                                n_orbits=100000,
                                                sepCapID=0,
                                                file_out_base="{0}/histo_{1}".format("data/LEDruns", time_string()[:-4]),
                                                script = False)
				LEDoff(ts)
				print "End LED run"
			elif (period!=0) and (dt > period*60):
				t0 = time()
				logpath, log, link_status = record(ts=ts, path=path, scale=0)
				# also parse the log here
				monitor_teststand.monitor_teststand(ts, ts_status, logpath, link_status, 0)
				# take a histogram run
				print "Take histo run"
				uhtr.get_histos(ts,
						n_orbits=100000,
						sepCapID=0,
						file_out_base="{0}/histo_{1}".format("data/long_histos", time_string()[:-4]),
						script = False)           
				print "End histo run"                                
			elif (period_fast!=0) and (dt_fast > period_fast):
				t0_fast = time()
				record_fast(ts=ts, ts_status = ts_status, path=path)
	
			elif strftime("%H:%M") == options.ptime:
				logpath, log, link_status = record(ts=ts, path=path, scale=1)
			        # also parse the log here
				monitor_teststand.monitor_teststand(ts, ts_status, logpath, link_status, 1)
			else:
				sleep(1)
		except KeyboardInterrupt:
			print "bye!"
			sys.exit()
		except Exception as ex:
			nfailed_tries += 1
		 	print "Something weird happened (occasion {0}), perhaps a time-out or very bad data".format(nfailed_tries)
		 	print ex
		 	if nfailed_tries > 10:
		 		print "System is in a bad state, stopping the logger nicely and alerting experts..."
				#monitor_teststand.send_email("Problem for HE Teststand {0}!".format(ts.name),
				#			     "Please check system now. Multiple exceptions were caught. Something is not working properly, potentially multiple timeouts from ccmServer.")
				#sys.exit()
			

#		z = False
	
# /MAIN
