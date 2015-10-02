####################################################################
# Type: SCRIPT                                                     #
#                                                                  #
# Description: This is a script skeleton.                          #
####################################################################

from hcal_teststand import *
from hcal_teststand.hcal_teststand import teststand
import sys

# CLASSES:
# /CLASSES

# FUNCTIONS:
# /FUNCTIONS
def my_log_temp(ts):
	log = []
	log.append("%% TEMPERATURES\n")
	cmds = [
		"get HE1-1-temperature_f", 
		"get HE1-2-temperature_f"
		]
	output = ngccm.send_commands_parsed(ts, cmds)["output"]
	log.extend([ "{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	return "".join(log)

def my_log_power(ts):
	log = []
	log.append("%% POWER\n")
	cmds = [
		"get HE1-VIN_voltage_f", 
		"get HE1-VIN_current_f"
		]
	output = ngccm.send_commands_parsed(ts, cmds)["output"]
	log.extend([ "{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
	return "".join(log)

def get_qie_shift_reg(ts , crate , slot , qie_list = range(1,5) ):
	
	qie_settings = [ #"CalMode", 
			 "CapID0pedestal", 
			 "CapID1pedestal", 
			 "CapID2pedestal", 
			 "CapID3pedestal", 
			 "ChargeInjectDAC", 
			 "DiscOn", 
			 "FixRange",
			 "Gsel",
			 #"IdcBias", 
			 #"IsetpBias", 
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
	#[ "get HE{0}-{1}-QIE{2}_{3}".format(crate,slot,qie,setting) for setting in qie_settings for qie in qie_list ]
	for qie in qie_list :
		#print qie
		for setting in qie_settings : 
			commands.append("get HE{0}-{1}-QIE{2}_{3}".format(crate,slot,qie,setting))
	
	ngccm_output = ngccm.send_commands_parsed(ts , commands)
	
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
	
	print_table.print_table(table_)



# MAIN:
if __name__ == "__main__":
	name = ""
	if len(sys.argv) == 1:
		name = "904"
	elif len(sys.argv) == 2:
		name = sys.argv[1]
	else:
		name = "904"
	ts = teststand(name)		# Initialize a teststand object. This object stores the teststand configuration and has a number of useful methods.
	print "\nYou've just run a script that's a skeleton for making your own script."
	# Print out some information about the teststand:
	print ">> The teststand you're using is named {0}.".format(ts.name)
	print ">> The crate and QIE card organization for the teststand is below:\n{0}".format(ts.fe)
# /MAIN


# FUNCTIONS:

	print "QIE slots: ", ts.qie_slots

	#print ">> Test logging"
	#print my_log_temp(ts)
	#print my_log_power(ts)
	#print get_qie_shift_reg(ts , 1 , 1 , qie_list = range(1,5) )
