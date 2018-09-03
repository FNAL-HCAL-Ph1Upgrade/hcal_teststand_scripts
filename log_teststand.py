###################################################################
# Type: SCRIPT                                                     #
#                                                                  #
# Description: This script logs all BRIDGE, IGLOO2, and nGCCM      #
# registers as well as the power supply and time. This script is   #
# to run continuously, logging at a user set period.               #
####################################################################

#from hcal_teststand import *
from hcal_teststand.simpleTestStand import teststand
import hcal_teststand.uhtr as uhtr
from hcal_teststand.utilities import *
#from hcal_teststand.hcal_teststand import teststand
#from hcal_teststand.utilities import *
import sys
import os
from optparse import OptionParser
from time import sleep, time,strftime
import numpy
from commands import getoutput
import monitor_teststand, HEsetup
from teststand_status import TestStandStatus
import socket


# CLASSES:

# /CLASSES

# FUNCTIONS:
def log_temp(ts):
	log = ""
	log += "%% TEMPERATURES\n"

        cmds = []
        cmds2 = []
        cmds3 = []
        for rbx in ts.qiecards:
                for rm in ts.qiecards[rbx]:
                        cmds.extend([
                                "get {0}-{1}-rtdtemperature_f".format(rbx, rm),
                        ])
                        cmds2.append("get {0}-{1}-temperature_f".format(rbx, rm))
                        cmds2.append("get {0}-{1}-humidityS_f_rr".format(rbx, rm))
                        for qieCard in ts.qiecards[rbx][rm]:
                                cmds3.append("get {0}-{1}-{2}-B_SHT_temp_f_rr".format(rbx, rm, qieCard))

        output = ts.ngfec.send_commands(cmds=cmds, script=True)
        for result in output:
                log += "{0} -> {1}\n".format(result["cmd"], result["result"])

        output = ts.ngfec.send_commands(cmds=cmds3, script=True)
        for result in output:
                log += "{0} -> {1}\n".format(result["cmd"], result["result"])

        log += "\n"

	log += "%% HUMIDITY\n"
        output = ts.ngfec.send_commands(cmds=cmds2, script=False, timeout=15)
        for result in output:
                log += "{0} -> {1}\n".format(result["cmd"], result["result"])

        log += "\n"

	log += "%% VOLTAGES\n"

        cmds4 = ["get HB1-1-BVin_f_rr",
                 "get HB1-1-Vdd_f_rr",
                 "get HB1-2-BVin_f_rr",
                 "get HB1-2-Vdd_f_rr",
                 "get HB1a-VIN_voltage_Clk_f_rr",
                 "get HB1a-VIN_voltage_aCntrl_f_rr",
                 "get HB1a-VIN_voltage_bCntrl_f_rr",
                 "get HB1a-1V2_voltage_aCntrl_f_rr",
                 "get HB1a-1V2_voltage_bCntrl_f_rr",
                 "get HB1a-2V5_voltage_Clk_f_rr",
                 "get HB1a-2V5_voltage_aCntrl_f_rr",
                 "get HB1a-2V5_voltage_bCntrl_f_rr",
                 "get HB1a-3V3_voltage_Clk_f_rr",
                 "get HB1a-3V3_voltage_aCntrl_f_rr",
                 "get HB1a-3V3_voltage_bCntrl_f_rr",

         ]
        output = ts.ngfec.send_commands(cmds=cmds4, script=False, timeout=15)
        for result in output:
                log += "{0} -> {1}\n".format(result["cmd"], result["result"])
        
        log += "\n"

        log += "%% Currents\n"
        cmds5 = ["get HB1a-VIN_current_Clk_f_rr",
                 "get HB1a-1V2_current_aCntrl_f_rr",
                 "get HB1a-1V2_current_bCntrl_f_rr",
                 "get HB1a-2V5_current_Clk_f_rr",
                 "get HB1a-3V3_bkp_Clk_f_rr",
                 "get HB1a-3V3_bkp_aCntrl_f_rr",
                 "get HB1a-3V3_bkp_bCntrl_f_rr",
                 "get HB1a-3V3_current_Clk_f_rr"
         ]
        output = ts.ngfec.send_commands(cmds=cmds5, script=False, timeout=15)
        for result in output:
                log += "{0} -> {1}\n".format(result["cmd"], result["result"])
        
        log += "\n"


	return log


def log_biasVoltage():

        log = "%% BIASVOLTAGE\n\n"
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("192.168.1.20", 5025))
        s.sendall("MEAS:VOLT? (@1)\n")
        voltage = s.recv(128).strip("\n")
        s.sendall("MEAS:CURR? (@1)\n")
        current = s.recv(128).strip("\n")
        s.close()

        log += "BiasSupplyVoltage -> {0}\nBiasSupplyCurrent -> {1}\n".format(voltage, current)
        
        return log


def log_prbs(ts, ts_status):
	log = ""

	for crate in ts.fe_crates:
		cmds = [
			"get {0}a-fec_rx_prbs_error_cnt_rr".format(crate),
                        "get {0}a-fec_rx_rs_err_cnt_rr".format(crate),
			"get {0}a-mezz_rx_prbs_error_cnt_rr".format(crate),
			"get {0}a-b2b_rx_prbs_error_cnt_rr".format(crate),		
			"get {0}a-sb2b_rx_prbs_error_cnt_rr".format(crate),
                        "get {0}a-mezz_rx_rsdec_error_cnt_rr".format(crate),
                        "get {0}a-b2b_rx_rsdec_error_cnt_rr".format(crate),
                        "get {0}a-sb2b_rx_rsdec_error_cnt_rr".format(crate),
                        "get {0}a-mezz_RX_PLL_LOCK_LOST_CNT_rr".format(crate),
                        "get {0}a-mezz_rx_rsdec_error_cnt_rr".format(crate),
                        "get {0}a-mezz_TMR_ERROR_COUNT_rr".format(crate),
			"get hbfec2-SinErr_cnt_rr".format(crate),
			"get hbfec2-DbErr_cnt_rr".format(crate),
			"get {0}a-fec_dv_down_cnt_rr".format(crate),
			]
		output = ts.ngfec.send_commands(cmds=cmds, script=True)

                if ts_status != None:
                        for result in output:
                                # check if it's different:
                                if getattr(ts_status.control[crate], result["cmd"].split(" ")[-1].split("-")[-1]) != result["result"]:
                                        log += "{0} -> {1}\n".format(result["cmd"], result["result"])
                                        setattr(ts_status.control[crate], result["cmd"].split(" ")[-1].split("-")[-1], result["result"])
                else:
                        for result in output:
                                log += "{0} -> {1}\n".format(result["cmd"], result["result"])

	return log


def log_humidity(ts):
	log = ""
#	try:
#		hums = ts.get_hums()
#	except Exception as ex:
#		print ex
#		hums = False
#	log += "%% HUMIDITY\n"
# 	if hums:
#		for crate, cratetemps in enumerate(hums):
#			for itemps, temps in enumerate(cratetemps):
#				log += "Crate {0} -> RM {1} -> {2}\n".format(ts.fe_crates[crate],
#									     ts.qie_slots[crate][itemps],
#									     temps)

	return log

def log_power(ts):
	log = "%% POWER\n"
#	t0 = time_string()		# Get the time before. I get the time again after everything.
#	#power_fe = ts_157.get_power(ts,6)
#	power_fe8 = ts_157.get_power(ts,8)
#	#log += "HF {0:.2f} V\nHF {1:.2f} A\n".format(power_fe["V"], power_fe["I"])
#	log += "HE {0:.2f} V\nHE {1:.2f} A\n".format(power_fe8["V"], power_fe8["I"])
#	try:
#		power_ngccm = ngccm.get_power(ts).values()[0]		# Take only the crate 1 results (there's only one crate, anyway).
#	except Exception as ex:
#		print ex
#		power_ngccm = []
#	for result in power_ngccm:
#		log += "{0} -> {1}\n".format(result["cmd"], result["result"])
	return log

def log_registers(ts, scale=0):		# Scale 0 is the sparse set of registers, 1 is full.

        log = log_biasVoltage()

	log += "\n%% LINKSTATE\n"

	for i, crate in enumerate(ts.fe_crates):
                log += log_prbs(ts, None)


	log += "\n%% REGISTERS\n"

	# Will monitor all crates and slots by default
	# Function should be updated to take in an argument that lets you decide which ones to monitor
	# Do everything one crate at a time
	for i, crate in enumerate(ts.fe_crates):
		log += log_registers_crate(ts, crate, scale)
		log += log_igloo2_registers(ts, crate, ts.qie_slots[i], scale)
		log += log_bridge_registers(ts, crate, ts.qie_slots[i], scale)
		log += log_qie_registers(ts, crate, ts.qie_slots[i], scale)
		log += log_pulser_registers(ts, crate, scale)
                log += log_control_registers(ts, crate, ts.qie_slots[i], scale)

	return log



# OZGUR: TO BE UPDATED
def log_registers_crate(ts, crate, scale):
	  
	cmds = [
		"get hbfec2-LHC_clk_freq_rr",		# Check that this is > 400776 and < 400788.
		#"get {0}-mezz_ONES".format(crate),		# Check that this is all 1s.
		#"get {0}-mezz_ZEROES".format(crate),		# Check that is is all 0s.
		"get {0}a-bkp_pwr_bad_rr".format(crate),
		"get {0}a-mezz_scratch".format(crate),
		"get hbfec2-qie_reset_cnt_rr",
		"get hbfec2-sfp3_status.RxLOS_rr",
		"get hbfec2-qie_reset_early_cnt_rr",
		"get hbfec2-qie_reset_ontime_cnt_rr",
		"get hbfec2-qie_reset_late_cnt_rr",
		"get {0}a-fec_bkp_pwr_flip_cnt_rr".format(crate)
		]

		#for i in slots:
	#		for j in ts.qiecards[crate][i]:
#				cmds.append("get {0}-{1}-{2}-B_RESQIECOUNTER".format(crate,i,j+1))
#				cmds.append("get {0}-{1}-{2}-B_RESQIECOUNTER".format(crate,i,j+1))

        #cmds2 = 

	if scale == 1:
		cmds1 = [
		"get hbfec2-fec_firmware_date_rr",
		"get {0}a-mezz_TMR_ERROR_COUNT_rr".format(crate),
		"get {0}a-mezz_FPGA_MAJOR_VERSION_rr".format(crate),
		"get {0}a-mezz_FPGA_MINOR_VERSION_rr".format(crate),
		] # needs updating
		cmds.extend(cmds1)

	output = ts.ngfec.send_commands(cmds=cmds)
	log = ""

	for result in output:
		log += "{0} -> {1}\n".format(result["cmd"], result["result"])
	return log

# Specific HE stuff
def log_qie_registers_per_qie(ts, crate, slot, nqie):
	# We can log all registers every time since the QIEs only contain one big register
	cmds = [ 
		"get {0}-{1}-QIE{2}_CapID0pedestal".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_CapID1pedestal".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_CapID2pedestal".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_CapID3pedestal".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_DiscOn".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_Idcset".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_RangeSet".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_TimingIref".format(crate,slot,nqie), 
		"get {0}-{1}-QIE{2}_ChargeInjectDAC".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_FixRange".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_Lvds".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_TDCMode".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_TimingThresholdDAC".format(crate,slot,nqie),  
		"get {0}-{1}-QIE{2}_CkOutEn".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_Gsel".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_PedestalDAC".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_TGain".format(crate,slot,nqie),
		"get {0}-{1}-QIE{2}_Trim".format(crate,slot,nqie)  
		]
	output = ts.ngfec.send_commands(cmds=cmds, script=True)
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
                for j in ts.qiecards[crate][i]:
                        for k in xrange(ts.qies_per_card):
                                log.append(log_qie_registers_per_qie(ts, crate, i, (j-1)*ts.qies_per_card+k+1))

	# also log calibration unit QIE card
	#for k in xrange(ts.qies_per_card):
	#	log.append(log_qie_registers_per_qie(ts, crate, "calib", k+1))

	return "".join(log)



def log_igloo2_registers_per_card(ts, crate, slot, qiecard, igloo, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get {0}-{1}-{2}-{3}_FPGA_MINOR_VERSION_rr".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_FPGA_MAJOR_VERSION_rr".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_ZerosRegister".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_OnesRegister".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_FPGA_TopOrBottom".format(crate, slot, qiecard, igloo)
                ]
	cmds2 = ["get {0}-{1}-{2}-{3}_StatusReg_InputSpyFifoEmpty".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_StatusReg_InputSpyFifoFull".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_StatusReg_InputSpyWordNum".format(crate, slot, qiecard, igloo), 
		 "get {0}-{1}-{2}-{3}_StatusReg_PLL320MHzLock_rr".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_StatusReg_QieDLLNoLock_rr".format(crate, slot, qiecard, igloo),
                ]
	cmds3 = ["get {0}-{1}-{2}-{3}_WTE_count_rr".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_Clk_count_rr".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_bc0_gen_error".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_bc0_gen_locked_rr".format(crate, slot, qiecard, igloo),
                 "get {0}-{1}-{2}-{3}_bc0_status_count_a_rr".format(crate, slot, qiecard, igloo),
                 "get {0}-{1}-{2}-{3}_bc0_status_count_b_rr".format(crate, slot, qiecard, igloo),
                 "get {0}-{1}-{2}-{3}_bc0_status_missing_a_rr".format(crate, slot, qiecard, igloo),
                 "get {0}-{1}-{2}-{3}_bc0_status_shift_a_rr".format(crate, slot, qiecard, igloo),
                 "get {0}-{1}-{2}-{3}_bc0_status_missing_b_rr".format(crate, slot, qiecard, igloo),
                 "get {0}-{1}-{2}-{3}_bc0_status_shift_b_rr".format(crate, slot, qiecard, igloo),
		 "get {0}-{1}-{2}-{3}_scratch_rr".format(crate, slot, qiecard, igloo)
		 ]
	cmds4 = ["get {0}-{1}-{2}-{3}_ChAlignStatus".format(crate, slot, qiecard, igloo),
                 "get {0}-{1}-{2}-{3}_Spy96bits".format(crate, slot, qiecard, igloo),
		 ]

	output = ts.ngfec.send_commands(cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ts.ngfec.send_commands(cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ts.ngfec.send_commands(cmds=cmds3, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ts.ngfec.send_commands(cmds=cmds4, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])


	if scale == 1:
		cmds_extra = ["get {0}-{1}-{2}-{3}_CntrReg_WrEn_InputSpy_rr".format(crate, slot, qiecard, igloo),
			      "get {0}-{1}-{2}-{3}_CntrReg_CImode_rr".format(crate, slot, qiecard, igloo),
			      "get {0}-{1}-{2}-{3}_CntrReg_bit25_rr".format(crate, slot, qiecard, igloo),
			      "get {0}-{1}-{2}-{3}_CntrReg_bit27_rr".format(crate, slot, qiecard, igloo),
			      "get {0}-{1}-{2}-{3}_CntrReg_bit30_rr".format(crate, slot, qiecard, igloo),
			      "get {0}-{1}-{2}-{3}_CntrReg_bit31_rr".format(crate, slot, qiecard, igloo),
			      "get {0}-{1}-{2}-{3}_CntrReg_type2_Rst_rr".format(crate, slot, qiecard, igloo),
			      "get {0}-{1}-{2}-{3}_CntrReg_type3_Rst_rr".format(crate, slot, qiecard, igloo),
			      ]

		output = ts.ngfec.send_commands(cmds=cmds_extra, script=True)
		log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	if len(log) > 0:
		return "".join(log)
	else:
		print "No igloo registers found"
		return ""

def log_igloo2_registers_calib(ts, crate, igloo, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get {0}-calib-{1}_FPGA_MINOR_VERSION_rr".format(crate, igloo),
		 "get {0}-calib-{1}_FPGA_MAJOR_VERSION_rr".format(crate, igloo),
		 "get {0}-calib-{1}_ZerosRegister_rr".format(crate, igloo),
		 "get {0}-calib-{1}_OnesRegister_rr".format(crate, igloo),
		 "get {0}-calib-{1}_FPGA_TopOrBottom_rr".format(crate, igloo)
		 ]
	cmds2 = ["get {0}-calib-{1}_StatusReg_InputSpyFifoEmpty_rr".format(crate, igloo),
		 "get {0}-calib-{1}_StatusReg_InputSpyFifoFull_rr".format(crate, igloo),
		 "get {0}-calib-{1}_StatusReg_InputSpyWordNum_rr".format(crate, igloo), 
		 "get {0}-calib-{1}_StatusReg_PLL320MHzLock_rr".format(crate, igloo),
		 "get {0}-calib-{1}_StatusReg_QieDLLNoLock_rr".format(crate, igloo),
		 ]
	cmds3 = ["get {0}-calib-{1}_WTE_count_rr".format(crate, igloo),
		 "get {0}-calib-{1}_Clk_count_rr".format(crate, igloo),
                 "get {0}-calib-{1}_bc0_status_count_a_rr".format(crate, igloo),
                 "get {0}-calib-{1}_bc0_status_count_b_rr".format(crate, igloo),
                 "get {0}-calib-{1}_bc0_status_missing_a_rr".format(crate, igloo),
                 "get {0}-calib-{1}_bc0_status_shift_a_rr".format(crate, igloo),
                 "get {0}-calib-{1}_bc0_status_missing_b_rr".format(crate, igloo),
                 "get {0}-calib-{1}_bc0_status_shift_b_rr".format(crate, igloo),
		 "get {0}-calib-{1}_scratch_rr".format(crate, igloo)
		 ]
	cmds4 = ["get {0}-calib-{1}_ChAlignStatus_rr".format(crate, igloo),
                 "get {0}-calib-{1}_Spy96bits_rr".format(crate, igloo),
		 ]

	output = ts.ngfec.send_commands(cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ts.ngfec.send_commands(cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ts.ngfec.send_commands(cmds=cmds3, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ts.ngfec.send_commands(cmds=cmds4, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])


	if scale == 1:
		cmds_extra = ["get {0}-calib-{1}_CntrReg_WrEn_InputSpy_rr".format(crate, igloo),
			      "get {0}-calib-{1}_CntrReg_CImode_rr".format(crate, igloo),
			      "get {0}-calib-{1}_CntrReg_bit25_rr".format(crate, igloo),
			      "get {0}-calib-{1}_CntrReg_bit27_rr".format(crate, igloo),
			      "get {0}-calib-{1}_CntrReg_bit30_rr".format(crate, igloo),
			      "get {0}-calib-{1}_CntrReg_bit31_rr".format(crate, igloo),
			      "get {0}-calib-{1}_CntrReg_type2_Rst_rr".format(crate, igloo),
			      "get {0}-calib-{1}_CntrReg_type3_Rst_rr".format(crate, igloo),
			      ]

		output = ts.ngfec.send_commands(cmds=cmds_extra, script=True)
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
		###cmds = ["get {0}-{1}-Qie41_ck_ph_rr".format(crate, i)]
		###if scale == 1:
		###	for j in ts.qiecards[crate][i]:
		###		cmds.append("wait")
                ###                cmds.extend(["get {0}-{1}-Qie{2}_ck_ph_rr".format(crate, i, (j-1)*ts.qies_per_card+nqie+1) for nqie in xrange(ts.qies_per_card)])
		###output = ts.ngfec.send_commands(cmds=cmds, script=True)
		###log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])		   
		# Other igloo stuff
		for j in ts.qiecards[crate][i]:
                    for igloo in ['iTop', 'iBot']:
			log.append(log_igloo2_registers_per_card(ts, crate, i, j, igloo, scale))

	#cmds = ["get {0}-calib-Qie{1}_ck_ph_rr".format(crate, nqie+1) for nqie in xrange(ts.qies_per_card)]
	#output = ts.ngfec.send_commands(cmds=cmds, script=True)
	#log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])		   
	#log.append(log_igloo2_registers_calib(ts, crate, "iTop", scale))
	#log.append(log_igloo2_registers_calib(ts, crate, "iBot", scale))

	return "".join(log)


def log_bridge_registers_per_card(ts, crate, slot, qiecard, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get {0}-{1}-{2}-B_FIRMVERSION_MAJOR_rr".format(crate, slot, qiecard),
		 "get {0}-{1}-{2}-B_FIRMVERSION_MINOR_rr".format(crate, slot, qiecard),
		 "get {0}-{1}-{2}-B_ZEROES".format(crate, slot, qiecard),
		 "get {0}-{1}-{2}-B_ONES".format(crate, slot, qiecard),
		 "get {0}-{1}-{2}-B_ONESZEROES".format(crate, slot, qiecard)
		 ]
	cmds2 = ["get {0}-{1}-{2}-B_WTECOUNTER_rr".format(crate, slot, qiecard),
		 "get {0}-{1}-{2}-B_CLOCKCOUNTER_rr".format(crate, slot, qiecard),
		 "get {0}-{1}-{2}-B_RESQIECOUNTER_rr".format(crate, slot, qiecard),
		 "get {0}-{1}-{2}-B_SCRATCH_rr".format(crate, slot, qiecard)
		 ]
	cmds3 = ["get {0}-{1}-{2}-B_SHT_temp_f_rr".format(crate, slot, qiecard),]
#		 "get {0}-{1}-{2}-B_SHT_rh_f_rr".format(crate, slot, qiecard)] 

	output = ts.ngfec.send_commands(cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ts.ngfec.send_commands(cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ts.ngfec.send_commands(cmds=cmds3, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	if len(log) > 0:
		return "".join(log)
	else:
		print "No bridge registers found"
		return ""

def log_bridge_registers_calib(ts, crate, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get {0}-calib-B_FIRMVERSION_MAJOR_rr".format(crate),
		 "get {0}-calib-B_FIRMVERSION_MINOR_rr".format(crate),
		 "get {0}-calib-B_ZEROES_rr".format(crate),
		 "get {0}-calib-B_ONES_rr".format(crate),
		 "get {0}-calib-B_ONESZEROES_rr".format(crate)
		 ]
	cmds2 = ["get {0}-calib-B_WTECOUNTER_rr".format(crate),
		 "get {0}-calib-B_CLOCKCOUNTER_rr".format(crate),
		 "get {0}-calib-B_RESQIECOUNTER_rr".format(crate),
		 "get {0}-calib-B_SCRATCH_rr".format(crate)
		 ]
	cmds3 = ["get {0}-calib-B_SHT_temp_f_rr".format(crate),]
#		 "get {0}-calib-B_SHT_rh_f_rr".format(crate)]

	output = ts.ngfec.send_commands(cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ts.ngfec.send_commands(cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ts.ngfec.send_commands(cmds=cmds3, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	if len(log) > 0:
		return "".join(log)
	else:
		print "No bridge registers on CU found"
		return ""


def log_bridge_registers(ts, crate, slots, scale=0):
	log = []
	for i in slots:
		for j in ts.qiecards[crate][i]:
			log.append(log_bridge_registers_per_card(ts, crate, i, j, scale))

	#log.append(log_bridge_registers_calib(ts, crate, scale))

	return "".join(log)


def log_control_registers_per_card(ts, crate, slot, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get {0}-{1}-peltier_adjustment_f".format(crate, slot),
		 "get {0}-{1}-peltier_control".format(crate, slot),
		 "get {0}-{1}-peltier_stepseconds".format(crate, slot),
		 "get {0}-{1}-peltier_targettemperature_f".format(crate, slot),
		 "get {0}-{1}-PeltierVoltage_f_rr".format(crate, slot),
		 "get {0}-{1}-PeltierCurrent_f_rr".format(crate, slot)
		 ]
	cmds2 = ["get {0}-{1}-BVin_f_rr".format(crate, slot),
		 "get {0}-{1}-Vin_f_rr".format(crate, slot),
		 "get {0}-{1}-Vt_f_rr".format(crate, slot),
		 "get {0}-{1}-Vdd_f_rr".format(crate, slot)
		 ]
	cmds3 = []
	cmds4 = []
	# TODO find a better way to handle this
        cmds4.append("get {0}-{1}-biasmon[1-64]_f_rr".format(crate, slot))
        cmds4.append("get {0}-{1}-LeakageCurrent[1-64]_f_rr".format(crate, slot))
	
	output = ts.ngfec.send_commands(cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ts.ngfec.send_commands(cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	#output = ts.ngfec.send_commands(cmds=cmds3, script=True)
	#log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ts.ngfec.send_commands(cmds=cmds4, script=True)
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
	cmds1 = ["get {0}-pulser-ledA-enable_rr".format(crate),
		 "get {0}-pulser-ledA-attenuation_rr".format(crate),
		 "get {0}-pulser-ledA-delay_rr".format(crate),
		 "get {0}-pulser-ledA-bxdelay_rr".format(crate),
		 "get {0}-pulser-ledA-width_rr".format(crate),
		 "get {0}-pulser-ledB-enable_rr".format(crate),
		 "get {0}-pulser-ledB-attenuation_rr".format(crate),
		 "get {0}-pulser-ledB-delay_rr".format(crate),
		 "get {0}-pulser-ledB-bxdelay_rr".format(crate),
		 "get {0}-pulser-ledB-width_rr".format(crate),
		 ]

	output = ts.ngfec.send_commands(cmds=cmds1, script=True)
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
                #if scale == 1:
		log += "{0}\n".format(statusString)
                link_status_parsed.append((uhtr_, statusDict))

        # Now also grab some spy data
#	link_results = uhtr.get_info_links(ts, ts.uhtrs[("HB1",1)].crate, ts.uhtrs[("HB1",1)].slot)
        link_results = {}
        for thing in link_status_parsed:
                link_results[thing[0].ip] = {'active': [], 'orbit': []}
                for link in thing[1]:
                        link_results[thing[0].ip]['active'].append(thing[1][link]['power'])
                        link_results[thing[0].ip]['orbit'].append( thing[1][link]['orbitRates'])

	for cs in link_results.keys():
		active_links = [i for i, active in enumerate(link_results[cs]["active"]) if active]
		#log += "crate,slot{0}\tlinks:{1}\n".format(cs,active_links)
                log += "ip{0}\tlinks:{1}\n".format(cs,active_links)
		orbits = []
		for link in active_links:
			orbits.append(link_results[cs]["orbit"][link])
		log += "ip{0}\torbit:{1}\n".format(cs,list2f(orbits))
		adc_avg = []
		data_full = ""
		for i in active_links:
			uhtr_read = uhtr.get_raw_spy(ts=ts,crate=ts.uhtrs[("HB1",1)].crate,slot=ts.uhtrs[("HB1",1)].slot,n_bx=50,i_link=i)[cs][i]
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
			log += uhtr.get_linkdtc(ts,ts.uhtrs[("HB1",1)].crate,ts.uhtrs[("HB1",1)].slot)

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

def LEDon(ts, amplitude = "0x00", enableB = False):
	for crate in ts.fe_crates:
		cmds1 = ["put {0}-pulser-ledA-enable 1".format(crate),
			 "put {0}-pulser-ledA-attenuation {1}".format(crate, amplitude),
			 "put {0}-pulser-ledA-delay 2".format(crate),
			 "put {0}-pulser-ledA-bxdelay 10".format(crate),
			 "put {0}-pulser-ledA-width 10".format(crate),
			 #"wait", 
			 "put {0}-pulser-ledB-enable {1}".format(crate, "1" if enableB else "0"),
			 "put {0}-pulser-ledA-attenuation {1}".format(crate, amplitude),
			 "put {0}-pulser-ledB-delay 2".format(crate),
			 "put {0}-pulser-ledB-bxdelay 10".format(crate),
			 "put {0}-pulser-ledB-width 10".format(crate),]
		output = ts.ngfec.send_commands(cmds=cmds1, script=True)
		for out in output:
			print "{0} -> {1}".format(out["cmd"], out["result"])

def LEDoff(ts, amplitude = "0xff"):
	for crate in ts.fe_crates:
		cmds1 = ["put {0}-pulser-ledA-enable 0".format(crate),
			 "put {0}-pulser-ledA-attenuation {1}".format(crate, amplitude),
			 "put {0}-pulser-ledA-delay 2".format(crate),
			 "put {0}-pulser-ledA-bxdelay 10".format(crate),
			 "put {0}-pulser-ledA-width 10".format(crate),

			 "put {0}-pulser-ledB-enable 0".format(crate),
			 "put {0}-pulser-ledB-attenuation {1}".format(crate, amplitude),
			 "put {0}-pulser-ledB-delay 2".format(crate),
			 "put {0}-pulser-ledB-bxdelay 10".format(crate),
			 "put {0}-pulser-ledB-width 10".format(crate),]
		output = ts.ngfec.send_commands(cmds=cmds1, script=True)
		for out in output:
			print "{0} -> {1}".format(out["cmd"], out["result"])


def BVscan(ts, biasVoltages):
	#Scan over bias voltages
	print "Starting biasvoltage scan"
	current_time = time_string()[:-4]
	for bv in biasVoltages:
		for i, crate in enumerate(ts.fe_crates):
			for slot in ts.qie_slots[i]:
				cmds1 = ["put {0}-{1}-biasvoltage[1-64]_f 64*{2}".format(crate, slot, bv),]
				output = ts.ngfec.send_commands(cmds=cmds1, script=True)
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
		LEDon(ts, "0x00", True)
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
	ts = teststand()
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
				LEDon(ts, amplitude = "0x00", enableB = True)
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
				sys.exit()
			

#		z = False
	
# /MAIN
