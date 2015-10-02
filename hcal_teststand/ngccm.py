####################################################################
# Type: MODULE                                                     #
#                                                                  #
# Description: This module contains functions for talking to the   #
# ngCCM and the ngccm tool (terribly named).                       #
####################################################################

from re import search, escape
from subprocess import Popen, PIPE
import pexpect
from time import time, sleep
from print_table import *


# CLASSES:
class status:
	# Construction:
	def __init__(self, ts=None, status=[], crate=-1, fw=[]):
		if not ts:
			ts = None
		self.ts = ts
		if not status:
			status = []
		self.status = status
		self.crate = crate
		if not fw:
			fw = []
		self.fw = fw
		if len(self.fw) == 2:
			self.fw_major = self.fw[0]
			self.fw_minor = self.fw[1]
		else:
			self.fw_major = -1
			self.fw_minor = -1
	
	# String behavior
	def __str__(self):
		if self.ts:
			return "<ngccm.status object: {0}>".format(self.status)
		else:
			return "<empty ngccm.status object>"
	
	# Methods:
	def update(self):
		self.good = (False, True)[bool(self.status) and len(self.status) == sum(self.status)]
		if len(self.fw) == 2:
			self.fw_major = self.fw[0]
			self.fw_minor = self.fw[1]
	
	def Print(self, verbose=True):
		if verbose:
			print "[{0}] ngCCM of crate {1} status: {2} <- {3}".format(("!!", "OK")[self.good], self.crate, ("BAD", "GOOD")[self.good], self.status)
			if self.good:
				print "\tFW major: {0}".format(self.fw_major)
				print "\tFW minor: {0}".format(self.fw_minor)
		else:
			print "[{0}] ngCCM of crate {1} status: {2}".format(("!!", "OK")[self.good], self.crate, ("BAD", "GOOD")[self.good])
	
	def log(self):
		output = "%% ngCCM {0}\n".format(self.crate)
		output += "{0}\n".format(int(self.good))
		output += "{0}\n".format(self.status)
		output += "{0}\n".format(self.fw)
		return output.strip()
	# /methods
# /CLASSES

# FUNCTIONS:
def send_commands(ts, cmds):		# Executes ngccm commands in the slowest way, in order to read all of the output.
	log = ""
	raw_output = ""
	if isinstance(cmds, str):
		cmds = [cmds]
	if "quit" not in cmds:
		cmds.append("quit")
	ngfec_cmd = 'ngFEC.exe -z -c -p {0}'.format(ts.ngccm_port)
	if hasattr(ts, "control_hub"):
		ngfec_cmd += " -H {0}".format(ts.control_hub)
	p = pexpect.spawn(ngfec_cmd)
	log += "----------------------------\nYou ran the following script with the ngccm tool:\n"
	for c in cmds:
#		print ">> {0}".format(c)
		p.sendline(c)
		if c != "quit":
			p.expect("{0} #\s|E.*\n".format(c))		# Sometimes a line will come in looking like "get fec1-ctrl #completions = 65844", which should not be grabbed. (So when there's no whitespace it needs to be E for error.)
			raw_output += p.before + p.after
		log += c + "\n"
	log += "----------------------------\n"
	p.expect(pexpect.EOF)
	raw_output += p.before
	return {
		"output": raw_output.strip(),
		"log": log.strip(),
	}

def send_commands_parsed(ts, cmds):		# This executes commands as above, but returns the parsed responses in a list of pairs.
	log = ""
	output = []
	if isinstance(cmds, str):
		cmds = [cmds]
	if "quit" not in cmds:
		cmds.append("quit")
	try:
		ngfec_cmd = 'ngFEC.exe -z -c -p {0}'.format(ts.ngccm_port)
		if hasattr(ts, "control_hub"):
			ngfec_cmd += " -H {0}".format(ts.control_hub)
		p = pexpect.spawn(ngfec_cmd)
		log += "----------------------------\nYou ran the following script with the ngccm tool:\n"
		for c in cmds:
			p.sendline(c)
			t0 = time()
			if c != "quit":
				p.expect("{0} #((\s|E).*)\n".format(escape(c)))
				t1 = time()
				output.append({
					"cmd": c,
					"result": p.match.group(1).strip().replace("'", ""),
					"times": [t0, t1],
				})
	#			print output
			else:
				sleep(1)
			log += c + "\n"
		p.close()
	except Exception as ex:
		print ex
		log += str(ex)
	log += "----------------------------\n"
	return {
		"output": output,
		"log": log.strip(),
	}

def send_commands_fast(ts, cmds):		# This executes ngccm commands in a fast way, but some "get" results might not appear in the output.
	log = ""
	raw_output = ""
	if isinstance(cmds, str):
		cmds = [cmds]
	cmds_str = ""
	for c in cmds:
		cmds_str += "{0}\n".format(c)
	cmds_str += "quit\n"
	log += "----------------------------\nYou ran the following script with the uHTRTool:\n\n{0}\n----------------------------".format(cmds_str)
	ngfec_cmd = 'ngFEC.exe -z -c -p {0}'.format(ts.ngccm_port)
	if hasattr(ts, "control_hub"):
		ngfec_cmd += " -H {0}".format(ts.control_hub)
	p = Popen(['printf "{0}" | {1}'.format(cmds_str, ngfec_cmd)], shell = True, stdout = PIPE, stderr = PIPE)
	raw_output_temp = p.communicate()		# This puts the output of the commands into a list called "raw_output_temp" the first element of the list is stdout, the second is stderr.
	raw_output += raw_output_temp[0] + raw_output_temp[1]
	return {
		"output": raw_output,
		"log": log.strip(),
	}

def get_info(ts, crate):		# Returns a dictionary of information about the ngCCM, such as the FW versions.
	log =""
	version_fw_mez_major = -1
	version_fw_mez_minor = -1
#	command = "get HF{0}-mezz_reg4".format(crate)		# Deprecated
	cmds = [
		"get HF{0}-mezz_FPGA_MAJOR_VERSION".format(crate),
		"get HF{0}-mezz_FPGA_MINOR_VERSION".format(crate),
	]
	output = send_commands_parsed(ts, cmds)["output"]
	result = output[0]["result"]
	if "ERROR" not in output[0]["result"]:
#		version_str_x = "{0:#08x}".format(int(match.group(3),16))		# Deprecated
#		version_fw_mez_major = int(version_str_x[-2:], 16)		# Deprecated
#		version_fw_mez_minor = int(version_str_x[-4:-2], 16)		# Deprecated
		version_fw_mez_major = int(output[0]["result"])
	if "ERROR" not in output[1]["result"]:
		version_fw_mez_minor = int(output[1]["result"])
#	else:
#		log += ">> ERROR: Failed to find FW versions. The command result follows:\n{0} -> {1}".format(cmd, result)
	version_fw_mez = "{0:02d}.{1:02d}".format(version_fw_mez_major, version_fw_mez_minor)
	return {
		"version_fw_mez_major":	version_fw_mez_major,
		"version_fw_mez_minor":	version_fw_mez_minor,
		"version_fw_mez":	version_fw_mez,
		"version_sw":	"?",
		"log":			log.strip(),
	}

def setup(ts):
	log = []
	output = []
	
	if ts:
		for crate in ts.fe_crates:
			result = True
			cmds = [
				"put HF{0}-bkp_pwr_enable 0".format(crate),
				"put HF{0}-bkp_pwr_enable 1".format(crate),
				"put HF{0}-bkp_reset 1".format(crate),
				"put HF{0}-bkp_reset 0".format(crate),
				"get HF{0}-bkp_pwr_bad".format(crate),
			]
			results = send_commands_parsed(ts, cmds)["output"]
			for cmd in results:
				log.append(cmd)
			for cmd in results[:-1]:
				if "OK" not in cmd["result"]:
					result = False
			if results[-1]["result"] == "1":
				result = False
			output.append(result)
		return {
			"result": output,		# A list of booleans, one for each crate.
			"log": log,		# A list of all ngccm commands sent.
		}
	else:
		return {
			"result": output,
			"log": log,
		}

def get_status(ts=None, crate=-1):		# Perform basic checks of the ngCCMs:
	log = ""
	s = status(ts=ts, crate=crate)
	
	if ts:
		# Check that versions are accessible:
		if crate in ts.fe_crates:
			s.crate = crate
			ngccm_info = get_info(ts, crate)
			s.fw = [
				ngccm_info["version_fw_mez_major"],
				ngccm_info["version_fw_mez_minor"]
			]
			if (s.fw[0] != -1):
				s.status.append(1)
			else:
				s.status.append(0)
			s.update()
		else:
			print "ERROR (ngccm.get_status): The crate you want ({0}) is not in the teststand object you supplied.".format(crate)
		
#		# Check the temperature:
#		temp = ts.get_temps()[0]
#		status["temp"] = temp
#		if ts.name == "bhm":
#			if (temp != -1) and (temp < 30.5):
#				status["status"].append(1)
#			else:
#				status["status"].append(0)
#		else:
#			if (temp != -1) and (temp < 37):
#				status["status"].append(1)
#			else:
#				status["status"].append(0)
	return s

def get_status_all(ts=None):
	log = ""
	ss = []
	
	if ts:
		for crate in ts.fe_crates:
			ss.append(get_status(ts=ts, crate=crate))
	return ss

def get_status_bkp(ts):		# Perform basic checks of the FE crate backplanes:
	log = ""
	status = {}
	status["status"] = []
	# Enable, reset, and check the BKP power:
	for crate in ts.fe_crates:
		ngccm_output = send_commands_fast(ts, ["put HF{0}-bkp_pwr_enable 1".format(crate), "put HF{0}-bkp_reset 1".format(crate), "put HF{0}-bkp_reset 0".format(crate)])["output"]
		log += ngccm_output
		ngccm_output = send_commands_fast(ts, "get HF{0}-bkp_pwr_bad".format(crate))["output"]
		log += ngccm_output
		match = search("{0} # ([01])".format("get HF{0}-bkp_pwr_bad".format(crate)), ngccm_output)
		if match:
			status["status"].append((int(match.group(1))+1)%2)
		else:
			log += "ERROR: Could not find the result of \"{0}\" in the output.".format("get HF{0}-bkp_pwr_bad".format(crate))
			status["status"].append(0)
	return status

def get_power(ts=False):
	output = {}
	
	if ts:
		for crate in ts.fe_crates:
			cmds = [
				"get HE{0}-VIN_voltage_f".format(crate),
				"get HE{0}-VIN_current_f".format(crate),
				]
			output[crate] = send_commands_parsed(ts, cmds)["output"]
			return output
	else:
		return output

# enable CI mode
def set_CI_mode(ts , crate , slot , enable = True , DAC = 0 ) :
	
	if( enable ) :
		commands = [#" put HF{0}-{1}-iTop_CntrReg_CImode 1".format(crate,slot)]
			    #"put HF{0}-{1}-iBot_CntrReg_CImode 1".format(crate,slot)
			    "put HF{0}-{1}-QIE1_ChargeInjectDAC {0}".format(crate,slot,DAC)]
	else : 		
		commands = [" put HF{0}-{1}-iTop_CntrReg_CImode 0".format(crate,slot)]
			    #"put HF{0}-{1}-iBot_CntrReg_CImode 0".format(crate,slot)]

	
	ngccm_output = send_commands_parsed( ts , commands )

# This function should be moved to "qie.py":
def get_qie_shift_reg(ts , crate , slot , qie_list = range(1,5) ):
	
	qie_settings = [ "CapID0pedestal", 
			 "CapID1pedestal", 
			 "CapID2pedestal", 
			 "CapID3pedestal", 
			 "ChargeInjectDAC", 
			 "DiscOn", 
			 "FixRange",
			 "Gsel",
			 "Idcset",
			 "Lvds", 
			 "PedestalDAC",
			 "RangeSet", 
			 "TDCmode",
			 "TGain", 
			 "TimingIref", 
			 "TimingThresholdDAC",
			 "Trim"]
	
	table = [qie_settings]
	qieLabels = ["setting"]
	commands = []
	for qie in qie_list :
		#print qie
		for setting in qie_settings : 
			commands.append("get HE{0}-{1}-QIE{2}_{3}".format(crate,slot,qie,setting))
	
	ngccm_output = send_commands_parsed(ts , commands)
	
	for qie in qie_list : 
		qieLabels.append("QIE {0}".format(qie))
		values = []
		for i in ngccm_output["output"] : 		
			for setting in qie_settings : 
				if setting in i["cmd"] and "QIE{0}".format(qie) in i["cmd"]:
					values.append( i["result"] )
				
		table.append( values ) 
	
	#print table
	table_ = [ qieLabels ] 
	for i in zip(*table) : 
		table_.append(i)
	
	print_table(table_)
# /FUNCTIONS
def get_commands(crate,slot):
    commands=[
	"get HF{0}-{1}-B_Adc".format(crate,slot),
	"get HF{0}-{1}-QIE16_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE2_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-iBot_AddrToSERDES".format(crate,slot),
	"get HF{0}-{1}-B_BkPln_GEO".format(crate,slot),
	"get HF{0}-{1}-QIE16_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE2_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-iBot_CapIdErrLink1_count".format(crate,slot),
	"get HF{0}-{1}-B_BkPln_RES_QIE".format(crate,slot),
	"get HF{0}-{1}-QIE16_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE2_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-iBot_CapIdErrLink2_count".format(crate,slot),
	"get HF{0}-{1}-B_BkPln_Spare_1_Counter".format(crate,slot),
	"get HF{0}-{1}-QIE16_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE2_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-iBot_CapIdErrLink3_count".format(crate,slot),
	"get HF{0}-{1}-B_BkPln_Spare_2_Counter".format(crate,slot),
	"get HF{0}-{1}-QIE16_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE2_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-iBot_Clk_count".format(crate,slot),
	"get HF{0}-{1}-B_BkPln_Spare_3_Counter".format(crate,slot),
	"get HF{0}-{1}-QIE16_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE2_DiscOn".format(crate,slot),
	"get HF{0}-{1}-iBot_CntrReg_CImode".format(crate,slot),
	"get HF{0}-{1}-B_BkPln_WTE".format(crate,slot),
	"get HF{0}-{1}-QIE16_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE2_FixRange".format(crate,slot),
	"get HF{0}-{1}-iBot_CtrlToSERDES_i2c_go".format(crate,slot),
	"get HF{0}-{1}-B_Bottom_RESET_N".format(crate,slot),
	"get HF{0}-{1}-QIE16_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE2_IdcBias".format(crate,slot),
	"get HF{0}-{1}-iBot_CtrlToSERDES_i2c_write".format(crate,slot),
	"get HF{0}-{1}-B_Bottom_TRST_N".format(crate,slot),
	"get HF{0}-{1}-QIE16_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE2_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-iBot_DataFromSERDES".format(crate,slot),
	"get HF{0}-{1}-B_CLOCKCOUNTER".format(crate,slot),
	"get HF{0}-{1}-QIE16_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE2_Lvds".format(crate,slot),
	"get HF{0}-{1}-iBot_DataToSERDES".format(crate,slot),
	"get HF{0}-{1}-B_Eic1".format(crate,slot),
	"get HF{0}-{1}-QIE17_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE2_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-iBot_FPGA_MAJOR_VERSION".format(crate,slot),
	"get HF{0}-{1}-B_Eic2".format(crate,slot),
	"get HF{0}-{1}-QIE17_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE2_RangeSet".format(crate,slot),
	"get HF{0}-{1}-iBot_FPGA_MINOR_VERSION".format(crate,slot),
	"get HF{0}-{1}-B_FIRMVERSION_MAJOR".format(crate,slot),
	"get HF{0}-{1}-QIE17_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE2_TGain".format(crate,slot),
	"get HF{0}-{1}-iBot_FPGA_TopOrBottom".format(crate,slot),
	"get HF{0}-{1}-B_FIRMVERSION_MINOR".format(crate,slot),
	"get HF{0}-{1}-QIE17_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE2_TimingIref".format(crate,slot),
	"get HF{0}-{1}-iBot_LinkTestMode".format(crate,slot),
	"get HF{0}-{1}-B_FIRMVERSION_SVN".format(crate,slot),
	"get HF{0}-{1}-QIE17_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE2_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-B_GBTX_DataValid".format(crate,slot),
	"get HF{0}-{1}-QIE17_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE2_Trim".format(crate,slot),
	"get HF{0}-{1}-iBot_LinkTestPattern".format(crate,slot),
	"get HF{0}-{1}-B_GBTX_Override".format(crate,slot),
	"get HF{0}-{1}-QIE17_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE3_CalMode".format(crate,slot),
	"get HF{0}-{1}-iBot_OnesRegister".format(crate,slot),
	"get HF{0}-{1}-B_GBTX_ResetB".format(crate,slot),
	"get HF{0}-{1}-QIE17_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE3_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-iBot_RST_QIE_count".format(crate,slot),
	"get HF{0}-{1}-B_GBTX_TxRdy".format(crate,slot),
	"get HF{0}-{1}-QIE17_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE3_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-iBot_Spy96bits".format(crate,slot),
	"get HF{0}-{1}-B_I2CBUSID".format(crate,slot),
	"get HF{0}-{1}-QIE17_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE3_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-iBot_StatFromSERDES_busy".format(crate,slot),
	"get HF{0}-{1}-B_ID1".format(crate,slot),
	"get HF{0}-{1}-QIE17_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE3_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-iBot_StatFromSERDES_i2c_counter".format(crate,slot),
	"get HF{0}-{1}-B_ID2".format(crate,slot),
	"get HF{0}-{1}-QIE17_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE3_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-iBot_StatusReg_PLL320MHzLock".format(crate,slot),
	"get HF{0}-{1}-B_JTAGSEL".format(crate,slot),
	"get HF{0}-{1}-QIE17_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE3_DiscOn".format(crate,slot),
	"get HF{0}-{1}-iBot_StatusReg_QieDLLNoLock".format(crate,slot),
	"get HF{0}-{1}-B_JTAG_Select_Board".format(crate,slot),
	"get HF{0}-{1}-QIE17_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE3_FixRange".format(crate,slot),
	"get HF{0}-{1}-iBot_UniqueID".format(crate,slot),
	"get HF{0}-{1}-B_JTAG_Select_FPGA".format(crate,slot),
	"get HF{0}-{1}-QIE17_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE3_IdcBias".format(crate,slot),
	"get HF{0}-{1}-iBot_WTE_count".format(crate,slot),
	"get HF{0}-{1}-B_ONES".format(crate,slot),
	"get HF{0}-{1}-QIE17_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE3_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-iBot_ZerosRegister".format(crate,slot),
	"get HF{0}-{1}-B_ONESZEROES".format(crate,slot),
	"get HF{0}-{1}-QIE17_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE3_Lvds".format(crate,slot),
	"get HF{0}-{1}-iBot_fifo_data_1".format(crate,slot),
	"get HF{0}-{1}-B_PulserA_PulsePattern".format(crate,slot),
	"get HF{0}-{1}-QIE18_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE3_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-iBot_fifo_data_2".format(crate,slot),
	"get HF{0}-{1}-B_PulserA_TriggerDelay".format(crate,slot),
	"get HF{0}-{1}-QIE18_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE3_RangeSet".format(crate,slot),
	"get HF{0}-{1}-iBot_fifo_data_3".format(crate,slot),
	"get HF{0}-{1}-B_PulserA_TriggerSelect".format(crate,slot),
	"get HF{0}-{1}-QIE18_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE3_TGain".format(crate,slot),
	"get HF{0}-{1}-iBot_scratch".format(crate,slot),
	"get HF{0}-{1}-B_PulserB_PulsePattern".format(crate,slot),
	"get HF{0}-{1}-QIE18_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE3_TimingIref".format(crate,slot),
	"get HF{0}-{1}-iTop_AddrToSERDES".format(crate,slot),
	"get HF{0}-{1}-B_PulserB_TriggerDelay".format(crate,slot),
	"get HF{0}-{1}-QIE18_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE3_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-iTop_CapIdErrLink1_count".format(crate,slot),
	"get HF{0}-{1}-B_PulserB_TriggerSelect".format(crate,slot),
	"get HF{0}-{1}-QIE18_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE3_Trim".format(crate,slot),
	"get HF{0}-{1}-iTop_CapIdErrLink2_count".format(crate,slot),
	"get HF{0}-{1}-B_RESQIECOUNTER".format(crate,slot),
	"get HF{0}-{1}-QIE18_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE4_CalMode".format(crate,slot),
	"get HF{0}-{1}-iTop_CapIdErrLink3_count".format(crate,slot),
	"get HF{0}-{1}-B_SCRATCH".format(crate,slot),
	"get HF{0}-{1}-QIE18_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE4_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-iTop_Clk_count".format(crate,slot),
	"get HF{0}-{1}-B_SHT1_ident".format(crate,slot),
	"get HF{0}-{1}-QIE18_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE4_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-iTop_CntrReg_CImode".format(crate,slot),
	"get HF{0}-{1}-B_SHT1_rh_f".format(crate,slot),
	"get HF{0}-{1}-QIE18_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE4_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-iTop_CtrlToSERDES_i2c_go".format(crate,slot),
	"get HF{0}-{1}-B_SHT1_temp_f".format(crate,slot),
	"get HF{0}-{1}-QIE18_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE4_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-iTop_CtrlToSERDES_i2c_write".format(crate,slot),
	"get HF{0}-{1}-B_SHT1_user".format(crate,slot),
	"get HF{0}-{1}-QIE18_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE4_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-iTop_DataFromSERDES".format(crate,slot),
	"get HF{0}-{1}-B_SHT2_ident".format(crate,slot),
	"get HF{0}-{1}-QIE18_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE4_DiscOn".format(crate,slot),
	"get HF{0}-{1}-iTop_DataToSERDES".format(crate,slot),
	"get HF{0}-{1}-B_SHT2_rh_f".format(crate,slot),
	"get HF{0}-{1}-QIE18_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE4_FixRange".format(crate,slot),
	"get HF{0}-{1}-iTop_FPGA_MAJOR_VERSION".format(crate,slot),
	"get HF{0}-{1}-B_SHT2_temp_f".format(crate,slot),
	"get HF{0}-{1}-QIE18_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE4_IdcBias".format(crate,slot),
	"get HF{0}-{1}-iTop_FPGA_MINOR_VERSION".format(crate,slot),
	"get HF{0}-{1}-B_SHT2_user".format(crate,slot),
	"get HF{0}-{1}-QIE18_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE4_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-iTop_FPGA_TopOrBottom".format(crate,slot),
	"get HF{0}-{1}-B_Temp_userread".format(crate,slot),
	"get HF{0}-{1}-QIE18_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE4_Lvds".format(crate,slot),
	"get HF{0}-{1}-iTop_LinkTestMode".format(crate,slot),
	"get HF{0}-{1}-B_Thermometer".format(crate,slot),
	"get HF{0}-{1}-QIE19_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE4_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-B_Top_TRST_N".format(crate,slot),
	"get HF{0}-{1}-QIE19_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE4_RangeSet".format(crate,slot),
	"get HF{0}-{1}-iTop_LinkTestPattern".format(crate,slot),
	"get HF{0}-{1}-B_WTECOUNTER".format(crate,slot),
	"get HF{0}-{1}-QIE19_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE4_TGain".format(crate,slot),
	"get HF{0}-{1}-iTop_OnesRegister".format(crate,slot),
	"get HF{0}-{1}-B_ZEROES".format(crate,slot),
	"get HF{0}-{1}-QIE19_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE4_TimingIref".format(crate,slot),
	"get HF{0}-{1}-iTop_RST_QIE_count".format(crate,slot),
	"get HF{0}-{1}-Control".format(crate,slot),
	"get HF{0}-{1}-QIE19_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE4_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-iTop_Spy96bits".format(crate,slot),
	"get HF{0}-{1}-QIE19_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE4_Trim".format(crate,slot),
	"get HF{0}-{1}-iTop_StatFromSERDES_busy".format(crate,slot),
	"get HF{0}-{1}-Input_BytesA".format(crate,slot),
	"get HF{0}-{1}-QIE19_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE5_CalMode".format(crate,slot),
	"get HF{0}-{1}-iTop_StatFromSERDES_i2c_counter".format(crate,slot),
	"get HF{0}-{1}-Input_BytesBA".format(crate,slot),
	"get HF{0}-{1}-QIE19_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE5_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-iTop_StatusReg_PLL320MHzLock".format(crate,slot),
	"get HF{0}-{1}-Input_BytesBB".format(crate,slot),
	"get HF{0}-{1}-QIE19_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE5_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-iTop_StatusReg_QieDLLNoLock".format(crate,slot),
	"get HF{0}-{1}-QIE19_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE5_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-iTop_UniqueID".format(crate,slot),
	"get HF{0}-{1}-Output_Bytes".format(crate,slot),
	"get HF{0}-{1}-QIE19_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE5_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-iTop_WTE_count".format(crate,slot),
	"get HF{0}-{1}-QIE10_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE19_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE5_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-iTop_ZerosRegister".format(crate,slot),
	"get HF{0}-{1}-QIE10_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE19_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE5_DiscOn".format(crate,slot),
	"get HF{0}-{1}-iTop_fifo_data_1".format(crate,slot),
	"get HF{0}-{1}-QIE10_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE19_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE5_FixRange".format(crate,slot),
	"get HF{0}-{1}-iTop_fifo_data_2".format(crate,slot),
	"get HF{0}-{1}-QIE10_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE19_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE5_IdcBias".format(crate,slot),
	"get HF{0}-{1}-iTop_fifo_data_3".format(crate,slot),
	"get HF{0}-{1}-QIE10_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE19_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE5_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-iTop_scratch".format(crate,slot),
	"get HF{0}-{1}-QIE10_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE19_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE5_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE10_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE1_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE5_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-Bias_Current".format(crate,slot),
	"get HF{0}-{1}-QIE10_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE1_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE5_RangeSet".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-Bias_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE10_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE1_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE5_TGain".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-DIS_ST".format(crate,slot),
	"get HF{0}-{1}-QIE10_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE1_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE5_TimingIref".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-ENA".format(crate,slot),
	"get HF{0}-{1}-QIE10_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE1_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE5_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-EN_A".format(crate,slot),
	"get HF{0}-{1}-QIE10_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE1_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE5_Trim".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-EN_B".format(crate,slot),
	"get HF{0}-{1}-QIE10_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE1_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE6_CalMode".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-EN_EMA".format(crate,slot),
	"get HF{0}-{1}-QIE10_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE1_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE6_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-EN_EMB".format(crate,slot),
	"get HF{0}-{1}-QIE10_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE1_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE6_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-EXTCON".format(crate,slot),
	"get HF{0}-{1}-QIE10_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE1_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE6_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-MOD".format(crate,slot),
	"get HF{0}-{1}-QIE10_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE1_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE6_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-Modulation_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE11_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE1_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE6_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-PREDRV".format(crate,slot),
	"get HF{0}-{1}-QIE11_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE1_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE6_DiscOn".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-PREHF".format(crate,slot),
	"get HF{0}-{1}-QIE11_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE1_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE6_FixRange".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-PREHR".format(crate,slot),
	"get HF{0}-{1}-QIE11_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE1_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE6_IdcBias".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-PREW".format(crate,slot),
	"get HF{0}-{1}-QIE11_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE1_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE6_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-PRE_F".format(crate,slot),
	"get HF{0}-{1}-QIE11_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE1_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE6_Lvds".format(crate,slot),
	"get HF{0}-{1}-vttxBot1-PRE_R".format(crate,slot),
	"get HF{0}-{1}-QIE11_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE20_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE6_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-Bias_Current".format(crate,slot),
	"get HF{0}-{1}-QIE11_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE20_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE6_RangeSet".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-Bias_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE11_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE20_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE6_TGain".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-DIS_ST".format(crate,slot),
	"get HF{0}-{1}-QIE11_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE20_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE6_TimingIref".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-ENA".format(crate,slot),
	"get HF{0}-{1}-QIE11_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE20_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE6_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-EN_A".format(crate,slot),
	"get HF{0}-{1}-QIE11_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE20_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE6_Trim".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-EN_B".format(crate,slot),
	"get HF{0}-{1}-QIE11_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE20_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE7_CalMode".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-EN_EMA".format(crate,slot),
	"get HF{0}-{1}-QIE11_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE20_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE7_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-EN_EMB".format(crate,slot),
	"get HF{0}-{1}-QIE11_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE20_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE7_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-EXTCON".format(crate,slot),
	"get HF{0}-{1}-QIE11_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE20_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE7_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-MOD".format(crate,slot),
	"get HF{0}-{1}-QIE11_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE20_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE7_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-Modulation_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE12_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE20_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE7_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-PREDRV".format(crate,slot),
	"get HF{0}-{1}-QIE12_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE20_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE7_DiscOn".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-PREHF".format(crate,slot),
	"get HF{0}-{1}-QIE12_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE20_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE7_FixRange".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-PREHR".format(crate,slot),
	"get HF{0}-{1}-QIE12_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE20_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE7_IdcBias".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-PREW".format(crate,slot),
	"get HF{0}-{1}-QIE12_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE20_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE7_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-PRE_F".format(crate,slot),
	"get HF{0}-{1}-QIE12_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE20_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE7_Lvds".format(crate,slot),
	"get HF{0}-{1}-vttxBot2-PRE_R".format(crate,slot),
	"get HF{0}-{1}-QIE12_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE21_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE7_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-Bias_Current".format(crate,slot),
	"get HF{0}-{1}-QIE12_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE21_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE7_RangeSet".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-Bias_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE12_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE21_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE7_TGain".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-DIS_ST".format(crate,slot),
	"get HF{0}-{1}-QIE12_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE21_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE7_TimingIref".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-ENA".format(crate,slot),
	"get HF{0}-{1}-QIE12_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE21_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE7_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-EN_A".format(crate,slot),
	"get HF{0}-{1}-QIE12_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE21_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE7_Trim".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-EN_B".format(crate,slot),
	"get HF{0}-{1}-QIE12_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE21_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE8_CalMode".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-EN_EMA".format(crate,slot),
	"get HF{0}-{1}-QIE12_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE21_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE8_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-EN_EMB".format(crate,slot),
	"get HF{0}-{1}-QIE12_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE21_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE8_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-EXTCON".format(crate,slot),
	"get HF{0}-{1}-QIE12_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE21_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE8_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-MOD".format(crate,slot),
	"get HF{0}-{1}-QIE12_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE21_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE8_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-Modulation_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE13_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE21_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE8_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-PREDRV".format(crate,slot),
	"get HF{0}-{1}-QIE13_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE21_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE8_DiscOn".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-PREHF".format(crate,slot),
	"get HF{0}-{1}-QIE13_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE21_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE8_FixRange".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-PREHR".format(crate,slot),
	"get HF{0}-{1}-QIE13_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE21_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE8_IdcBias".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-PREW".format(crate,slot),
	"get HF{0}-{1}-QIE13_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE21_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE8_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-PRE_F".format(crate,slot),
	"get HF{0}-{1}-QIE13_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE21_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE8_Lvds".format(crate,slot),
	"get HF{0}-{1}-vttxBot3-PRE_R".format(crate,slot),
	"get HF{0}-{1}-QIE13_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE22_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE8_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-Bias_Current".format(crate,slot),
	"get HF{0}-{1}-QIE13_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE22_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE8_RangeSet".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-Bias_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE13_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE22_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE8_TGain".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-DIS_ST".format(crate,slot),
	"get HF{0}-{1}-QIE13_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE22_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE8_TimingIref".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-ENA".format(crate,slot),
	"get HF{0}-{1}-QIE13_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE22_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE8_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-EN_A".format(crate,slot),
	"get HF{0}-{1}-QIE13_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE22_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE8_Trim".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-EN_B".format(crate,slot),
	"get HF{0}-{1}-QIE13_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE22_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE9_CalMode".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-EN_EMA".format(crate,slot),
	"get HF{0}-{1}-QIE13_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE22_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE9_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-EN_EMB".format(crate,slot),
	"get HF{0}-{1}-QIE13_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE22_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE9_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-EXTCON".format(crate,slot),
	"get HF{0}-{1}-QIE13_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE22_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE9_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-MOD".format(crate,slot),
	"get HF{0}-{1}-QIE13_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE22_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE9_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-Modulation_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE14_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE22_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE9_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-PREDRV".format(crate,slot),
	"get HF{0}-{1}-QIE14_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE22_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE9_DiscOn".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-PREHF".format(crate,slot),
	"get HF{0}-{1}-QIE14_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE22_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE9_FixRange".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-PREHR".format(crate,slot),
	"get HF{0}-{1}-QIE14_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE22_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE9_IdcBias".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-PREW".format(crate,slot),
	"get HF{0}-{1}-QIE14_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE22_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE9_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-PRE_F".format(crate,slot),
	"get HF{0}-{1}-QIE14_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE22_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE9_Lvds".format(crate,slot),
	"get HF{0}-{1}-vttxTop1-PRE_R".format(crate,slot),
	"get HF{0}-{1}-QIE14_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE23_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE9_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-Bias_Current".format(crate,slot),
	"get HF{0}-{1}-QIE14_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE23_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE9_RangeSet".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-Bias_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE14_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE23_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE9_TGain".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-DIS_ST".format(crate,slot),
	"get HF{0}-{1}-QIE14_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE23_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE9_TimingIref".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-ENA".format(crate,slot),
	"get HF{0}-{1}-QIE14_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE23_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE9_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-EN_A".format(crate,slot),
	"get HF{0}-{1}-QIE14_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE23_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE9_Trim".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-EN_B".format(crate,slot),
	"get HF{0}-{1}-QIE14_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE23_DiscOn".format(crate,slot),
	"get HF{0}-{1}-Qie10_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-EN_EMA".format(crate,slot),
	"get HF{0}-{1}-QIE14_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE23_FixRange".format(crate,slot),
	"get HF{0}-{1}-Qie11_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-EN_EMB".format(crate,slot),
	"get HF{0}-{1}-QIE14_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE23_IdcBias".format(crate,slot),
	"get HF{0}-{1}-Qie12_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-EXTCON".format(crate,slot),
	"get HF{0}-{1}-QIE14_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE23_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-Qie13_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-MOD".format(crate,slot),
	"get HF{0}-{1}-QIE14_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE23_Lvds".format(crate,slot),
	"get HF{0}-{1}-Qie14_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-Modulation_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE15_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE23_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-Qie15_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-PREDRV".format(crate,slot),
	"get HF{0}-{1}-QIE15_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE23_RangeSet".format(crate,slot),
	"get HF{0}-{1}-Qie16_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-PREHF".format(crate,slot),
	"get HF{0}-{1}-QIE15_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE23_TGain".format(crate,slot),
	"get HF{0}-{1}-Qie17_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-PREHR".format(crate,slot),
	"get HF{0}-{1}-QIE15_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE23_TimingIref".format(crate,slot),
	"get HF{0}-{1}-Qie18_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-PREW".format(crate,slot),
	"get HF{0}-{1}-QIE15_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE23_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-Qie19_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-PRE_F".format(crate,slot),
	"get HF{0}-{1}-QIE15_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE23_Trim".format(crate,slot),
	"get HF{0}-{1}-Qie1_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop2-PRE_R".format(crate,slot),
	"get HF{0}-{1}-QIE15_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE24_CalMode".format(crate,slot),
	"get HF{0}-{1}-Qie20_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-Bias_Current".format(crate,slot),
	"get HF{0}-{1}-QIE15_FixRange".format(crate,slot),
	"get HF{0}-{1}-QIE24_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-Qie21_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-Bias_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE15_IdcBias".format(crate,slot),
	"get HF{0}-{1}-QIE24_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-Qie22_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-DIS_ST".format(crate,slot),
	"get HF{0}-{1}-QIE15_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-QIE24_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-Qie23_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-ENA".format(crate,slot),
	"get HF{0}-{1}-QIE15_Lvds".format(crate,slot),
	"get HF{0}-{1}-QIE24_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-Qie24_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-EN_A".format(crate,slot),
	"get HF{0}-{1}-QIE15_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-QIE24_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-Qie2_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-EN_B".format(crate,slot),
	"get HF{0}-{1}-QIE15_RangeSet".format(crate,slot),
	"get HF{0}-{1}-QIE24_DiscOn".format(crate,slot),
	"get HF{0}-{1}-Qie3_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-EN_EMA".format(crate,slot),
	"get HF{0}-{1}-QIE15_TGain".format(crate,slot),
	"get HF{0}-{1}-QIE24_FixRange".format(crate,slot),
	"get HF{0}-{1}-Qie4_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-EN_EMB".format(crate,slot),
	"get HF{0}-{1}-QIE15_TimingIref".format(crate,slot),
	"get HF{0}-{1}-QIE24_IdcBias".format(crate,slot),
	"get HF{0}-{1}-Qie5_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-EXTCON".format(crate,slot),
	"get HF{0}-{1}-QIE15_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-QIE24_IsetpBias".format(crate,slot),
	"get HF{0}-{1}-Qie6_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-MOD".format(crate,slot),
	"get HF{0}-{1}-QIE15_Trim".format(crate,slot),
	"get HF{0}-{1}-QIE24_Lvds".format(crate,slot),
	"get HF{0}-{1}-Qie7_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-Modulation_Mask".format(crate,slot),
	"get HF{0}-{1}-QIE16_CalMode".format(crate,slot),
	"get HF{0}-{1}-QIE24_PedestalDAC".format(crate,slot),
	"get HF{0}-{1}-Qie8_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-PREDRV".format(crate,slot),
	"get HF{0}-{1}-QIE16_CapID0pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE24_RangeSet".format(crate,slot),
	"get HF{0}-{1}-Qie9_ck_ph".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-PREHF".format(crate,slot),
	"get HF{0}-{1}-QIE16_CapID1pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE24_TGain".format(crate,slot),
	"get HF{0}-{1}-Status".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-PREHR".format(crate,slot),
	"get HF{0}-{1}-QIE16_CapID2pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE24_TimingIref".format(crate,slot),
	"get HF{0}-{1}-UniqueID".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-PREW".format(crate,slot),
	"get HF{0}-{1}-QIE16_CapID3pedestal".format(crate,slot),
	"get HF{0}-{1}-QIE24_TimingThresholdDAC".format(crate,slot),
	"get HF{0}-{1}-UniqueIDn".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-PRE_F".format(crate,slot),
	"get HF{0}-{1}-QIE16_ChargeInjectDAC".format(crate,slot),
	"get HF{0}-{1}-QIE24_Trim".format(crate,slot),
	"get HF{0}-{1}-bkp_pwr_bad".format(crate,slot),
	"get HF{0}-{1}-vttxTop3-PRE_R".format(crate,slot),
	"get HF{0}-{1}-QIE16_DiscOn".format(crate,slot),
	"get HF{0}-{1}-QIE2_CalMode".format(crate,slot),
	"get HF{0}-{1}-bkp_temp_f".format(crate,slot),
	"get HF{0}-adc50_control".format(crate),
	"get HF{0}-adc50temp_f".format(crate),
	"get HF{0}-adc52_t".format(crate),
	"get HF{0}-adc54_f".format(crate),
	"get HF{0}-adc56_control".format(crate),
	"get HF{0}-adc56temp_f".format(crate),
	"get HF{0}-adc58_t".format(crate),
	"get HF{0}-adc50_f".format(crate),
	"get HF{0}-adc52_control".format(crate),
	"get HF{0}-adc52temp_f".format(crate),
	"get HF{0}-adc54_t".format(crate),
	"get HF{0}-adc56_f".format(crate),
	"get HF{0}-adc58_control".format(crate),
	"get HF{0}-adc58temp_f".format(crate),
	"get HF{0}-adc50_t".format(crate),
	"get HF{0}-adc52_f".format(crate),
	"get HF{0}-adc54_control".format(crate),
	"get HF{0}-adc54temp_f".format(crate),
	"get HF{0}-adc56_t".format(crate),
	"get HF{0}-adc58_f".format(crate),
	"get HF{0}-adc5Atemp_f".format(crate),
	"get HF{0}-bitslip_ctrl_slide_enable".format(crate),
	"get HF{0}-bkp_pwr_bad".format(crate),
	"get HF{0}-bkpregs_ngccm_bkp_reset_out".format(crate),
	"get HF{0}-bkpregs_ngccm_rev_id".format(crate),
	"get HF{0}-bitslip_ctrl_slide_manual".format(crate),
	"get HF{0}-bkpregs_bkp_pwr_good".format(crate),
	"get HF{0}-bkpregs_ngccm_bkp_reset_qie_out".format(crate),
	"get HF{0}-bitslip_ctrl_slide_nbr".format(crate),
	"get HF{0}-bkpregs_bkp_spare".format(crate),
	"get HF{0}-bkpregs_ngccm_bkp_wte_out".format(crate),
	"get HF{0}-bitslip_ctrl_slide_run".format(crate),
	"get HF{0}-bkpregs_ngccm_bkp_pwr_enable_out".format(crate),
	"get HF{0}-bkpregs_ngccm_neigh_rev_id".format(crate),
	"get HF{0}-BERCLK".format(crate),
	"get HF{0}-directaccess".format(crate),
	"get HF{0}-gbt_status_aligned".format(crate),
	"get HF{0}-gbt_status_bitslips".format(crate),
	"get HF{0}-heartbeat_enabled".format(crate),
	"get HF{0}-jtag_data".format(crate),
	"get HF{0}-jtag_reg".format(crate),
	"get HF{0}-jtag_sel".format(crate),
	"get HF{0}-link_ctrl_gbt_rx_rst".format(crate),
	"get HF{0}-link_ctrl_gtx_loopback".format(crate),
	"get HF{0}-link_ctrl_gtx_rx_reset".format(crate),
	"get HF{0}-link_ctrl_gtx_tx_pwrdown".format(crate),
	"get HF{0}-link_ctrl_gtx_tx_sync_rst".format(crate),
	"get HF{0}-link_ctrl_gbt_tx_rst".format(crate),
	"get HF{0}-link_ctrl_gtx_rx_pwrdown".format(crate),
	"get HF{0}-link_ctrl_gtx_rx_sync_rst".format(crate),
	"get HF{0}-link_ctrl_gtx_tx_reset".format(crate),
	"get HF{0}-m-Control".format(crate),
	"get HF{0}-m-vtrx-EN_EMB".format(crate),
	"get HF{0}-m-vtrx-PRE_F".format(crate),
	"get HF{0}-mezz_SERDES_LANE_SEL".format(crate),
	"get HF{0}-m-vtrx-Bias_Current".format(crate),
	"get HF{0}-m-vtrx-EXTCON".format(crate),
	"get HF{0}-m-vtrx-PRE_R".format(crate),
	"get HF{0}-mezz_SERDES_REFCLK_SEL".format(crate),
	"get HF{0}-m-Input_BytesA".format(crate),
	"get HF{0}-m-vtrx-Bias_Mask".format(crate),
	"get HF{0}-m-vtrx-MOD".format(crate),
	"get HF{0}-mezz_BoardID".format(crate),
	"get HF{0}-mezz_ZEROES".format(crate),
	"get HF{0}-m-Input_BytesBA".format(crate),
	"get HF{0}-m-vtrx-DIS_ST".format(crate),
	"get HF{0}-m-vtrx-Modulation_Mask".format(crate),
	"get HF{0}-mezz_ERROR_COUNT".format(crate),
	"get HF{0}-mezz_error_count_reset".format(crate),
	"get HF{0}-m-Input_BytesBB".format(crate),
	"get HF{0}-m-vtrx-ENA".format(crate),
	"get HF{0}-m-vtrx-PREDRV".format(crate),
	"get HF{0}-mezz_FPGA_MAJOR_VERSION".format(crate),
	"get HF{0}-mezz_reg3".format(crate),
	"get HF{0}-m-vtrx-EN_A".format(crate),
	"get HF{0}-m-vtrx-PREHF".format(crate),
	"get HF{0}-mezz_FPGA_MINOR_VERSION".format(crate),
	"get HF{0}-mezz_scratch".format(crate),
	"get HF{0}-m-Output_Bytes".format(crate),
	"get HF{0}-m-vtrx-EN_B".format(crate),
	"get HF{0}-m-vtrx-PREHR".format(crate),
	"get HF{0}-mezz_ONES".format(crate),
	"get HF{0}-mezz_slowSig1".format(crate),
	"get HF{0}-m-Status".format(crate),
	"get HF{0}-m-vtrx-EN_EMA".format(crate),
	"get HF{0}-m-vtrx-PREW".format(crate),
	"get HF{0}-mezz_RX_BITSLIP_NUMBER".format(crate),
	"get HF{0}-mezz_slowSig2".format(crate),
	"get HF{0}-n-Control".format(crate),
	"get HF{0}-n-Input_BytesA".format(crate),
	"get HF{0}-n-Input_BytesBB".format(crate),
	"get HF{0}-n-Output_Bytes".format(crate),
	"get HF{0}-n-Input_BytesBA".format(crate),
	"get HF{0}-n-Status".format(crate),
	"get HF{0}-power".format(crate),
	"get HF{0}-pulser-daccontrol_ToggleFunctionEnable".format(crate),
	"get HF{0}-pulser-delay-cr3_delay".format(crate),
	"get HF{0}-pulser-daccontrol_ChannelMonitorEnable".format(crate),
	"get HF{0}-pulser-delay-cr0_delay".format(crate),
	"get HF{0}-pulser-delay-cr3_enable".format(crate),
	"get HF{0}-pulser-daccontrol_CurrentBoostEnable".format(crate),
	"get HF{0}-pulser-delay-cr0_enable".format(crate),
	"get HF{0}-pulser-delay-cr4_delay".format(crate),
	"get HF{0}-pulser-daccontrol_InternalRefEnable".format(crate),
	"get HF{0}-pulser-delay-cr1_delay".format(crate),
	"get HF{0}-pulser-delay-cr4_enable".format(crate),
	"get HF{0}-pulser-daccontrol_PowerDownStatus".format(crate),
	"get HF{0}-pulser-delay-cr1_enable".format(crate),
	"get HF{0}-pulser-delay-gcr_IDLL".format(crate),
	"get HF{0}-pulser-daccontrol_RefSelect".format(crate),
	"get HF{0}-pulser-delay-cr2_delay".format(crate),
	"get HF{0}-pulser-delay-gcr_freq".format(crate),
	"get HF{0}-pulser-daccontrol_ThermalMonitorEnable".format(crate),
	"get HF{0}-pulser-delay-cr2_enable".format(crate),
	"get HF{0}-pwrenable".format(crate),
	"get HF{0}-qiereset".format(crate),
	"get HF{0}-reset".format(crate),
	"get HF{0}-RX_40MHZ".format(crate),
	"get HF{0}-RX_USRCLK_DIV2".format(crate),
	"get HF{0}-TX_40MHZ".format(crate),
	"get HF{0}-TX_USRCLK_DIV2".format(crate),
	"get HF{0}-vtrx_clk_rssi_f".format(crate),
	"get HF{0}-vtrx_rssi_f".format(crate),
	"get HF{0}-VIN_current_f".format(crate),
	"get HF{0}-VIN_voltage_f".format(crate),
	"get HF{0}-wte".format(crate),
	"get fec1-BC0_cnt",
	"get fec1-firmware_dd",
	"get fec1-gbt_phase_mon_reset",
	"get fec1-sfp1_status.TxFault",
	"get fec1-tclka_dr_en",
	"get fec1-v6_cpld",
	"get fec1-DbErr_cnt",
	"get fec1-firmware_mm",
	"get fec1-gtx_conf",
	"get fec1-sfp2_status.Mod_abs",
	"get fec1-tclkb_dr_en",
	"get fec1-xpoint_2x2_s1",
	"get fec1-EC0_cnt",
	"get fec1-firmware_ver_build",
	"get fec1-gtx_global_reset",
	"get fec1-sfp2_status.RxLOS",
	"get fec1-user_board_id",
	"get fec1-xpoint_2x2_s2",
	"get fec1-LHC_clk_freq",
	"get fec1-firmware_ver_major",
	"get fec1-icap_page",
	"get fec1-sfp2_status.TxFault",
	"get fec1-user_firmware_dd",
	"get fec1-xpoint_4x4_s1",
	"get fec1-SinErr_cnt",
	"get fec1-firmware_ver_minor",
	"get fec1-icap_trigg",
	"get fec1-sfp3_status.Mod_abs",
	"get fec1-user_firmware_mm",
	"get fec1-xpoint_4x4_s2",
	"get fec1-board_id",
	"get fec1-firmware_yy",
	"get fec1-pcie_clk_fsel",
	"get fec1-sfp3_status.RxLOS",
	"get fec1-user_firmware_yy",
	"get fec1-xpoint_4x4_s3",
	"get fec1-cdce_ctrl_sel",
	"get fec1-fmc1_presence",
	"get fec1-pcie_clk_mr",
	"get fec1-sfp3_status.TxFault",
	"get fec1-user_sys_id",
	"get fec1-xpoint_4x4_s4",
	"get fec1-cdce_lock",
	"get fec1-fmc2_presence",
	"get fec1-pcie_clk_oe",
	"get fec1-sfp4_status.Mod_abs",
	"get fec1-user_ver_build",
	"get fec1-cdce_powerup",
	"get fec1-fpga_program_b_trst",
	"get fec1-qie_reset_cnt",
	"get fec1-sfp4_status.RxLOS",
	"get fec1-user_ver_major",
	"get fec1-cdce_refsel",
	"get fec1-fpga_reset",
	"get fec1-sfp1_status.Mod_abs",
	"get fec1-sfp4_status.TxFault",
	"get fec1-user_ver_minor",
	"get fec1-cdce_sync",
	"get fec1-gbe_int",
	"get fec1-sfp1_status.RxLOS",
	"get fec1-sma_output",
	"get fec1-user_wb_regs",
	"get softf1",
	"get softf2u",
	"get softf3s",
	"get testsoft",
	"get testsoft32",
	"get testsoftread",
	"get HF{0}-1wA_config".format(crate),
	"get HF{0}-1wA_id".format(crate),
	"get HF{0}-1wA_user1".format(crate),
	"get HF{0}-1wB_config".format(crate),
	"get HF{0}-1wB_id".format(crate),
	"get HF{0}-1wB_user1".format(crate),
	"get HF{0}-1wA_f".format(crate),
	"get HF{0}-1wA_t".format(crate),
	"get HF{0}-1wA_user2".format(crate),
	"get HF{0}-1wB_f".format(crate),
	"get HF{0}-1wB_t".format(crate),
	"get HF{0}-1wB_user2".format(crate),
	"get HF{0}-tmr_errors".format(crate),
	"get HF{0}-tmr_errors2".format(crate)]
    return commands

# VARIABLES:
# /VARIABLES

if __name__ == "__main__":
	print "Hang on."
	print 'What you just ran is "ngccm.py". This is a module, not a script. See the documentation ("readme.md") for more information.'
