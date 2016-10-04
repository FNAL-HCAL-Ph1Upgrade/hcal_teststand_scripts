####################################################################
# Type: MODULE                                                     #
#                                                                  #
# Description: ?                                                   #
#                                                                  #
# Notes: Keep this module compatible with Python 2.4. That means   #
# don't use "format"!                                              #
####################################################################

from re import search, split
#from hcal_teststand import amc13		# Not compatible...

# FUNCTIONS:
def parse_ts_configuration(f="teststands.txt"):		# This function must be compatible with Python 2.4. (Don't use "format".)
	variables = {
		"name": "s",
		"mch_ips": "sl",
		"amc13_ips": "sL",
		"ngfec_port": "i", 
		"uhtr_settings": "sl",
		"control_hub": "s",
		"be_crates": "il",
		"uhtr_slots": "iL",
		"glib_slots": "iL",
		"fe_crates": "il",
		"qie_slots": "iL",
		"qie_cards_per_slot": "iM",
		"qies_per_card": "i"
	}
	teststand_info = {}
	raw = ""
	if ("/" in f):
		raw = open(f).read()
	else:
		raw = open("configuration/" + f).read()
	teststands_raw = split("\n\s*%%", raw)
	for teststand_raw in teststands_raw:
		lines = teststand_raw.strip().split("\n")
		ts_name = ""
		for line in [l for l in lines if l]:
			match_var_val = search("^\s*(\w+)\s*=\s*([^#]+)", line)
			if match_var_val:
				variable = match_var_val.group(1)
				value = match_var_val.group(2).strip()
				if variable in variables.keys():
					if (variable == "name"):
						ts_name = value
						teststand_info[ts_name] = {}
					elif ts_name:
						teststand_info[ts_name][variable] = parse_config_var(raw=value, var_type=variables[variable])
					else:
						print "ERROR (install.parse_ts_configuration): The ts name isn't at the top of the variable list for at least one of the teststands! This is confusing to me. See the config below:"
						print teststand_raw
						return False
	return teststand_info

def parse_config_var(raw=None, var_type="s"):
	# Parse:
	if "l" not in var_type.lower() and "m" not in var_type.lower():
		if "s" in var_type:
			return str(raw)
		elif "i" in var_type:
			return int(raw)
	else:
		if "l" in var_type:
				if "s" in var_type:
					return [str(i).strip() for i in raw.split(",")]
				elif "i" in var_type:
					return [int(i) for i in raw.split(",")]
		elif "L" in var_type:
			lists = raw.split(";")
			result = []
			for l in lists:
				if l:
					if "s" in var_type:
						result.append([str(i).strip() for i in l.split(",")])
					elif "i" in var_type:
						result.append([int(i) for i in l.split(",")])
				else:
					result.append([])
                        return result
                elif "M" in var_type:
			lists = raw.split(";")
			result = []
			for l in lists:
				if l:
                                        sublists = l.split("|")
                                        subresult = []
                                        for m in sublists:
                                                if m:
                                                        if "s" in var_type:
                                                                subresult.append([str(i).strip() for i in m.split(",")])
                                                        elif "i" in var_type:
                                                                subresult.append([int(i) for i in m.split(",")])
                                                else:
                                                        subresult.append([])
                                        result.append(subresult)
				else:
					result.append([])                        
		#	# Let a semicolon be at the end of the last list without adding an empty list:
		#	if not result[-1]:
		#		del result[-1]
			return result

def make_amc13_configs(f="teststands.txt"):		# Write configuration files for AMC13.
	names = []
	ts_info = parse_ts_configuration(f=f)
	for name, info in ts_info.iteritems():
		if "control_hub" in info:
			ch = info["control_hub"]
		else:
			ch = "localhost"
		if info:
			string = '<?xml version="1.0" encoding="UTF-8"?>\n<connections>\n'
			amc13s = [ips for ips in info["amc13_ips"] if ips]
			for i, ips in enumerate(amc13s):
#				string += '\t<!-- AMC13 with SN = ' + str(amc13.sn_from_ip(ips[0])) + ' -->\n'
				if len(amc13s) > 1:
					prefix = str(i) + "."
				else:
					prefix = ""
				string += '\t<connection id="' + prefix + 'T1" uri="chtcp-2.0://' + ch + ':10203?target=' + ips[0] + ':50001" address_table="file:///opt/cactus/etc/amc13/AMC13XG_T1.xml" />\n'
				string += '\t<connection id="' + prefix + 'T2" uri="chtcp-2.0://' + ch + ':10203?target=' + ips[1] + ':50001" address_table="file:///opt/cactus/etc/amc13/AMC13XG_T2.xml" />\n'
			string += '</connections>'
			try:
				out = open("configuration/amc13_" + name + "_config.xml", "w")
				out.write(string)
				names.append(name)
			except Exception, ex:		# This notation is compatible with older versions of Python. It's good to keep this compatible so that the script can be run from the B904 head node.
				print ex
		else:
			print "ERROR: Didn't make an AMC13 configuration file for " + name + "."
	return names

def make_setup_scripts(f):		# Write the set up scripts.
	names = []
	ts_info = parse_ts_configuration(f)
	for name, info in ts_info.iteritems():
		string = ""
		if info:
			if name == "bhm":
				string = '''
source /nfshome0/hcalsw/bin/env.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/ngccm/lib
export PATH=$PATH:/opt/ngccm/bin
				'''.strip()
			elif "904" in name:
				string = '''
source /nfshome0/hcalsw/bin/env.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/nfshome0/hcalpro/ngFEC
export PATH=$PATH:/nfshome0/hcalpro/ngFEC
				'''.strip()
			elif name == "157":
				string = '''
source /home/daq/environment.sh
				'''.strip()
			elif name == "fnal":
				string = '''
source /home/hcalpro/tote/env.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/hcalpro/ngFEC
export PATH=$PATH:/home/hcalpro/ngFEC
				'''.strip()
			try:
				out = open("configuration/setup_" + name + ".sh", "w")
				out.write(string)
				names.append(name)
			except Exception, ex:
				print ex
		else:
			print "[!!] ERROR: Didn't make an setup script for " + name + "."
	print "[OK] Installation successful."
	return names
# /FUNCTIONS
