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
# CLASSES:
# /CLASSES

# FUNCTIONS:
def log_temp(ts):
	log = ""
	try:
		temps = hcal_teststand.get_temps(ts).values()		# Only care about crate 1
	except Exception as ex:
		print ex
		temps = False
	log += "%% TEMPERATURES\n"
	if temps:
		for results in temps:
			for result in results:
				log += "{0} -> {1}\n".format(result["cmd"], result["result"])
	crates=ts.fe_crates
	cmds=[]
	for crate in crates:
		cmds.extend([
				"get HF{0}-adc58_f".format(crate),		# Check that this is less than 65.
				"get HF{0}-1wA_f".format(crate),
				"get HF{0}-1wB_f".format(crate),
				])
  	output = ngfec.send_commands(ts=ts, cmds=cmds)
	for result in output:
		log += "{0} -> {1}\n".format(result["cmd"], result["result"])
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
	nslots=ts.qie_slots
	crates=ts.fe_crates
	for n in range(len(crates)):
		crate=crates[n]
		nslot=nslots[n]
		if scale == 0:
			cmds = [
				"get fec1-LHC_clk_freq",		# Check that this is > 400776 and < 400788.
				"get HF{0}-mezz_ONES".format(crate),		# Check that this is all 1s.
				"get HF{0}-mezz_ZEROES".format(crate),		# Check that is is all 0s.
				"get HF{0}-bkp_pwr_bad".format(crate),
				"get fec1-qie_reset_cnt",
				"get HF{0}-mezz_TMR_ERROR_COUNT".format(crate),
				"get HF{0}-mezz_FPGA_MAJOR_VERSION".format(crate),
				"get HF{0}-mezz_FPGA_MINOR_VERSION".format(crate),
				"get fec1-firmware_dd",
				"get fec1-firmware_mm",
				"get fec1-firmware_yy",
				"get fec1-sfp1_status.RxLOS",
				"get HF{0}-ngccm_rev_ids".format(crate),
				]
			
			for i in nslot:
				cmds.append("get HF{0}-{1}-B_RESQIECOUNTER".format(crate,i))
				cmds.append("get HF{0}-{1}-B_RESQIECOUNTER".format(crate,i))
				cmds.append("get HF{0}-{1}-iTop_RST_QIE_count".format(crate,i))
				cmds.append("get HF{0}-{1}-iTop_RST_QIE_count".format(crate,i))
				cmds.append("get HF{0}-{1}-iBot_RST_QIE_count".format(crate,i))
				cmds.append("get HF{0}-{1}-iBot_RST_QIE_count".format(crate,i))
				cmds.append("get HF{0}-{1}-iTop_LinkTestMode".format(crate,i))
				cmds.append("get HF{0}-{1}-iBot_LinkTestMode".format(crate,i))
				cmds.append("get HF{0}-{1}-iTop_CntrReg_CImode".format(crate,i))
				cmds.append("get HF{0}-{1}-iBot_CntrReg_CImode".format(crate,i))
			cmds.extend(["get fec1-sfp{0}_prbs_rx_pattern_error_cnt".format(m+1) for m in range(6)])
		elif scale == 1:
			cmds=[]
			for i in nslot:
				cmds.extend(ngccm.get_commands(crate,i))
		else:
			cmds = []
		output = ngfec.send_commands(ts=ts, cmds=cmds)
		for result in output:
			log += "{0} -> {1}\n".format(result["cmd"], result["result"])
	return log

def list2f(List):
	return ["{0:.2f}".format(i) for i in List]
	
def log_links(ts, scale=0):
	log = "%% LINKS\n"
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
			if scale == 1:
				data_full += uhtr_read
			adc_avg.append(list2f([numpy.mean([qad.adc for qad in item]) for item in uhtr.parse_spy(uhtr_read)]))
		log += "crate,slot{0}\tmeanADC:{1}\n".format(cs,adc_avg)
		if scale == 1:
			log += data_full
			log += uhtr.get_linkdtc(ts,cs[0],cs[1])
	return log

def record(ts=False, path="data/unsorted", scale=0):
	log = ""
	t_string = time_string()[:-4]
	t0 = time_string()

	# Log basics:
	log += log_power(ts)		# Power
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
	log += log_links(ts, scale=scale)
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
	return log
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
	
	# Print information:
	print ">> The output directory is {0}.".format(path)
	print ">> The logging period is {0} minutes.".format(period)
	print ">> (A full log will be taken every {0} minutes.)".format(period_long)
	
	# Logging loop:
	z = True
	t0 = 0
	t0_long = time()
	while z == True:
		dt = time() - t0
		dt_long = time() - t0_long
		if (period_long!=0) and (dt_long > period_long*60):
			t0_long = time()
			record(ts=ts, path=path, scale=1)
		if (period!=0) and (dt > period*60):
			t0 = time()
			record(ts=ts, path=path, scale=0)
		if strftime("%H:%M") == options.ptime:
			record(ts=ts, path=path, scale=1)
		else:
			sleep(1)
#		z = False
	
# /MAIN
