# This module contains functions for talking to the QIE card.

from re import search
from subprocess import Popen, PIPE
import ngccm
from time import time, sleep
from numpy import mean, std
import uhtr

# CLASSES:
class qie:
	# Construction:
	def __init__(self, ts=None, unique_id="", crate=-1, slot=-1, n=-1, uhtr_slot=-1, fiber=-1, half=-1, link=-1, channel=-1):
		if not ts:
			ts = None
		self.ts = ts
		self.id = unique_id
		self.crate = crate
		self.slot = slot
		self.n = n
		self.uhtr_slot = uhtr_slot
		self.fiber = fiber
		self.half = half
		self.link = link
		self.channel = channel
	
	# String behavior
	def __str__(self):
		if self.ts:
			return "<qie.qie object: {0}, {1}>".format(self.id, self.n)
		else:
			return "<empty qie.qie object>"
	
	# Methods:
	def get_data(self, method=0):		# Method 0 is for uHTR SPY. Nothing else is implemented, yet.
		if method == 0:
			return uhtr.get_data_parsed_new(self.ts, self.uhtr_slot, 300, self.link)[channel]
		else:
			print "ERROR (qie object {0}): Could not get data because method value {1} wasn't recognized.".format(self.id, method)
			return False
	# /Methods

class datum:
	# Construction:
	def __init__(self, adc=-1, cid=-1, tdc_le=-1, tdc_te=-1, raw="", bx=-1):
		self.adc = adc
		self.cid = cid
		self.tdc_le = tdc_le
		self.tdc_te = tdc_te
		self.raw = raw
		self.bx = bx
	
	# String behavior
	def __str__(self):
		if self.adc != -1:
			return "<qie.datum object>"
		else:
			return "<empty qie.datum object>"
	
	# Methods:
	# /Methods

class status:
	# Construction:
	def __init__(self, ts=None, status=[], crate=-1, slot=-1, fw_top=[], fw_bot="", fw_b=[]):
		if not ts:
			ts = None
		self.ts = ts
		if not status:
			status = []
		self.status = status
		self.crate = crate
		self.slot = slot
		if not fw_top:
			fw_top = []
		self.fw_top = fw_top
		if not fw_bot:
			fw_bot = []
		self.fw_bot = fw_bot
		if not fw_b:
			fw_b = []
		self.fw_b = fw_b
	
	# String behavior
	def __str__(self):
		if self.ts:
			return "<qie.status object: {0}>".format(self.status)
		else:
			return "<empty qie.status object>"
	
	# Methods:
	def update(self):
		self.good = (False, True)[bool(self.status) and len(self.status) == sum(self.status)]
	
	def Print(self, verbose=True):
		if verbose:
			print "[{0}] QIE card in crate {1}, slot {2} status: {3} <- {4}".format(("!!", "OK")[self.good], self.crate, self.slot, ("BAD", "GOOD")[self.good], self.status)
			if self.good:
				print "\tFW IGLOO2 top: {0}".format(self.fw_top)
				print "\tFW IGLOO2 bottom: {0}".format(self.fw_bot)
				print "\tFW bridge: {0}".format(self.fw_b)
		else:
			print "[{0}] QIE card in crate {1}, slot {2} status: {3}".format(("!!", "OK")[self.good], self.crate, self.slot, ("BAD", "GOOD")[self.good])
	
	def log(self):
		output = "%% QIE {0}, {1}\n".format(self.crate, self.slot)
		output += "{0}\n".format(int(self.good))
		output += "{0}\n".format(self.status)
		output += "{0}\n".format(self.fw_top)
		output += "{0}\n".format(self.fw_bot)
		output += "{0}\n".format(self.fw_b)
		return output.strip()
	# /Methods
# /CLASSES

# FUNCTIONS:
# Functions to fetch component information:
def get_bridge_info(ts, crate, slot, qie_card):		# Returns a dictionary of information about the Bridge FPGA, such as the FW versions.
	data = [
		["version_fw_major", 'get HE{0}-{1}-{2}-B_FIRMVERSION_MAJOR'.format(crate, slot, qie_card), 0],
		["version_fw_minor", 'get HE{0}-{1}-{2}-B_FIRMVERSION_MINOR'.format(crate, slot, qie_card), 0],
		["version_fw_svn", 'get HE{0}-{1}-{2}-B_FIRMVERSION_SVN'.format(crate, slot, qie_card), 0],
	]
	log = ""
	parsed_output = ngccm.send_commands_parsed(ts, [info[1] for info in data])["output"]
#	print parsed_output
	for info in data:
		result = parsed_output[data.index(info)]["result"]
		cmd = parsed_output[data.index(info)]["cmd"]
		if "ERROR" not in result:
			info[2] = int(result, 16)
		else:
			log += '>> ERROR: Failed to find the result of "{0}". The data string follows:\n{1}'.format(cmd, result)
	version_fw = "{0:02d}.{1:02d}.{2:04d}".format(data[0][2], data[1][2], data[2][2])
	return {
		"slot":	slot,
		"card": qie_card,
		"version_fw_major":	data[0][2],
		"version_fw_minor":	data[1][2],
		"version_fw_svn":	data[2][2],
		"version_fw":	        version_fw,
		"log":			log.strip(),
	}

def get_igloo_info(ts, crate, slot, qie_card):		# Returns a dictionary of information about the IGLOO2, such as the FW versions.
	data = [
		["version_fw_major", 'get HE{0}-{1}-{2}-i_FPGA_MAJOR_VERSION'.format(crate, slot, qie_card), 0],
		["version_fw_minor", 'get HE{0}-{1}-{2}-i_FPGA_MINOR_VERSION'.format(crate, slot, qie_card), 0],
	]
	log = ""
	parsed_output = ngccm.send_commands_parsed(ts, [info[1] for info in data])["output"]
#	print parsed_output
	for info in data:
		result = parsed_output[data.index(info)]["result"]
		cmd = parsed_output[data.index(info)]["cmd"]
		if "ERROR" not in result:
			info[2] = int(result, 16)
		else:
			log += '>> ERROR: Failed to find the result of "{0}". The data string follows:\n{1}'.format(cmd, result)
	version_fw = "{0:02d}.{1:02d}".format(data[0][2], data[1][2])
	return {
		"slot": slot,
		"card": qie_card,
		"version_fw_major":	data[0][2],
		"version_fw_minor":	data[1][2],
		"version_fw":	version_fw,
		"log":			log.strip(),
	}

def get_info(ts, crate, slot, qie_card):
	return{
		"bridge": get_bridge_info(ts, crate, slot, qie_card),
		"igloo": get_igloo_info(ts, crate, slot, qie_card),
	}

def get_unique_id(ts, crate, slot):		# Reads the unique ID of a given crate and slot and returns it as a list.
	ngccm_output = ngccm.send_commands_parsed(ts, ["get HF{0}-{1}-UniqueID".format(crate,slot)])		# Results in something like "get HF1-1-UniqueID # '1 0x5f000000 0x9b46ce70'"
	result = ngccm_output["output"][0]["result"]
	if "ERROR" not in result: 
		return result.split()[1:3]		# Get the result of the command, and turn the result into a list (ignoring the first element).
	else:
		return []

def get_map(ts, v=False):		# Determines the QIE map of the teststand. A qie map is from QIE crate, slot, qie number to link number, IP, unique_id, etc. It's a list of dictionaries with 3tuples as the keys: (crate, slot, qie)
	# THIS IS A WORK IN PROGRESS. User get_map_slow until this is fixed.
	print ">> Getting links ..."
	links_by_slot = ts.get_links()
	qie_map = []
	
	# Make sure the teststand is set up:
	print "Disabling fixed-range mode ..."
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			set_fix_range_all(ts, crate, slot, False)
	
	# Do the mapping:
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			print ">> Mapping crate {0}, slot {1} ...".format(crate, slot)
			for i in range(2):		# Do the following step twice (for QIEs 1-12, and for 13-24).
				print ">> Doing the cycle {0} ...".format(i)
				uhtr_data = []
				set_fix_range_all(ts, crate, slot, False)
				for qie in range(i*12 + 1, i*12 + 13):
					if (v): print "{0} -> {1}".format(qie, int((qie - i*12 - 1)/4) + 1)
					set_fix_range(ts, crate, slot, qie, True, int((qie - i*12 - 1)/4) + 1)
				files_histo = {}
				for uhtr_slot in links_by_slot.keys():
					files_histo[uhtr_slot] = uhtr.get_histo(ts=ts, uhtr_slot=uhtr_slot, sepCapID=0)
					uhtr_data_temp = uhtr.read_histo(files_histo[uhtr_slot])
					temp = {}
					for datum in uhtr_data_temp:
						temp = datum
						temp["uhtr_slot"] = uhtr_slot
						uhtr_data.append(temp)
				
				groups = [[] for j in range(4)]
				for r in range(1, 4):
					for datum in uhtr_data:
						if datum["mean"] > r*64 - 10 and datum["mean"] < r*64 + 10:
#							print datum["mean"]
							groups[r].append(datum)
				
				for r in range(4):
					if len(groups[r]) == 4:
						if len([j["link"] for j in groups[r]]) == 1 and len([j["uhtr_link"] for j in groups[r]]) == 1:
							i_link = groups[r][0]["link"]
							uhtr_slot = groups[r][0]["uhtr_slot"]
						else:
							print "ERROR (qie.get_map): Something is strange about how things are organized ..."
							print groups[r]
					else:
						print "ERROR (qie.get_map): The following group doesn't contain four QIEs"
						print groups[r]
	
	# Make sure the teststand is set up:
	print "Disabling fixed-range mode ..."
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			set_fix_range_all(ts, crate, slot, False)
	
	return qie_map

def get_map_slow(ts):		# Determines the QIE map of the teststand. A qie map is from QIE crate, slot, qie number to link number, IP, unique_id, etc. It's a list of dictionaries with 3tuples as the keys: (crate, slot, qie)
	print ">> Getting links ..."
	links_by_ip = ts.get_links()
#	print links_by_ip
	qie_map = []
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			set_fix_range_all(ts, crate, slot, False)
			for qie in range(1, 25):
				print ">> Finding crate {0}, slot {1}, QIE {2} ...".format(crate, slot, qie)
				set_fix_range(ts, crate, slot, qie, True, 2)
				channel_save = []
				link_save = []
				for ip, links in links_by_ip.iteritems():
					for link in [l for l in links if l.on]:
						data = link.get_data()
#						print data
						if data:
							for channel in range(4):
								adc_avg = mean([i_bx[channel] for i_bx in data["adc"]])
								print adc_avg
								if adc_avg == 128:
									channel_save.append(channel)
									link_save.append(link)
				if len(channel_save) == 1 and len(link_save):
					channel = channel_save[0]
					link = link_save[0]
					qie_map.append({
						"crate": crate,
						"slot": slot,
						"qie": qie,
						"id": link.qie_unique_id,
						"link": link.n,
						"channel": channel,
						"half": link.qie_half,
						"fiber": link.qie_fiber,
						"uhtr_slot": link.slot,
					})
				else:
					if len(channel_save) > 1:
						print "ERROR: Mapping is weird."
					qie_map.append({
						"crate": crate,
						"slot": slot,
						"qie": qie,
						"id": [link.qie_unique_id for link in link_save],
						"link": [link.n for link in link_save],
						"channel": channel_save,
						"half": [link.qie_half for link in link_save],
						"fiber": [link.qie_fiber for link in link_save],
						"uhtr_slot": [link.slot for link in link_save],
					})
				set_fix_range(ts, crate, slot, qie, False)
	return qie_map
# /

# Functions to set up components:
def set_unique_id(ts, crate, slot):		# Saves the unique ID of a crate slot to the associated QIE card to IGLOO registers.
	unique_id = get_unique_id(ts, crate, slot)
	if unique_id:
		ngccm_output = ngccm.send_commands(ts, [
			"put HF{0}-{1}-iTop_UniqueID {2} {3}".format(crate, slot, unique_id[0], unique_id[1]),
			"put HF{0}-{1}-iBot_UniqueID {2} {3}".format(crate, slot, unique_id[0], unique_id[1])
		])
		return 1
	else:
		return 0

def set_unique_id_all(ts):		# Repeats the "set_unique_id" function from above for all slots in the teststand.
	is_set = []
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			is_set.append(set_unique_id(ts, crate, slot))		# Set the QIE card's unique ID into the correct IGLOO registers.
	if len(set(is_set)) == 1:
		return list(set(is_set))[0]
	else:
		return 0
# /

# Functions to "status" components, including calculating clocks:
def get_status(ts=None, crate=-1, slot=-1):		# Perform basic checks of the QIE cards:
	log =""
	s = status(ts=ts, crate=crate, slot=slot)
	
#	f_orbit = get_frequency_orbit(ts)
	if ts:
		# Check Bridge FPGA and IGLOO2 version are accessible:
		qie_info = get_info(ts, crate, slot)
		
		## Top:
		s.fw_top = [
			qie_info["igloo"]["version_fw_major_top"],
			qie_info["igloo"]["version_fw_minor_top"],
		]
		if (s.fw_top[0] != 0):
			s.status.append(1)
		else:
			s.status.append(0)
		
		## Bottom:
		s.fw_bot = [
			qie_info["igloo"]["version_fw_major_bot"],
			qie_info["igloo"]["version_fw_minor_bot"],
		]
		if (s.fw_bot[0] != 0):
			s.status.append(1)
		else:
			s.status.append(0)
		
		## Bridge:
		qie_info = get_info(ts, crate, slot)
		s.fw_b = [
			qie_info["bridge"]["version_fw_major"],
			qie_info["bridge"]["version_fw_minor"],
			qie_info["bridge"]["version_fw_svn"]
		]
		if (s.fw_b[0] != 0):
			s.status.append(1)
		else:
			s.status.append(0)
		
		
#		# Check QIE resets in the BRIDGE (1) and the IGLOO2s (2):
#		orbit_temp = []
#		f_orbit_bridge = f_orbit["bridge"][i_qie]
#		f_orbit_igloo = f_orbit["igloo"][i_qie]
#		## (1) Check the BRIDGE:
#		if (f_orbit_bridge["f"] < 13000 and f_orbit_bridge["f"] > 10000 and f_orbit_bridge["f_e"] < 500):
#			status["status"].append(1)
#		else:
#			status["status"].append(0)
#		orbit_temp.append([f_orbit_bridge["f"], f_orbit_bridge["f_e"]])
#		## (2) Check the IGLOO2s:
#		for i in range(2):
#			if (f_orbit_igloo["f"][i] < 13000 and f_orbit_igloo["f"][i] > 10000 and f_orbit_igloo["f_e"][i] < 600):
#				status["status"].append(1)
#			else:
#				status["status"].append(0)
#			orbit_temp.append([f_orbit_igloo["f"][i], f_orbit_igloo["f_e"][i]])
#		status["orbit"].append(orbit_temp)
		s.update()
	return s

def get_status_all(ts=None):
	log = ""
	ss = []
	
	if ts:
		for crate, slots in ts.fe.iteritems():
			for slot in slots:
				ss.append(get_status(ts=ts, crate=crate, slot=slot))
	return ss

def read_counter_qie_bridge(ts, crate, slot):
	log = ""
	count = -1
	cmd = "get HF{0}-{1}-B_RESQIECOUNTER".format(crate, slot)
	output = ngccm.send_commands_parsed(ts, cmd)["output"]
	try:
		count = int(output[0]["result"], 16)
	except Exception as ex:
		log += output[0]["cmd"] + " -> " + output[0]["result"] + "\n"
	return {
		"count": count,
		"log": log,
	}
def read_counter_qie_igloo(ts, crate, slot):
	log = ""
	counts = [-1, -1]
	times = [-1, -1]
	cmds = [
		"get HF{0}-{1}-iTop_RST_QIE_count".format(crate, slot),
		"get HF{0}-{1}-iBot_RST_QIE_count".format(crate, slot),
	]
	result = ngccm.send_commands_parsed(ts, cmds)
	output = result["output"]
	for i in range(2):
		try:
			counts[i] = int(output[i]["result"], 16)
			times[i] = output[i]["times"][0]
		except Exception as ex:
			log += output[i][0] + " -> " + output[i][1] + "\n" + ex + "\n"
	return {
		"counts": counts,
		"times": times,
		"log": log,
	}

def get_frequency_orbit(ts):
	data = {
		"bridge": [],
		"igloo": [],
		"log": "",
	}
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			for fpga in data.keys():
				if fpga == "bridge":
					c = []
					t = []
					for i in range(6):
						result = read_counter_qie_bridge(ts, crate, slot)
						data["log"] += result["log"]
						c.append(result["count"])
						t.append(time())
#						sleep(0.01)
					f = []
					for i in range(len(c)-1):
						f.append((c[i+1]-c[i])/(t[i+1]-t[i]))
					data[fpga].append({
						"f_list":	f,
						"f":	mean(f),
						"f_e":	std(f)/(len(f)**0.5),
					})
				elif fpga == "igloo":
					c = []
					t = []
					for i in range(6):
						result = read_counter_qie_igloo(ts, crate, slot)
						data["log"] += result["log"]
						c.append(result["counts"])
						t.append([result["times"][0], result["times"][1]])
#						sleep(0.01)
					f = []
					for j in range(2):
						f_temp = []
						for i in range(len(c)-1):
							f_temp.append((c[i+1][j]-c[i][j])/(t[i+1][j]-t[i][j]))
						f.append(f_temp)
					data[fpga].append({
						"f_list":	f,
						"f":	[mean(f[0]), mean(f[1])],
						"f_e":	[std(f[0])/(len(f[0])**0.5), std(f[1])/(len(f[1])**0.5)],
					})
	return data
# /

# Functions to set QIE registers:
## Pedestals:
def set_ped(ts, crate, slot, i, n):		# Set the pedestal of QIE i to DAC value n.
	assert isinstance(n, int)
	if abs(n) > 31:
		print n
		print ">> ERROR: You must enter a decimal integer between -31 and 31. The pedestals have not been changed."
	else:
		if n <= 0:
			n = abs(n)
		else:
			n = n + 32
		n_str = "{0:#04x}".format(n)		# The "#" prints the "0x". The number of digits to pad with 0s must include these "0x", hence "4" instead of "2".
		commands = ["put HF{0}-{1}-QIE{2}_PedestalDAC {3}".format(crate, slot, i, n_str)]
		raw_output = ngccm.send_commands_fast(ts, commands)["output"]
		# Maybe I should include something here to make sure the command didn't return an error? Return 1 if not...

def set_ped_all(ts, crate, slot, n):		# n is the decimal representation of the pedestal register.
	# This function is faster than running "set_ped" 24 times.
	assert isinstance(n, int)
#	for i in range(1, 25):
#		set_ped(ts, crate, slot, i, n)
	if abs(n) > 31:
		print ">> ERROR: You must enter a decimal integer between -31 and 31. The pedestals have not been changed."
	else:
		if n <= 0:
			n = abs(n)
		else:
			n = n + 32
		n_str = "{0:#04x}".format(n)		# The "#" prints the "0x". The number of digits to pad with 0s must include these "0x", hence "4" instead of "2".
		commands = ["put HF{0}-{1}-QIE{2}_PedestalDAC {3}".format(crate, slot, i, n_str) for i in range(1, 25)]
#		print commands
		raw_output = ngccm.send_commands_fast(ts, commands)["output"]
#		print raw_output
		# I should include something here to make sure the command didn't return an error? Return 1 if not...
## /

## Fixed Range Mode:
def set_fix_range(ts, crate, slot, qie, enable=False, rangeSet=0):		# Turn fixed range mode on or off for a given QIE.
	assert isinstance(rangeSet, int)
	if rangeSet < 0 or rangeSet > 3 : 
		print ">> ERROR: the range you select with \"RangeSet\" must be an element of {0, 1, 2, 3}."
	else:
		if enable:
			commands = [
				"put HF{0}-{1}-QIE{2}_FixRange 1".format(crate, slot, qie),
				"put HF{0}-{1}-QIE{2}_RangeSet {3}".format(crate, slot, qie, rangeSet)
			]
		else :
			commands = ["put HF{0}-{1}-QIE{2}_FixRange 0".format(crate, slot, qie)]
		
		raw_output = ngccm.send_commands_fast(ts, commands)["output"]
#		raw_output = ngccm.send_commands_parsed(ts, commands)["output"]
		return raw_output

def set_fix_range_all(ts, crate, slot, enable=False, rangeSet=0):		# Turn fixed range mode on or off for all QIEs on a given board.
	assert isinstance(rangeSet, int)
	if rangeSet < 0 or rangeSet > 3: 
		print ">> ERROR: the range you select with \"RangeSet\" must be an element of {0, 1, 2, 3}."
	else:
		commands = []
		if enable:
			for i_qie in range(1, 25):
				commands.append("put HF{0}-{1}-QIE{2}_FixRange 1".format(crate, slot, i_qie))
				commands.append("put HF{0}-{1}-QIE{2}_RangeSet {3}".format(crate, slot, i_qie, rangeSet))
		else:
			for i_qie in range(1, 25):
				commands.append("put HF{0}-{1}-QIE{2}_FixRange 0".format(crate, slot, i_qie))
				commands.append("put HF{0}-{1}-QIE{2}_RangeSet 0".format(crate, slot, i_qie))
		
		# This should work, but I've had trouble with these "mass settings" before:
#		if enable:
#			commands.append("put HF{0}-{1}-QIE[1-24]_FixRange 24*1".format(crate, slot))
#			commands.append("put HF{0}-{1}-QIE[1-24]_RangeSet 24*{2}".format(crate, slot, rangeSet))
#		else:
#			commands.append("put HF{0}-{1}-QIE[1-24]_FixRange 24*0".format(crate, slot))
#			commands.append("put HF{0}-{1}-QIE[1-24]_RangeSet 24*0".format(crate, slot))		# Not necessary, but I think it's probably good form.
		raw_output = ngccm.send_commands_fast(ts, commands)["output"]
#		raw_output = ngccm.send_commands_parsed(ts, commands)["output"]
		return raw_output
## /

## Cal Mode:
def set_cal_mode(ts, crate, slot, qie, enable=False):
	value = 1 if enable else 0
	commands = ["put HF{0}-{1}-QIE{2}_CalMode {3}".format(crate, slot, qie, value)]
	raw_output = ngccm.send_commands_fast(ts, commands)["output"]
#	raw_output = ngccm.send_commands_parsed(ts, commands)["output"]
	return raw_output

def set_cal_mode_all(ts, crate, slot, enable=False):
	commands = []
	value = 1 if enable else 0
	for qie in range(1, 25):
		commands.append("put HF{0}-{1}-QIE{2}_CalMode {3}".format(crate, slot, qie, value))
	raw_output = ngccm.send_commands_fast(ts, commands)["output"]
#	raw_output = ngccm.send_commands_parsed(ts, commands)["output"]
	return raw_output
## /

## QIE clock phase:
def set_clk_phase(ts, crate, slot, qie, phase=0):
	return ngccm.send_commands_parsed(ts, "put HF{0}-{1}-Qie{2}_ck_ph {3}".format(crate, slot, qie, phase))

def set_clk_phase_all(ts, crate, slot, phase=0):
	cmds = ["put HF{0}-{1}-Qie{2}_ck_ph {3}".format(crate, slot, qie, phase) for qie in range(1, 25)]
	return ngccm.send_commands_parsed(ts, cmds)
## /
# /

# Functions dealing with QIE chip behavior:
def make_adc_to_q_conversion():		# This function generates a list of charge values (in fC) indexed by ADC bin number.
	srs = [		# Subrange information
		range(0, 16),
		range(16, 36),
		range(36, 57),
		range(57, 64)
	]
	overlap = 3		# The number of bins that overlap at range transitions.
	s_init = 3.1		# All other ideal sensitivities can be calculated from this using s = s_init * (8**r) * (2**sr).
	s = 0
	s_sr_min = 0
#	p = -16
	p = 0
	q_sum = p
	q = []
	for r in range(4):
		for sr in range(4):
			for m in srs[sr]:
				s_prev = s
				s = s_init * (8**r) * (2**sr)		# Calculate the appropriate sensitivity.
				q_sum += s_prev/2 + s/2
				if sr == 0 and m == 0 and r > 0:
					q_sum -= s*overlap
				q.append(q_sum)
	return q
# /
# /FUNCTIONS


if __name__ == "__main__":
	print "Hang on."
	print 'What you just ran is "qie.py". This is a module, not a script. See the documentation ("readme.md") for more information.'
