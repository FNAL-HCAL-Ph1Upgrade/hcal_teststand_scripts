####################################################################
# Type: SCRIPT                                                     #
#                                                                  #
# Description: This script logs all BRIDGE, IGLOO2, and nGCCM      #
# registers as well as the power supply and time. This script is   #
# to run continuously, logging at a user set period.               #
####################################################################

from hcal_teststand import *
from hcal_teststand.hcal_teststand import teststand
from hcal_teststand.utilities import *
import sys
import os
from optparse import OptionParser
from time import sleep, time,strftime
import numpy
from commands import getoutput
import monitor_teststand
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
			for itemps, temps in enumerate(cratetemps):
				log += "Crate {0} -> RM {1} -> {2}\n".format(ts.fe_crates[crate],
									     ts.qie_slots[crate][itemps],
									     temps)
	return log

def log_power(ts):
	log = "%% POWER\n"
	t0 = time_string()		# Get the time before. I get the time again after everything.
#	power_fe = ts_157.get_power(ts)
#	log += "%% POWER\n{0:.2f} V\n{1:.2f} A\n".format(power_fe["V"], power_fe["I"])
	try:
		power_ngccm = ngccm.get_power(ts)		# Take only the crate 1 results (there's only one crate, anyway).
	except Exception as ex:
		print ex
		power_ngccm = {}
	for cra in power_ngccm.keys():
		for result in power_ngccm[cra]:
			log += "{0} -> {1}\n".format(result["cmd"], result["result"])
	return log

def log_registers(ts=False, scale=0):		# Scale 0 is the sparse set of registers, 1 is full.
	log = ""
	log += "%% REGISTERS\n"

	# Will monitor all crates and slots by default
	# Function should be updated to take in an argument that lets you decide which ones to monitor
	# Do everything one crate at a time
	for i, crate in enumerate(ts.fe_crates):
		#log += log_registers_crate_slots(ts, crate, ts.qie_slots[i], scale)
		log += log_igloo2_registers(ts, crate, ts.qie_slots[i], scale)
		log += log_bridge_registers(ts, crate, ts.qie_slots[i], scale)
		log += log_qie_registers(ts, crate, ts.qie_slots[i], scale)
		log += log_control_registers(ts, crate, ts.qie_slots[i], scale)

	return log

def log_registers_crate_slots(ts, crate, slots, scale):

	if scale == 0:
		cmds = [
			"get fec1-LHC_clk_freq",		# Check that this is > 400776 and < 400788.
			"get HE{0}-mezz_ONES".format(crate),		# Check that this is all 1s.
			"get HE{0}-mezz_ZEROES".format(crate),		# Check that is is all 0s.
			"get HE{0}-bkp_pwr_bad".format(crate),
			"get fec1-qie_reset_cnt",
			"get HE{0}-mezz_TMR_ERROR_COUNT".format(crate),
			"get HE{0}-mezz_FPGA_MAJOR_VERSION".format(crate),
			"get HE{0}-mezz_FPGA_MINOR_VERSION".format(crate),
			"get fec1-firmware_dd",
			"get fec1-firmware_mm",
			"get fec1-firmware_yy",
			"get fec1-sfp1_status.RxLOS",
			]
			
		for i in slots:
			for j in ts.qiecards[crate,i]:
				cmds.append("get HE{0}-{1}-{2}-B_RESQIECOUNTER".format(crate,i,j+1))
				cmds.append("get HE{0}-{1}-{2}-B_RESQIECOUNTER".format(crate,i,j+1))
	elif scale == 1:
		cmds=[]
		for i in slots:
			pass
			#cmds.extend(ngccm.get_commands(crate,i)) # TODO: update to HE version
	else:
		cmds = []
	#output = ngccm.send_commands_parsed(ts, cmds)["output"]
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
		 "get HE{0}-{1}-{2}-i_StatusReg_BRIDGE_SPARE".format(crate, slot, qiecard),
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
			      ]

		output = ngfec.send_commands(ts=ts, cmds=cmds_extra, script=True)
		log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	if len(log) > 0:
		return "".join(log)
	else:
		print "No igloo registers found"
		return ""

def log_igloo2_registers(ts, crate, slots, scale=0):
	log = []
	for i in slots:
		# QIE clock phases
		cmds = ["get HE{0}-{1}-Qie41_ck_ph".format(crate, i)]
		if scale == 1:
			for j in ts.qiecards[crate,i]:
                                cmds.extend(["get HE{0}-{1}-Qie{2}_ck_ph".format(crate, i, (j-1)*ts.qies_per_card+nqie+1) for nqie in xrange(ts.qies_per_card)])
		output = ngfec.send_commands(ts=ts, cmds=cmds, script=True)
		log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])		   
		# Other igloo stuff
		for j in ts.qiecards[crate,i]:
			log.append(log_igloo2_registers_per_card(ts, crate, i, j, scale))

	return "".join(log)


def log_bridge_registers_per_card(ts, crate, slot, qiecard, scale):
	# Providing all commands at the same time seems to result in timeout
	# Until better solution is available, I will pass the commands in smaller groups

	cmds1 = ["get HE{0}-{1}-{2}-B_FIRMVERSION_MAJOR".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_FIRMVERSION_MINOR".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_ZEROES".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_ONES".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_ONESZEROES".format(crate, slot, qiecard)
		 ]
	cmds2 = [#"get HE{0}-{1}-{2}-B_WTECOUNTER".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_CLOCKCOUNTER".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_RESQIECOUNTER".format(crate, slot, qiecard),
		 "get HE{0}-{1}-{2}-B_SCRATCH".format(crate, slot, qiecard)
		 ]
	cmds3 = ["get HE{0}-{1}-{2}-B_SHT_temp_f".format(crate, slot, qiecard)
		 ]

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


def log_bridge_registers(ts, crate, slots, scale=0):
	log = []
	for i in slots:
		for j in ts.qiecards[crate,i]:
			log.append(log_bridge_registers_per_card(ts, crate, i, j, scale))

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
        for j in ts.qiecards[crate,slot]:
                for k in xrange(ts.qies_per_card):
                        cmds3.append("get HE{0}-{1}-biasmon{2}_f".format(crate, slot, (j-1)*ts.qies_per_card+1+k))
                        cmds3.append("get HE{0}-{1}-LeakageCurrent{2}_f".format(crate, slot, (j-1)*ts.qies_per_card+1+k))

	output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
	log = ["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output]
	output = ngfec.send_commands(ts=ts, cmds=cmds2, script=True)
	log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	output = ngfec.send_commands(ts=ts, cmds=cmds3, script=True)
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
	if scale == 1:
		histo_output = uhtr.get_histos(ts, 
					       n_orbits=5000, 
					       sepCapID=0, 
					       file_out_base="{0}/histo_{1}".format(logpath, logstring), 
					       script = False)
		log += "\n Took a histo run, with base name {0}/histo_{1}.\n".format(logpath, logstring)

	return log, link_status_parsed

## -----------------------
## -- put back the setup
## -----------------------
def HEsetup(ts):
	log = []

	# loop over the crates and slots
	for icrate, crate in enumerate(ts.fe_crates):
		for slot in ts.qie_slots[icrate]:
			cmds1 = ["put HE{0}-{1}-dac1-daccontrol_RefSelect 0".format(crate, slot),
				 "put HE{0}-{1}-dac1-daccontrol_ChannelMonitorEnable 1".format(crate, slot), 
				 "put HE{0}-{1}-dac1-daccontrol_InternalRefEnable 1".format(crate, slot),
				 "put HE{0}-{1}-dac2-daccontrol_RefSelect 0".format(crate, slot),
				 "put HE{0}-{1}-dac2-daccontrol_ChannelMonitorEnable 1".format(crate, slot), 
				 "put HE{0}-{1}-dac2-daccontrol_InternalRefEnable 1".format(crate, slot)
				 ]

			cmds2 = ["put HE{0}-{1}-biasvoltage[1-48]_f 48*70.0".format(crate, slot)]

			cmds3 = ["put HE{0}-{1}-peltier_stepseconds 900".format(crate, slot),
				 "put HE{0}-{1}-peltier_targettemperature_f 22.0".format(crate, slot),
				 "put HE{0}-{1}-peltier_adjustment_f 0.25".format(crate, slot),
				 "put HE{0}-{1}-peltier_control 1".format(crate, slot)
				 ]
	
			output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
			log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
			output = ngfec.send_commands(ts=ts, cmds=cmds2, script=True)
			log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
			output = ngfec.send_commands(ts=ts, cmds=cmds3, script=True)
			log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
			
			for qiecard in ts.qiecards[crate, slot]:
				cmds4 = ["put HE{0}-{1}-{2}-i_scratch 0xab".format(crate, slot, qiecard),
					 "put HE{0}-{1}-{2}-B_SCRATCH 0xab".format(crate, slot, qiecard)
					 ]
				output = ngfec.send_commands(ts=ts, cmds=cmds4, script=True)
				log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	print "".join(log)

## -----------------------
## -- Main logging order 
## -----------------------
def record(ts=False, path="data/unsorted", scale=0):
	log = ""
	t_string = time_string()[:-4]
	t0 = time_string()

	# Log basics:
	#log += log_power(ts)		# Power
	log += "\n"
#	log += log_version(ts)
	log += log_temp(ts)		# Temperature
	log += "\n"
	log += '%% USERS\n'
	log += getoutput('w')
	log += "\n"
	log += "\n"
	# Log registers:
	log += log_registers(ts=ts, scale=scale)
	log += "\n"
	
	# Log links:
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
# /FUNCTIONS

# MAIN:
if __name__ == "__main__":
	# Script arguments:
	parser = OptionParser()
	parser.add_option("-t", "--teststand", dest="ts",
		default="904",
		help="The name of the teststand you want to use (default is \"904\"). Unless you specify the path, the directory will be put in \"data\".",
		metavar="STR"
	)
	parser.add_option("-o", "--fileName", dest="out",
		default="",
		help="The name of the directory you want to output the logs to (default is \"ts_904\").",
		metavar="STR"
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
	t0_long = time()
	nfailed_tries = 0
	while z == True:
		ntries += 1
		dt = time() - t0
		dt_long = time() - t0_long
		try:
			if (period_long!=0) and (dt_long > period_long*60):
				t0_long = time()
				logpath, log, link_status = record(ts=ts, path=path, scale=1)
				# also parse the log here
				monitor_teststand.monitor_teststand(ts, ts_status, logpath, link_status, 1)
			if (period!=0) and (dt > period*60):
				t0 = time()
				logpath, log, link_status = record(ts=ts, path=path, scale=0)
				# also parse the log here
				monitor_teststand.monitor_teststand(ts, ts_status, logpath, link_status, 0)
			if strftime("%H:%M") == options.ptime:
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
			if nfailed_tries > 2:
				print "System is in a bad state, stopping the logger nicely and alerting experts..."
				monitor_teststand.send_email("Problem for HE Teststand (0)!","Please check system now. Multiple exceptions were caught. Something is not working properly, potentially multiple timeouts from ccmServer.".format(ts.name))
				sys.exit()
			

#		z = False
	
# /MAIN
