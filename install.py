####################################################################
# Type: SCRIPT                                                     #
#                                                                  #
# Description: This script installs the repository. It creates     #
# configuration files and set up scripts.                          #
#                                                                  #
# Notes: Keep this script compatible with Python 2.4.              #
####################################################################

from re import search, split

# FUNCTIONS:
def parse_ts_configuration(f="teststands.txt"):		# This function is a clone of the function of the same name in hcal_teststand but modified to be compatible with Python 2.4.
	# WHEN YOU EDIT THIS SCRIPT, MAKE SURE TO UPDATE hcal_teststand.py IF YOU NEED TO!
	variables = ["name", "fe_crates", "ngccm_port", "uhtr_ip_base", "uhtr_slots", "uhtr_settings", "glib_slot", "mch_ip", "amc13_ips", "qie_slots", "control_hub", "qie_cards_per_slot", "qies_per_card"]
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
		for variable in variables:
			for line in lines:
				if line:		# Skip empty lines. This isn't really necessary.
					if search("^\s*" + variable, line):		# Consider lines beginning with the variable name.
						if (variable == "name"):
							ts_name = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name] = {}
						elif (variable == "fe_crates"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = [int(i) for i in value.split(",")]
						elif (variable == "ngccm_port"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = int(value)
						elif (variable == "uhtr_ip_base"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = value.strip()
						elif (variable == "uhtr_slots"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = sorted([int(i) for i in value.split(",")])
						elif (variable == "uhtr_settings"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = [i for i in value.split(",")]
						elif (variable == "glib_slot"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = int(value)
						elif (variable == "mch_ip"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = value.strip()
						elif (variable == "amc13_ips"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = [i.strip() for i in value.split(",")]
						elif (variable == "qie_cards_per_slot"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = int(value.strip())
						elif (variable == "qies_per_card"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = int(value.strip())
						elif (variable == "qie_slots"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							crate_lists = value.split(";")
							teststand_info[ts_name][variable] = []
							for crate_list in crate_lists:
								if crate_list:
									teststand_info[ts_name][variable].append([int(i) for i in crate_list.split(",")])
								else:
									teststand_info[ts_name][variable].append([])
							# Let a semicolon be at the end of the last list without adding an empty list:
							if not teststand_info[ts_name][variable][-1]:
								del teststand_info[ts_name][variable][-1]
						elif (variable == "control_hub"):
							value = search(variable + "\s*=\s*([^#]+)", line).group(1).strip()
							teststand_info[ts_name][variable] = value.strip()
	return teststand_info

def make_amc13_configs(f="teststands.txt"):		# Write configuration files for AMC13.
	names = []
	ts_info = parse_ts_configuration(f=f)
	for name, info in ts_info.iteritems():
		if "control_hub" in info:
			ch = info["control_hub"]
		else:
			ch = "localhost"
		if info:
			string = '''
<?xml version="1.0" encoding="UTF-8"?>
<connections>
	<connection id="T1" uri="chtcp-2.0://''' + ch + ''':10203?target=''' + info["amc13_ips"][0] + ''':50001" address_table="file:///opt/cactus/etc/amc13/AMC13XG_T1.xml" />
	<connection id="T2" uri="chtcp-2.0://''' + ch + ''':10203?target=''' + info["amc13_ips"][1] + ''':50001" address_table="file:///opt/cactus/etc/amc13/AMC13XG_T2.xml" />
</connections>'''.strip()
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
			elif name == "904":
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
			print "ERROR: Didn't make an setup script for " + name + "."
	return names
# /FUNCTIONS

# MAIN:
if __name__ == "__main__":
	make_amc13_configs()
	make_setup_scripts("teststands.txt")
 # /MAIN
