from re import search, split
from subprocess import Popen, PIPE
import mch
import amc13
import glib
import uhtr
import ngccm
import qie
import json
import os

# CLASSES:
class teststand:
	# CONSTRUCTION (attribute assignment):
	def __init__(self, *args):
#		if ( (len(args) == 2) and isinstance(args[0], str) and isinstance(args[1], str) ):
		if ( (len(args) == 1) and isinstance(args[0], str) ):
			self.name = args[0]
			f = "teststands.txt"
			ts_info = {}
			try:
				# Exctract teststand info from the teststand configuration file:
				ts_info = parse_ts_configuration(f)[self.name]
#				print ts_info
				for key, value in ts_info.iteritems():
					setattr(self, key, value)
				# Assign a few other calculable attributes:
				self.uhtr_ips = []
				self.uhtr = {}
				for slot in self.uhtr_slots:
					ip = "{0}.{1}".format(self.uhtr_ip_base, slot*4)
					self.uhtr_ips.append(ip)
					self.uhtr[slot] = ip
				self.glib_ip = "192.168.1.{0}".format(160 + self.glib_slot)
				self.nqies = int(self.qie_cards_per_slot) * int(self.qies_per_card)
				self.fe = {}
				if len(self.fe_crates) <= len(self.qie_slots):
					for i in range(len(self.fe_crates)):
						self.fe[self.fe_crates[i]] = self.qie_slots[i]
			except Exception as ex:		# The above will fail if the teststand names doesn't appear in the configuration file.
				print "ERROR: Could not read the teststand information for {0} from the configuration file: {1}".format(self.name, f)
				print ">> {0}".format(ex)
		else:
			print "ERROR: You need to initialize a teststand object with a name (string) from the teststand configuration file (configuration/teststands.txt)."
	# /CONSTRUCTION
	
	# METHODS:
	def get_links(self, uhtr_slot=False):
		if uhtr_slot:
			return uhtr.get_links(self, ip)
		else:
			return uhtr.get_links_all(self)
	
	def get_info(self):		# Returns a dictionary of component information, namely versions.
		data = {}
		data["amc13"] = amc13.get_info(ts=self)
		data["glib"] = glib.get_info(self)
		data["uhtr"] = uhtr.get_info(self)
		data["ngccm"] = []
		data["qie"] = []
		for crate, slots in self.fe.iteritems():
			data["ngccm"].append(ngccm.get_info(self, crate))
			for slot in slots:
				data["qie"].append(qie.get_info(self, crate, slot))
		return data
	
	def get_temps(self):		# Returns a list of various temperatures around the teststand.
		temps = []
		for i, crate in enumerate(self.fe_crates):
			temps.append(get_temp(self, crate, i)["temp"])		# See the "get_temp" funtion above.
		return temps
	
	def get_data(self, uhtr_slot=12, i_link=0, n=300):
		return uhtr.get_data_parsed(self, uhtr_slot, n, i_link)
	
	def get_status(self):		# Sets up and checks that the teststand is working.
		return get_ts_status(self)
	
	def set_ped(self, crate=0, slot=0, i_qie=0, dac=6):
		qie.set_ped(self, crate, slot, i_qie, dac)
	
	def set_ped_all(self, n):
		for crate, slots in self.fe.iteritems():
			for slot in slots:
				qie.set_ped_all(self, crate, slot, n)
	
	def set_cal_mode_all(self, enable=False):
		for crate, slots in self.fe.iteritems():
			for slot in slots:
				qie.set_cal_mode_all(self, crate, slot, enable)
	
	def get_qie_map(self):
		qie_map = qie.get_map_slow(self)
		return qie_map
	
	def save_qie_map(self, f="", d="configuration/maps"):		# Saves the qie map to a file named f in directory d.
		if f:
			if f.split(".")[-1] != "json":
				f += ".json"
		else:
			f = "{0}_qie_map.json".format(self.name)
		if not os.path.exists(d):
			os.makedirs(d)
		qie_map = self.get_qie_map()		# A qie map is from QIE crate, slot, qie number to link number, IP, unique_id, etc. It's a list of dictionaries with 3tuples as the keys: (crate, slot, qie)
		
		qie_map_out = {}
		for qie in qie_map:
			qie_map_out["{0:02d}{1:02d}{2:02d}".format(qie["crate"], qie["slot"], qie["qie"])] = qie
		with open("{0}/{1}".format(d, f), "w") as out:
#			json.dump(qie_map_out, out)
			json.dump(qie_map, out)
	
	def read_qie_map(self, f="", d="configuration/maps"):
		if f:
			if f.split(".")[-1] != "json":
				f += ".json"
		else:
			f = "{0}_qie_map.json".format(self.name)
		
		path = d + "/" + f
		if os.path.exists(path):
			with open(path) as infile:
				qie_map = json.loads(infile.read())
		else:
			"ERROR: Could not find the qie_map at {0}".format(path)
			qie_map = []
		return qie_map
	
	def uhtr_from_qie(self, qie_id="", f="", d="configuration/maps"):
		result = {}
		qie_map = self.read_qie_map(f=f, d=d)
		if qie_id:
			uhtr_info = sorted(list(set([(qie["uhtr_slot"], qie["link"]) for qie in qie_map if qie["id"] == qie_id])))
		else:
			uhtr_info = sorted(list(set([(qie["uhtr_slot"], qie["link"]) for qie in qie_map])))
#		print uhtr_info
		for slot, link in uhtr_info:
			if slot in result:
				result[slot].append(link)
			else:
				result[slot] = [link]
		return result
	
	def crate_slot_from_qie(self, qie_id="", f="", d="configuration/maps"):
		qie_map = self.read_qie_map(f=f, d=d)
		if qie_id:
			info = sorted(list(set([(qie["crate"], qie["slot"]) for qie in qie_map if qie["id"] == qie_id])))
		else:
			info = sorted(list(set([(qie["crate"], qie["slot"]) for qie in qie_map])))
		if len(info) == 1:
			return info[0]
		else:
			print "WARNING (ts.crate_slot_from_qie): qie {0} maps to more than one crate, slot: {1}".format(qie_id, info)
			return info[0]
	
	def get_qies(self, unique_id, f="", d="configuration/maps"):
		return get_qies(self, unique_id, f=f, d=d)
	# /METHODS
	
	def __str__(self):		# This just defines what the object looks like when it's printed.
		if hasattr(self, "name"):
			return "<teststand object: {0}>".format(self.name)
		else:
			return "<empty teststand object>"
# /CLASSES

# FUNCTIONS:
def get_qies(ts, unique_id, f="", d="configuration/maps"):
	# Deal with QIE map location:
	if f:
		if f.split(".")[-1] != "json":
			f += ".json"
	else:
		f = "{0}_qie_map.json".format(ts.name)
	
	# Read the QIE map and construct qie objects:
	qie_map = ts.read_qie_map(f=f, d=d)
	qies = []
	for i_qie in [i_qie for i_qie in qie_map if i_qie["id"] == unique_id]:
		qies.append(qie.qie(
			ts=ts,
			unique_id=unique_id,
			crate=i_qie["crate"],
			slot=i_qie["slot"],
			n=i_qie["qie"],
			uhtr_slot=i_qie["uhtr_slot"],
			fiber=i_qie["fiber"],
			half=i_qie["half"],
			link=i_qie["link"],
			channel=i_qie["channel"],
		))
	return qies

# Return the temperatures of your system:
def get_temp(ts, crate, icrate):		# It's more flexible to not have the input be a teststand object. I should make it accept both.
	commands = []
	for slot in ts.qie_slots[icrate]:
		commands.append("get HE{0}-{1}-temperature_f".format(crate, slot))
		commands.append("wait")
	raw_output = ngccm.send_commands(ts, commands)["output"]
	temp = []
	log =[]
	for i,slot in enumerate(ts.qie_slots[icrate]):
		temp.append("")
		log.append("")
		try:
			match = search("get HE{0}-{1}-temperature_f # ([\d\.]+)".format(crate, slot), raw_output)
			#print match.group(0)
			#print match.group(1)
			temp[i] = float(match.group(1))
		except Exception as ex:
			#		print raw_output
			log[i] += 'Trying to find the temperature of Crate {0} with "{1}" resulted in: {2}\n'.format(crate, commands[i], ex)
			match = search("\n(.*ERROR!!.*)\n", raw_output)
		if match:
			log[i] += 'The data string was "{0}".'.format(match.group(0).strip())

	return {
		"temp":	temp,
		"log":	log,
		}

def get_temps(ts=False):		# It's more flexible to not have the input be a teststand object. I should make it accept both.
	output = {}
	
	if ts:
		for crate, slots in ts.fe.iteritems():
			output[crate] = []
			for slot in slots:
				cmds = [
					"get HE{0}-{1}-bkp_temp_f".format(crate, slot),		# The temperature sensor on the QIE card, near the bottom, labeled "U40".
				]
				output[crate] += ngccm.send_commands_parsed(ts, cmds)["output"]
		return output
	else:
		return output

# Functions for the whole system (BE and FE):
def get_ts_status(ts):		# This function does basic initializations and checks. If all the "status" bits for each component are 1, then things are good.
	status = {}
	log = ""
	print ">> Checking the MCHs ..."
	status["mch"] = mch.get_status(ts)
	print ">> Checking the AMC13s ..."
	status["amc13"] = amc13.get_status(ts=ts)
	print ">> Checking the GLIBs ..."
	status["glib"] = glib.get_status(ts)
	print ">> Checking the uHTRs ..."
	status["uhtr"] = uhtr.get_status(ts)
	print ">> Checking the backplanes ..."
	status["bkp"] = ngccm.get_status_bkp(ts)
	print ">> Checking the ngCCMs ..."
	status["ngccm"] = ngccm.get_status(ts)
	print ">> Checking the QIE cards ..."
	status["qie"] = qie.get_status(ts)
	st = []
	for component in ["amc13", "glib", "mch", "uhtr", "bkp", "ngccm", "qie"]:
#		print component
		st_temp = 1
		for s in status[component]["status"]:
			if s != 1:
				st_temp = 0
		st.append(st_temp)
	return {
		"status": st,
		"info": status,
		"log": log,
	}

def parse_ts_configuration(f="teststands.txt"):		# This function is used to parse the "teststands.txt" configuration file. It is run by the "teststand" class; usually you want to use that instead of running this yourself.
	# WHEN YOU EDIT THIS SCRIPT, MAKE SURE TO UPDATE install.py!
	variables = ["name", "fe_crates", "ngccm_port", "uhtr_ip_base", "uhtr_slots", "uhtr_settings", "glib_slot", "mch_ip", "amc13_ips", "qie_slots", "control_hub", "qie_cards_per_slot", "qies_per_card"]
	teststand_info = {}
	raw = ""
	if ("/" in f):
		raw = open("{0}".format(f)).read()
	else:
		raw = open("configuration/{0}".format(f)).read()
	teststands_raw = split("\n\s*%%", raw)
	for teststand_raw in teststands_raw:
		lines = teststand_raw.strip().split("\n")
		ts_name = ""
		for variable in variables:
			for line in lines:
				if line:		# Skip empty lines. This isn't really necessary.
					if search("^\s*{0}".format(variable), line):		# Consider lines beginning with the variable name.
						if (variable == "name"):
							ts_name = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name] = {}
						elif (variable == "fe_crates"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = [int(i) for i in value.split(",")]
						elif (variable == "ngccm_port"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = int(value)
						elif (variable == "uhtr_ip_base"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = value.strip()
						elif (variable == "uhtr_slots"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = sorted([int(i) for i in value.split(",")])
						elif (variable == "uhtr_settings"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = [i for i in value.split(",")]
						elif (variable == "glib_slot"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = int(value)
						elif (variable == "mch_ip"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = value.strip()
						elif (variable == "amc13_ips"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = [i.strip() for i in value.split(",")]
						elif (variable == "qie_cards_per_slot"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = int(value.strip())
						elif (variable == "qies_per_card"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = int(value.strip())
						elif (variable == "qie_slots"):
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
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
							value = search("{0}\s*=\s*([^#]+)".format(variable), line).group(1).strip()
							teststand_info[ts_name][variable] = value.strip()
	return teststand_info

def set_mode(ts, crate, slot, n):		# 0: normal mode, 1: link test mode A (test mode string), 2: link test mode B (IGLOO register)
	s = 0
	if n == 0:
		cmds = [
			"put HF{0}-{1}-iTop_LinkTestMode 0x0".format(crate, slot, n),
			"put HF{0}-{1}-iBot_LinkTestMode 0x0".format(crate, slot, n),
			"get HF{0}-{1}-iTop_LinkTestMode".format(crate, slot, n),
			"get HF{0}-{1}-iBot_LinkTestMode".format(crate, slot, n),
		]
		output = ngccm.send_commands_parsed(ts, cmds)["output"]
#		print output
		if "ERROR" not in output[0]["result"] and "ERROR" not in output[1]["result"]:
			s = 1
	elif n == 1:
		cmds = [
			"put HF{0}-{1}-iTop_LinkTestMode 0x1".format(crate, slot, n),
			"put HF{0}-{1}-iBot_LinkTestMode 0x1".format(crate, slot, n),
			"get HF{0}-{1}-iTop_LinkTestMode".format(crate, slot, n),
			"get HF{0}-{1}-iBot_LinkTestMode".format(crate, slot, n),
		]
		output = ngccm.send_commands_parsed(ts, cmds)["output"]
		if "ERROR" not in output[0]["result"] and "ERROR" not in output[1]["result"]:
			s = 1
	elif n == 2:
		cmds = [
			"put HF{0}-{1}-iTop_LinkTestMode 0x7".format(crate, slot, n),
			"put HF{0}-{1}-iBot_LinkTestMode 0x7".format(crate, slot, n),
			"get HF{0}-{1}-iTop_LinkTestMode".format(crate, slot, n),
			"get HF{0}-{1}-iBot_LinkTestMode".format(crate, slot, n),
		]
		output = ngccm.send_commands_parsed(ts, cmds)["output"]
#		print output
		if "ERROR" not in output[0]["result"] and "ERROR" not in output[1]["result"]:
			s = 1
	return s

def set_mode_all(ts=False, n=0):		# 0: normal mode, 1: link test mode A (test mode string), 2: link test mode B (IGLOO register)
	s = 1
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			s_temp = set_mode(ts, crate, slot, n)
			if s_temp != 1:
				s = 0
	return s
# /FUNCTIONS

# This is what gets exectuted when hcal_teststand.py is executed (not imported).
if __name__ == "__main__":
	print "Hang on."
	print 'What you just ran is "hcal_teststand.py". This is a module, not a script. See the documentation (readme.md) for more information.'
